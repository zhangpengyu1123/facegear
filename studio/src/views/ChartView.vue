<script setup>
import { ref, onMounted, onBeforeUnmount, watch, inject, nextTick } from "vue";
import * as echarts from "echarts";
import { sweep, sweep2d } from "../api";

const params = inject("params");

const chartEl = ref(null);
let chart = null;

/* ---------------- 可选项 ---------------- */
const X_KEYS = [
  { k: "m", label: "模数 m" }, { k: "z1", label: "小齿轮齿数 z₁" },
  { k: "z2", label: "面齿轮齿数 z₂" }, { k: "alpha", label: "压力角 α" },
  { k: "b", label: "齿宽 b" }, { k: "torque", label: "扭矩 T" },
  { k: "speed", label: "转速 n" }, { k: "k_hface", label: "K_Hface" },
  { k: "r_in", label: "内半径" }, { k: "life", label: "寿命" },
];
const OUT_KEYS = [
  { k: "s_h", label: "接触应力 σ_H" }, { k: "s_f", label: "弯曲应力 σ_F" },
  { k: "safety_h", label: "接触安全系数 S_H" }, { k: "safety_f", label: "弯曲安全系数 S_F" },
  { k: "eps", label: "重合度 ε_α" }, { k: "ft", label: "切向力 F_t" },
  { k: "vel", label: "节线速度 v" }, { k: "kv", label: "动载系数 K_V" },
  { k: "yf", label: "齿形系数 Y_F" }, { k: "zh", label: "节点区域系数 Z_H" },
  { k: "power", label: "功率 P" }, { k: "d1", label: "分度圆 d₁" },
];
const TYPES = [
  { k: "line", label: "折线" }, { k: "scatter", label: "散点" },
  { k: "bar", label: "柱状" }, { k: "heatmap", label: "热力" },
  { k: "contour", label: "等高线" },
];

const xKey = ref("m");
const outKey = ref("s_h");
const chartType = ref("line");
const steps = ref(60);
const busy = ref(false);

/* 扫描范围：自动跟随参数值上下浮动 */
function rangeOf(key) {
  const base = params[key];
  const span = {
    m: 4, z1: 20, z2: 100, alpha: 8, b: 60, torque: 2400,
    speed: 3000, k_hface: 0.6, r_in: 300, life: 8000,
  }[key] ?? Math.abs(base) * 0.6;
  return [Math.max(0.1, base - span * 0.5), base + span * 0.5];
}

const xRange = ref({ from: 2.35, to: 10.35 });

function syncRange() {
  const [a, b] = rangeOf(xKey.value);
  xRange.value = { from: +a.toFixed(3), to: +b.toFixed(3) };
}

/* ---------------- 绘图 ---------------- */
const axisStyle = {
  axisLine: { lineStyle: { color: "#cbd5e1" } },
  axisTick: { lineStyle: { color: "#cbd5e1" } },
  axisLabel: { color: "#64748b", fontSize: 10.5 },
  splitLine: { lineStyle: { color: "#eef2f7" } },
  nameTextStyle: { color: "#475569", fontSize: 11, fontWeight: 500 },
};

function baseOption() {
  return {
    backgroundColor: "transparent",
    grid: { left: 66, right: 30, top: 46, bottom: 54 },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#ffffff",
      borderColor: "#dbe2ec",
      borderWidth: 1,
      padding: [8, 12],
      textStyle: { color: "#0f172a", fontSize: 12 },
      extraCssText: "box-shadow:0 4px 16px rgba(15,23,42,.10);border-radius:8px;",
    },
    animationDuration: 260,
  };
}

async function render() {
  if (!chart) return;
  busy.value = true;
  try {
    if (chartType.value === "heatmap" || chartType.value === "contour") {
      const [a1, b1] = rangeOf(xKey.value);
      const yKey = outKey.value === "s_f" ? "torque" : "b";
      const [a2, b2] = yKey === "torque" ? [400, 4000] : [20, 140];
      const res = await sweep2d({
        params: { ...params },
        key_x: xKey.value, from_x: a1, to_x: b1,
        key_y: yKey, from_y: a2, to_y: b2,
        steps: Math.min(steps.value, 60),
        out_key: outKey.value,
      });
      draw2d(res, yKey);
    } else {
      const res = await sweep({
        params: { ...params },
        key: xKey.value,
        from: xRange.value.from, to: xRange.value.to,
        steps: steps.value,
        out_key: outKey.value,
      });
      draw1d(res);
    }
  } finally {
    busy.value = false;
  }
}

