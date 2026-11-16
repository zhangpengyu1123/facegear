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
  axisTick: { lineStyle: { color: "#cbd5e1" }, length: 4 },
  axisLabel: { color: "#475569", fontSize: 11 },
  splitLine: { lineStyle: { color: "#e8edf5", width: 1 } },
  minorSplitLine: { show: true, lineStyle: { color: "#f2f5fa" } },
  minorTick: { show: true, lineStyle: { color: "#dfe6ef" } },
  nameTextStyle: { color: "#334155", fontSize: 11.5, fontWeight: 500 },
};

function baseOption(title) {
  return {
    backgroundColor: "transparent",
    grid: { left: 62, right: 26, top: 38, bottom: 44 },
    title: title ? {
      text: title,
      left: 4, top: 4,
      textStyle: { color: "#0f172a", fontSize: 12, fontWeight: 600 },
    } : undefined,
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
      updateWorkPoint(res);
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

  const title = `${res.y_label} 随 ${res.x_label} 的变化`;
  const opt = {
    ...baseOption(title),
    legend: {
      right: 8, top: 4, itemWidth: 13, itemHeight: 7, itemGap: 12,
      textStyle: { color: "#475569", fontSize: 10.5 },
      data: [res.y_label],
    },
    xAxis: {
      type: isBar ? "category" : "value",
      data: isBar ? xs.map((x) => x.toFixed(2)) : undefined,
      min: isBar ? undefined : xs[0],
      max: isBar ? undefined : xs[xs.length - 1],
      name: `${res.x_label}${res.x_unit ? " (" + res.x_unit + ")" : ""}`,
      nameLocation: "middle", nameGap: 32,
      ...axisStyle,
      axisLabel: { ...axisStyle.axisLabel, rotate: isBar ? 45 : 0,
                   formatter: (v) => (Number.isFinite(+v) ? (+v).toFixed(1) : v) },
    },
    yAxis: {
      type: "value",
      scale: true,
      name: `${res.y_label}${res.y_unit ? " (" + res.y_unit + ")" : ""}`,
      nameLocation: "middle", nameGap: 52,
      // 让许用阈值线始终可见（超出数据范围时自动扩展坐标轴）
      max: (v) => {
        const th = THRESHOLD[outKey.value];
        return th ? Math.max(v.max, th.value) * 1.02 : v.max * 1.05;
      },
      ...axisStyle,
    },
    series: [{
      name: res.y_label,
      type: isBar ? "bar" : isScatter ? "scatter" : "line",
      data: isBar ? res.ys.map((y, i) => [xs[i], y]) : xs.map((x, i) => [x, res.ys[i]]),
      smooth: !isScatter && !isBar,
      symbolSize: isScatter ? 7 : 5,
      showSymbol: isScatter || xs.length <= 30,
      lineStyle: { width: 2.2, color: "#2563eb" },
      itemStyle: { color: "#2563eb", borderColor: "#fff", borderWidth: isScatter ? 1 : 0 },
      areaStyle: (!isScatter && !isBar) ? {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: "rgba(37,99,235,.20)" },
          { offset: 1, color: "rgba(37,99,235,.01)" },
        ]),
      } : undefined,
      barWidth: isBar ? "58%" : undefined,
      barMaxWidth: 26,
      // 许用阈值线（仅当看应力类变量时）
      markLine: THRESHOLD[outKey.value] ? {
        silent: true, symbol: "none",
        lineStyle: { color: "#dc2626", type: "dashed", width: 1.2, opacity: 0.75 },
        label: {
          formatter: `许用 ${THRESHOLD[outKey.value].value} ${THRESHOLD[outKey.value].unit}`,
          color: "#dc2626", fontSize: 10.5, position: "insideEndTop",
        },
        data: [{ yAxis: THRESHOLD[outKey.value].value }],
      } : undefined,
      // 当前参数所在工作点
      markPoint: workPoint.value ? {
        symbol: "pin", symbolSize: 44,
        itemStyle: { color: "#0f172a" },
        label: { color: "#fff", fontSize: 9.5, formatter: workPoint.value.label },
        data: [{ coord: [workPoint.value.x, workPoint.value.y] }],
      } : undefined,
    }],
  };
  chart.setOption(opt, true);
}

/** 应力类变量的许用值（画阈值线用） */
const THRESHOLD = {
  s_h: { value: 1500, unit: "MPa" },
  s_f: { value: 960, unit: "MPa" },
};

