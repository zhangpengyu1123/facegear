<script setup>
import { computed, inject, ref } from "vue";
import { fmt, utilColor } from "../format";
import { indexVars } from "../useSolve";

const result = inject("result");
const showVars = inject("showVars");

const V = computed(() => indexVars(result.value));

const nH = computed(() => V.value.s_h?.value ?? 0);
const nF = computed(() => V.value.s_f?.value ?? 0);
const aH = computed(() => V.value.s_h_allow?.value ?? 1);
const aF = computed(() => V.value.s_f_allow?.value ?? 1);
const S_H = computed(() => V.value.safety_h?.value ?? 0);
const S_F = computed(() => V.value.safety_f?.value ?? 0);

const uH = computed(() => utilColor(nH.value / aH.value));
const uF = computed(() => utilColor(nF.value / aF.value));
const uSH = computed(() => utilColor(S_H.value > 0 ? 1.18 / S_H.value : 0));

const pct = (r) => Math.min(Math.max(r, 0) * 100, 100).toFixed(0) + "%";

/** 关键辅助值 */
const aux = computed(() => [
  { l: "u", v: fmt(V.value.u?.value, "u") },
  { l: "ε_α", v: fmt(V.value.eps?.value, "eps") },
  { l: "F_t", v: fmt(V.value.ft?.value, "ft") + " N" },
  { l: "P", v: fmt(V.value.power?.value, "power") + " kW" },
]);

const grouped = computed(() => {
  const g = new Map();
  (result.value?.vars || []).forEach((v) => {
    if (!g.has(v.group)) g.set(v.group, []);
    g.get(v.group).push(v);
  });
  return [...g.entries()];
});
</script>

<template>
  <div class="kpi">
    <!-- 三个核心指标 -->
    <div class="cell">
      <div class="ct">σ_H 接触</div>
      <div class="cv">
        {{ fmt(nH, "s_h") }}<em>MPa</em>
        <span class="tag" :style="{ color: uH.fg }">{{ uH.label }}</span>
      </div>
      <div class="cbar"><i :style="{ width: pct(nH / aH), background: uH.bar }"></i></div>
    </div>

    <div class="cell">
      <div class="ct">σ_F 弯曲</div>
      <div class="cv">
        {{ fmt(nF, "s_f") }}<em>MPa</em>
        <span class="tag" :style="{ color: uF.fg }">{{ uF.label }}</span>
      </div>
      <div class="cbar"><i :style="{ width: pct(nF / aF), background: uF.bar }"></i></div>
    </div>

    <div class="cell">
      <div class="ct">安全系数 S_H / S_F</div>
      <div class="cv">
        {{ fmt(S_H, "safety_h") }}<em>/ {{ fmt(S_F, "safety_f") }}</em>
        <span class="tag" :style="{ color: uSH.fg }">要求 1.18</span>
      </div>
      <div class="cbar"><i :style="{ width: pct(1.18 / S_H || 0), background: uSH.bar }"></i></div>
    </div>

    <!-- 判定 -->
    <div class="cell verdict-cell" :class="result?.verdict_ok ? 'ok' : 'bad'">
      <div class="vmark">{{ result?.verdict_ok ? "✓" : "✗" }}</div>
      <div class="vtxt">{{ result?.verdict_ok ? "合格" : "不合格" }}</div>
    </div>

    <!-- 辅助值 -->
    <div class="aux">
      <div class="ax" v-for="a in aux" :key="a.l">
        <span class="al">{{ a.l }}</span>
        <span class="av">{{ a.v }}</span>
      </div>
    </div>

    <button class="varsbtn" @click="showVars = !showVars"
            :class="{ on: showVars }">
      变量 {{ result?.vars?.length || 0 }}
    </button>

    <!-- 全部变量浮层 -->
    <div v-if="showVars" class="vars-pop">
      <div class="vp-head">
        <span>全部变量</span>
        <button class="btn sm ghost" @click="showVars = false">关闭</button>
      </div>
      <div class="vp-body">
        <div v-for="[g, list] in grouped" :key="g" class="grp">
          <div class="gtitle">{{ g }}</div>
          <div class="grow" v-for="v in list" :key="v.key">
            <span class="gl">{{ v.label }}</span>
            <span class="gv">{{ fmt(v.value, v.key) }}<em v-if="v.unit">{{ v.unit }}</em></span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!result" class="loading">计算中…</div>
  </div>
</template>

<style scoped>
.kpi {
  position: relative;
  display: flex; align-items: stretch;
  height: 100%; min-height: 92px;
  padding: 10px 14px; gap: 18px;
}