function draw1d(res) {
  const xs = res.xs.map((x) => +x.toFixed(4));
  const isScatter = chartType.value === "scatter";
  const isBar = chartType.value === "bar";
  const opt = {
    ...baseOption(),
    xAxis: {
      type: isBar ? "category" : "value",
      data: isBar ? xs.map((x) => x.toFixed(2)) : undefined,
      min: isBar ? undefined : xs[0],
      max: isBar ? undefined : xs[xs.length - 1],
      name: `${res.x_label}${res.x_unit ? " (" + res.x_unit + ")" : ""}`,
      nameLocation: "middle", nameGap: 28,
      ...axisStyle,
      axisLabel: { ...axisStyle.axisLabel, rotate: isBar ? 45 : 0 },
    },
    yAxis: {
      type: "value",
      scale: true,
      name: `${res.y_label}${res.y_unit ? " (" + res.y_unit + ")" : ""}`,
      nameLocation: "middle", nameGap: 46,
      ...axisStyle,
    },
    series: [{
      type: isBar ? "bar" : isScatter ? "scatter" : "line",
      data: isBar ? res.ys.map((y, i) => [xs[i], y]) : xs.map((x, i) => [x, res.ys[i]]),
      smooth: !isScatter && !isBar,
      symbolSize: isScatter ? 7 : 5,
      showSymbol: isScatter,
      lineStyle: { width: 2.2, color: "#2563eb" },
      itemStyle: { color: "#2563eb", borderColor: "#fff", borderWidth: isScatter ? 1 : 0 },
      areaStyle: (!isScatter && !isBar) ? {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: "rgba(37,99,235,.22)" },
          { offset: 1, color: "rgba(37,99,235,.01)" },
        ]),
      } : undefined,
      barWidth: isBar ? "58%" : undefined,
      barMaxWidth: 26,
    }],
  };
  chart.setOption(opt, true);
}

function draw2d(res, yKey) {
  const xs = res.x.map((v) => +v.toFixed(3));
  const ys = res.y.map((v) => +v.toFixed(3));
  const data = [];
  let lo = Infinity, hi = -Infinity;
  res.z.forEach((row, j) => row.forEach((v, i) => {
    data.push([i, j, +v.toFixed(2)]);
    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }));

  if (chartType.value === "heatmap") {
    const opt = {
      ...baseOption(),
      grid: { left: 70, right: 88, top: 44, bottom: 56 },
      tooltip: {
        ...baseOption().tooltip,
        formatter: (p) => `${res.x_label} ${xs[p.data[0]]}<br/>${res.y_label} ${ys[p.data[1]]}<br/><b>${p.data[2]} ${res.z_unit}</b>`,
      },
      xAxis: { type: "category", data: xs, name: res.x_label, nameLocation: "middle", nameGap: 28, ...axisStyle },
      yAxis: { type: "category", data: ys, name: res.y_label, nameLocation: "middle", nameGap: 52, ...axisStyle },
      visualMap: {
        min: lo, max: hi, calculable: true, orient: "vertical",
        right: 8, top: "middle", itemWidth: 12, itemHeight: 130,
        textStyle: { color: "#64748b", fontSize: 10 },
        inRange: { color: ["#dbeafe", "#93c5fd", "#34d399", "#fbbf24", "#ef4444"] },
      },
      series: [{ type: "heatmap", data, progressive: 2000,
                 emphasis: { itemStyle: { borderColor: "#0f172a", borderWidth: 1 } } }],
    };
    chart.setOption(opt, true);
  } else {
    const contourData = [];
    res.z.forEach((row, j) => row.forEach((v, i) => contourData.push([xs[i], ys[j], v])));
    const opt = {
      ...baseOption(),
      grid: { left: 70, right: 88, top: 44, bottom: 56 },
      tooltip: {
        ...baseOption().tooltip,
        formatter: (p) => `${res.x_label} ${p.data?.[0]}<br/>${res.y_label} ${p.data?.[1]}<br/><b>${p.data?.[2]} ${res.z_unit}</b>`,
      },
      xAxis: { type: "value", name: res.x_label, nameLocation: "middle", nameGap: 28, ...axisStyle },
      yAxis: { type: "value", name: res.y_label, nameLocation: "middle", nameGap: 52, ...axisStyle },
      visualMap: {
        min: lo, max: hi, calculable: true, orient: "vertical",
        right: 8, top: "middle", itemWidth: 12, itemHeight: 130,
        textStyle: { color: "#64748b", fontSize: 10 },
        inRange: { color: ["#dbeafe", "#93c5fd", "#34d399", "#fbbf24", "#ef4444"] },
      },
      series: [{
        type: "contour", data: contourData, smooth: true,
        lineStyle: { width: 1.1, color: "rgba(71,85,105,.55)" },
        label: { show: false },
      }],
    };
    chart.setOption(opt, true);
  }
}