/** 当前参数对应的工作点（x = 当前扫描参数值，y = 当前输出值） */
const workPoint = ref(null);
const curPoint = ref(null);
function updateWorkPoint(res) {
  const cur = params[xKey.value];
  curPoint.value = { x: cur, xUnit: res.x_unit, xLabel: res.x_label, y: null, yUnit: res.out_unit, yLabel: res.y_label };
  if (!Number.isFinite(cur)) { workPoint.value = null; return; }
  const xs = res.xs, ys = res.ys;
  let best = 0, bd = Infinity;
  for (let i = 0; i < xs.length; i++) {
    const d = Math.abs(xs[i] - cur);
    if (d < bd) { bd = d; best = i; }
  }
  curPoint.value.y = ys[best];
  if (cur < xs[0] || cur > xs[xs.length - 1]) { workPoint.value = null; return; }
  workPoint.value = {
    x: +xs[best].toFixed(3),
    y: +ys[best].toFixed(1),
    label: `当前 ${cur}`,
  };
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
      ...baseOption(`${res.z_label} 二维分布（${res.x_label} × ${res.y_label}）`),
      grid: { left: 74, right: 92, top: 58, bottom: 58 },
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
      ...baseOption(`${res.z_label} 等值线（${res.x_label} × ${res.y_label}）`),
      grid: { left: 74, right: 92, top: 58, bottom: 58 },
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
    <!-- 工具条 -->
    <div class="bar">
      <div class="field">
        <label>X 轴</label>
        <select v-model="xKey" class="sel">
          <option v-for="o in X_KEYS" :key="o.k" :value="o.k">{{ o.label }}</option>
        </select>
      </div>
      <div class="field">
        <label>范围</label>
        <input type="number" v-model.number="xRange.from" step="0.01" class="num" />
        <span class="tilde">~</span>
        <input type="number" v-model.number="xRange.to" step="0.01" class="num" />
      </div>
      <div class="field">
        <label>Y 轴</label>
        <select v-model="outKey" class="sel">
          <option v-for="o in OUT_KEYS" :key="o.k" :value="o.k">{{ o.label }}</option>
        </select>
      </div>
      <div class="field">
        <label>图型</label>
        <div class="seg">
          <button v-for="t in TYPES" :key="t.k" class="segbtn"
                  :class="{ on: chartType === t.k }" @click="chartType = t.k">{{ t.label }}</button>
        </div>
      </div>
      <div class="field">
        <label>采样</label>
        <input type="range" v-model.number="steps" min="10" max="200" step="5" class="rng" />
        <span class="steps-v">{{ steps }}</span>
      </div>
      <div class="spacer"></div>
      <div class="wp" v-if="curPoint">
        <b>{{ curPoint.y !== null ? curPoint.y.toFixed(1) : "—" }}<em>{{ curPoint.yUnit }}</em></b>
        <span class="wp-tag">当前值</span>
      </div>
    </div>

    <!-- 图表 -->
    <div class="chartwrap">
      <div ref="chartEl" class="chart"></div>
      <div v-if="busy" class="loading">计算中…</div>
    </div>
  </div>
</template>

<style scoped>
.cv { display: flex; flex-direction: column; height: 100%; min-height: 0; }

/* 工具条 */
.bar {
  flex-shrink: 0; display: flex; align-items: center;
  gap: 9px; padding: 6px 11px;
  min-height: 38px; box-sizing: border-box;
  border-bottom: 1px solid var(--line);
  background: var(--panel2); flex-wrap: nowrap; overflow: hidden;
}
.field { display: flex; align-items: center; gap: 5px; flex: 0 0 auto; }
.field > label {
  font-size: 10px; color: var(--dim2); letter-spacing: 0.02em;
  white-space: nowrap; font-weight: 500;
}
.sel { font-size: 11px; padding: 4px 6px; border-radius: 6px; min-width: 78px; max-width: 96px; }
.num { width: 54px; font-size: 11px; padding: 4px 5px; border-radius: 6px; }
.tilde { color: var(--dim2); font-size: 10px; }

.seg {
  display: flex; border: 1px solid var(--line2); border-radius: 6px;
  overflow: hidden; background: var(--panel); flex: 0 0 auto;
}
.segbtn {
  border: none; background: transparent; font-size: 10.5px;
  padding: 4.5px 7px; color: var(--dim); cursor: pointer;
  font-family: inherit; border-right: 1px solid var(--line);
  transition: background 0.14s, color 0.14s; white-space: nowrap;
}
.segbtn:last-child { border-right: none; }
.segbtn:hover { background: var(--panel3); }
.segbtn.on {
  background: var(--brand-soft); color: var(--brand2); font-weight: 600;
}

.rng { width: 58px; flex: 0 0 auto; }
.steps-v {
  font-size: 10.5px; font-family: Consolas, monospace;
  color: var(--ink); min-width: 20px; font-weight: 600;
}
.spacer { flex: 1 1 auto; min-width: 4px; }

.wp {
  display: flex; align-items: baseline; gap: 5px; flex: 0 0 auto;
  font-size: 10.5px; color: var(--dim); white-space: nowrap;
}
.wp b {
  font-family: Consolas, monospace; color: var(--ink);
  font-size: 11.5px; font-variant-numeric: tabular-nums; font-weight: 600;
}
.wp em { color: var(--dim2); font-style: normal; font-size: 9px; margin-left: 2px; }
.wp-tag {
  font-size: 9.5px; color: var(--dim2); background: var(--panel3);
  padding: 1px 5px; border-radius: 4px; border: 1px solid var(--line);
}

/* 图表 */
.chartwrap { flex: 1; position: relative; min-height: 0; }
.chart { width: 100%; height: 100%; }
.loading {
  position: absolute; top: 10px; right: 14px; font-size: 11px; color: var(--dim2);
  background: var(--panel); padding: 4px 10px; border-radius: 6px;
  border: 1px solid var(--line); box-shadow: var(--shadow-sm);
}
</style>
