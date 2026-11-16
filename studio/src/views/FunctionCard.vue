<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from "vue";
import * as echarts from "echarts";
import "echarts-gl";
import { sweep, sweep2d } from "../api";
import { SCAN_KEYS, FUNC_MAP } from "../functionLibrary";
import { fmt } from "../format";

const props = defineProps({ card: Object, params: Object });
const emit = defineEmits(["remove"]);

const el = ref(null);
let chart = null;
let ro = null;

const MODES = [
  { k: "line", label: "线", title: "折线", dim: 2 },
  { k: "scatter", label: "点", title: "散点", dim: 2 },
  { k: "bar", label: "柱", title: "柱状", dim: 2 },
  { k: "heatmap", label: "热", title: "热力", dim: 3 },
  { k: "contour", label: "等", title: "等高线", dim: 3 },
  { k: "surface", label: "3D", title: "3D 曲面", dim: 3 },
];

const fn = () => FUNC_MAP[props.card.fn] || { name: props.card.fn, unit: "" };
const is3d = () => MODES.find((m) => m.k === props.card.mode)?.dim === 3;

function scanRange(key) {
  const s = SCAN_KEYS.find((x) => x.k === key);
  if (!s) return [0, 1];
  const [a, b] = s.span(props.params);
  return [+a.toFixed(4), +b.toFixed(4)];
}

function baseOpt(title) {
  return {
    backgroundColor: "transparent",
    animationDuration: 200,
    title: title ? {
      text: title, left: 6, top: 2,
      textStyle: { color: "#334155", fontSize: 11, fontWeight: 500 },
    } : undefined,
    tooltip: {
      backgroundColor: "#ffffff", borderColor: "#dbe2ec", borderWidth: 1,
      padding: [6, 10], textStyle: { color: "#0f172a", fontSize: 11 },
      extraCssText: "box-shadow:0 4px 14px rgba(15,23,42,.10);border-radius:7px;",
    },
  };
}

const ax = {
  axisLine: { lineStyle: { color: "#cbd5e1" } },
  axisTick: { lineStyle: { color: "#cbd5e1" }, length: 3 },
  axisLabel: { color: "#64748b", fontSize: 9.5 },
  splitLine: { lineStyle: { color: "#eef2f8" } },
  nameTextStyle: { color: "#475569", fontSize: 10 },
};