/* ---------------- 生命周期 ---------------- */
function resize() { chart?.resize(); }

onMounted(async () => {
  syncRange();
  await nextTick();
  chart = echarts.init(chartEl.value, null, { renderer: "canvas" });
  window.addEventListener("resize", resize);
  render();
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resize);
  chart?.dispose();
});

watch([xKey], () => { syncRange(); render(); });
watch([outKey, chartType, steps], render);
watch(params, render, { deep: true });
</script>

<template>
  <div class="cv">
    <aside class="cv-left">
      <p class="panel-title">X 轴 · 扫描参数</p>
      <select v-model="xKey" style="width:100%">
        <option v-for="o in X_KEYS" :key="o.k" :value="o.k">{{ o.label }}</option>
      </select>

      <div class="range">
        <div class="slider-row">
          <div class="slider-lab"><span>起点</span><span class="val">{{ xRange.from }}</span></div>
          <input type="range" v-model.number="xRange.from" :min="0" :max="xRange.to" step="0.01" />
        </div>
        <div class="slider-row">
          <div class="slider-lab"><span>终点</span><span class="val">{{ xRange.to }}</span></div>
          <input type="range" v-model.number="xRange.to" :min="xRange.from" max="2000" step="0.01" />
        </div>
      </div>

      <p class="panel-title" style="margin-top:16px">Y 轴 · 输出变量</p>
      <select v-model="outKey" style="width:100%">
        <option v-for="o in OUT_KEYS" :key="o.k" :value="o.k">{{ o.label }}</option>
      </select>

      <p class="panel-title" style="margin-top:16px">图表类型</p>
      <div class="types">
        <button v-for="t in TYPES" :key="t.k" class="btn sm"
                :class="{ on: chartType === t.k }" @click="chartType = t.k">{{ t.label }}</button>
      </div>

      <div class="slider-row" style="margin-top:16px">
        <div class="slider-lab"><span>采样点数</span><span class="val">{{ steps }}</span></div>
        <input type="range" v-model.number="steps" min="10" max="200" step="5" />
      </div>

      <p class="note">
        热力/等高线为二维扫描：X 轴＝所选参数，Y 轴固定为
        <b style="color:var(--dim)">{{ outKey === 's_f' ? '扭矩 T' : '齿宽 b' }}</b>。
        改左侧参数界面会实时重绘。
      </p>
    </aside>

    <section class="cv-right">
      <div ref="chartEl" class="chart"></div>
      <div v-if="busy" class="loading">计算中…</div>
    </section>
  </div>
</template>

<style scoped>
.cv { display: flex; flex: 1; min-width: 0; min-height: 0; }
.cv-left {
  width: 274px; flex-shrink: 0; overflow-y: auto; padding: 16px 18px 34px;
  border-right: 1px solid var(--line);
  background: var(--panel2);
}
.range { margin-top: 10px; }
.types { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.cv-right { flex: 1; position: relative; min-width: 0; background: var(--panel); }
.chart { width: 100%; height: 100%; }
.loading {
  position: absolute; top: 14px; right: 18px; font-size: 11px; color: var(--dim2);
  background: var(--panel); padding: 5px 11px; border-radius: 7px;
  border: 1px solid var(--line); box-shadow: var(--shadow-sm);
}
</style>