/* 指标单元 */
.cell {
  flex: 0 0 auto; min-width: 150px;
  display: flex; flex-direction: column; justify-content: center;
  padding-right: 18px; border-right: 1px solid var(--line);
}
.cell:last-of-type { border-right: none; }
.ct {
  font-size: 10.5px; color: var(--dim2); letter-spacing: 0.06em;
  margin-bottom: 3px; font-weight: 500;
}
.cv {
  font-family: Consolas, "SF Mono", monospace; font-size: 21px;
  font-weight: 650; letter-spacing: -0.02em; color: var(--ink);
  font-variant-numeric: tabular-nums; line-height: 1.15;
  display: flex; align-items: baseline; gap: 6px;
}
.cv em { font-size: 10.5px; font-weight: 500; color: var(--dim2); font-style: normal; }
.tag { font-size: 10px; font-weight: 600; font-family: inherit; letter-spacing: 0.02em; }
.cbar { height: 4px; border-radius: 2px; background: #edf1f6; margin-top: 7px; overflow: hidden; }
.cbar i { display: block; height: 100%; border-radius: 2px; transition: width 0.25s, background 0.25s; }

/* 判定块 */
.verdict-cell {
  flex: 0 0 auto; min-width: 92px; border-right: none;
  align-items: center; border-radius: 8px; padding: 6px 12px;
  flex-direction: row; gap: 8px;
}
.verdict-cell.ok { background: var(--ok-soft); border: 1px solid #a7e8c8; }
.verdict-cell.bad { background: var(--bad-soft); border: 1px solid #fbc4c4; }
.vmark { font-size: 19px; font-weight: 700; line-height: 1; }
.verdict-cell.ok .vmark, .verdict-cell.ok .vtxt { color: #047857; }
.verdict-cell.bad .vmark, .verdict-cell.bad .vtxt { color: #b91c1c; }
.vtxt { font-size: 12.5px; font-weight: 600; }

/* 辅助值 */
.aux {
  flex: 1; display: flex; align-items: center; justify-content: flex-end;
  gap: 16px; flex-wrap: wrap; min-width: 0;
}
.ax { display: flex; flex-direction: column; align-items: flex-end; }
.al { font-size: 10px; color: var(--dim2); letter-spacing: 0.04em; }
.av {
  font-family: Consolas, monospace; font-size: 12px; font-weight: 600;
  color: var(--ink); font-variant-numeric: tabular-nums;
}

.varsbtn {
  flex: 0 0 auto; align-self: center;
  background: var(--panel2); border: 1px solid var(--line2);
  color: var(--dim); font-size: 11.5px; padding: 6px 12px;
  border-radius: 7px; cursor: pointer; font-family: inherit;
  transition: 0.15s; white-space: nowrap;
}
.varsbtn:hover { border-color: #b8c4d4; color: var(--ink); }
.varsbtn.on { border-color: var(--brand); color: var(--brand2); background: var(--brand-soft); }

/* 变量浮层 */
.vars-pop {
  position: absolute; right: 10px; top: calc(100% + 6px);
  width: min(880px, 92%);
  max-height: 62vh;
  background: var(--panel); border: 1px solid var(--line2);
  border-radius: 11px; box-shadow: 0 12px 40px rgba(15, 23, 42, 0.18);
  z-index: 50; display: flex; flex-direction: column;
  overflow: hidden;
}
.vp-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px; border-bottom: 1px solid var(--line);
  font-size: 12px; font-weight: 600; color: var(--ink);
  background: var(--panel2);
}
.vp-body {
  padding: 12px; overflow-y: auto;
  display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 10px;
}
.grp { background: var(--panel2); border: 1px solid var(--line); border-radius: 8px; padding: 9px 11px; }
.gtitle {
  font-size: 10px; color: var(--dim2); letter-spacing: 0.14em;
  margin-bottom: 6px; font-weight: 600; text-transform: uppercase;
}
.grow {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 3px 0; font-size: 11px; border-bottom: 1px solid #eef2f7;
}
.grow:last-child { border-bottom: none; }
.gl { color: var(--dim); }
.gv {
  color: var(--ink); font-family: Consolas, monospace; font-weight: 500;
  font-variant-numeric: tabular-nums;
}
.gv em { color: var(--dim2); font-style: normal; font-size: 9.5px; margin-left: 3px; }

.loading {
  position: absolute; right: 14px; top: 50%; transform: translateY(-50%);
  font-size: 11px; color: var(--dim2);
}
</style>