async function render() {
  if (!chart) return;
  const f = fn();
  const yUnit = f.unit ? ` (${f.unit})` : "";
  const xs = SCAN_KEYS.find((x) => x.k === props.card.x);
  const ys = SCAN_KEYS.find((x) => x.k === props.card.y);

  try {
    if (!is3d()) {
      const [a, b] = scanRange(props.card.x);
      const res = await sweep({
        params: { ...props.params }, key: props.card.x,
        from: a, to: b, steps: 48, out_key: props.card.fn,
      });
      chart.setOption({
        ...baseOpt(null),
        grid: { left: 52, right: 14, top: 14, bottom: 34 },
        xAxis: {
          type: "value", name: xs?.label || props.card.x,
          nameLocation: "middle", nameGap: 24, ...ax,
        },
        yAxis: { type: "value", scale: true, name: f.name + yUnit,
                 nameLocation: "middle", nameGap: 40, ...ax },
        series: [{
          type: props.card.mode === "scatter" ? "scatter"
              : props.card.mode === "bar" ? "bar" : "line",
          data: res.xs.map((x, i) => [x, res.ys[i]]),
          smooth: props.card.mode === "line",
          showSymbol: false,
          symbolSize: 5,
          lineStyle: { width: 1.8, color: "#2563eb" },
          itemStyle: { color: "#2563eb" },
          areaStyle: props.card.mode === "line" ? {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "rgba(37,99,235,.16)" },
              { offset: 1, color: "rgba(37,99,235,.01)" },
            ]),
          } : undefined,
          barMaxWidth: 14,
        }],
      }, true);
    } else {
      const [ax0, ax1] = scanRange(props.card.x);
      const [ay0, ay1] = scanRange(props.card.y);
      const res = await sweep2d({
        params: { ...props.params },
        key_x: props.card.x, from_x: ax0, to_x: ax1,
        key_y: props.card.y, from_y: ay0, to_y: ay1,
        steps: 24, out_key: props.card.fn,
      });
      if (props.card.mode === "surface") {
        const data = [];
        let lo = Infinity, hi = -Infinity;
        res.z.forEach((row, j) => row.forEach((v, i) => {
          data.push([res.x[i], res.y[j], +v.toFixed(2)]);
          if (v < lo) lo = v;
          if (v > hi) hi = v;
        }));
        chart.setOption({
          ...baseOpt(null),
          visualMap: {
            show: false, min: lo, max: hi,
            inRange: { color: ["#dbeafe", "#93c5fd", "#34d399", "#fbbf24", "#ef4444"] },
          },
          xAxis3D: { type: "value", name: xs?.label || "", ...ax },
          yAxis3D: { type: "value", name: ys?.label || "", ...ax },
          zAxis3D: { type: "value", name: f.name, ...ax },
          grid3D: {
            boxWidth: 80, boxDepth: 80, boxHeight: 55,
            viewControl: { projection: "perspective", distance: 180, alpha: 24, beta: 35 },
            light: { main: { intensity: 1.1, shadow: false }, ambient: { intensity: 0.7 } },
            axisLine: { lineStyle: { color: "#cbd5e1" } },
            splitLine: { lineStyle: { color: "#eef2f8" } },
          },
          series: [{
            type: "surface", data, shading: "lambert",
            wireframe: { show: false },
            itemStyle: { opacity: 0.96 },
          }],
        }, true);
      } else {
        const data = [], xsCat = res.x.map((v) => +v.toFixed(3)), ysCat = res.y.map((v) => +v.toFixed(3));
        let lo = Infinity, hi = -Infinity;
        res.z.forEach((row, j) => row.forEach((v, i) => {
          data.push([i, j, +v.toFixed(2)]);
          if (v < lo) lo = v;
          if (v > hi) hi = v;
        }));
        const common = {
          ...baseOpt(null),
          grid: { left: 54, right: 46, top: 14, bottom: 34 },
          xAxis: { type: "category", data: xsCat, name: xs?.label || "", nameLocation: "middle", nameGap: 24, ...ax },
          yAxis: { type: "category", data: ysCat, name: ys?.label || "", nameLocation: "middle", nameGap: 42, ...ax },
          visualMap: {
            show: true, min: lo, max: hi, calculable: false,
            orient: "vertical", right: 2, top: "middle",
            itemWidth: 8, itemHeight: 70,
            textStyle: { color: "#64748b", fontSize: 8.5 },
            inRange: { color: ["#dbeafe", "#93c5fd", "#34d399", "#fbbf24", "#ef4444"] },
          },
        };
        if (props.card.mode === "heatmap") {
          chart.setOption({
            ...common,
            series: [{ type: "heatmap", data, progressive: 1200 }],
          }, true);
        } else {
          const cd = [];
          res.z.forEach((row, j) => row.forEach((v, i) => cd.push([xsCat[i], ysCat[j], v])));
          chart.setOption({
            ...common,
            xAxis: { type: "value", name: xs?.label || "", nameLocation: "middle", nameGap: 24, ...ax },
            yAxis: { type: "value", name: ys?.label || "", nameLocation: "middle", nameGap: 42, ...ax },
            series: [{
              type: "contour", data: cd, smooth: true,
              lineStyle: { width: 1, color: "rgba(71,85,105,.5)" },
              label: { show: false },
            }],
          }, true);
        }
      }
    }
  } catch (e) {
    console.error("chart error", e);
  }
}

onMounted(async () => {
  await nextTick();
  chart = echarts.init(el.value, null, { renderer: "canvas" });
  ro = new ResizeObserver(() => chart?.resize());
  ro.observe(el.value);
  render();
});

onBeforeUnmount(() => {
  ro?.disconnect();
  chart?.dispose();
});

watch(() => [props.card.fn, props.card.x, props.card.y, props.card.mode], render);
watch(() => props.params, render, { deep: true });
</script>

<template>
  <div class="card">
    <div class="chead">
      <div class="cinfo">
        <span class="cname">{{ fn().name }}</span>
        <span class="cunit" v-if="fn().unit">{{ fn().unit }}</span>
        <span class="ccore" v-if="fn().core">核心</span>
      </div>
      <button class="cclose" @click="$emit('remove', card.id)" title="移除">×</button>
    </div>

    <div class="ctools">
      <select v-model="card.x" class="mini">
        <option v-for="s in SCAN_KEYS" :key="s.k" :value="s.k">{{ s.label }}</option>
      </select>
      <select v-model="card.y" class="mini" v-if="is3d()">
        <option v-for="s in SCAN_KEYS" :key="s.k" :value="s.k">{{ s.label }}</option>
      </select>
      <div class="modes">
        <button v-for="m in MODES" :key="m.k" class="mbtn"
                :class="{ on: card.mode === m.k }" :title="m.title"
                @click="card.mode = m.k">{{ m.label }}</button>
      </div>
    </div>

    <div class="cbody" ref="el"></div>
    <div class="cdesc" v-if="fn().desc">{{ fn().desc }}</div>
  </div>
</template>

<style scoped>
.card {
  display: flex; flex-direction: column; min-height: 0;
  background: var(--panel); border: 1px solid var(--line);
  border-radius: 9px; overflow: hidden;
  box-shadow: var(--shadow-sm);
}
.chead {
  flex-shrink: 0; display: flex; align-items: center; gap: 7px;
  padding: 6px 10px 4px;
}
.cinfo { display: flex; align-items: baseline; gap: 6px; min-width: 0; }
.cname {
  font-size: 11.5px; font-weight: 600; color: var(--ink);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.cunit { font-size: 9.5px; color: var(--dim2); font-family: Consolas, monospace; }
.ccore {
  font-size: 9px; font-weight: 600; color: var(--brand2);
  background: var(--brand-soft); border: 1px solid #c7d9ff;
  padding: 0 5px; border-radius: 4px; letter-spacing: 0.04em;
}
.cclose {
  margin-left: auto; flex-shrink: 0;
  border: none; background: transparent; color: var(--dim2);
  font-size: 15px; line-height: 1; cursor: pointer; padding: 2px 4px;
  border-radius: 4px;
}
.cclose:hover { background: var(--bad-soft); color: var(--bad); }

.ctools {
  flex-shrink: 0; display: flex; align-items: center; gap: 4px;
  padding: 0 8px 5px; flex-wrap: nowrap; overflow: hidden;
}
.mini {
  font-size: 9.5px; padding: 2px 4px; border-radius: 4px;
  max-width: 92px; min-width: 60px; border: 1px solid var(--line);
}
.modes { display: flex; margin-left: auto; border: 1px solid var(--line); border-radius: 5px; overflow: hidden; }
.mbtn {
  border: none; background: transparent; font-size: 9px;
  padding: 2.5px 4px; color: var(--dim2); cursor: pointer;
  font-family: inherit; border-right: 1px solid var(--line);
}
.mbtn:last-child { border-right: none; }
.mbtn:hover { background: var(--panel3); }
.mbtn.on { background: var(--brand-soft); color: var(--brand2); font-weight: 600; }

.cbody { flex: 1; min-height: 0; }
.cdesc {
  flex-shrink: 0; font-size: 9.5px; color: var(--dim2);
  padding: 0 10px 6px; line-height: 1.4;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
</style>
