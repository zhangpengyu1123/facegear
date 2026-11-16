<script setup>
import { ref, inject } from "vue";
import { SUBJECTS } from "../api";
import { fmtParam } from "../format";

const params = inject("params");
const activePreset = ref("heli");

/* ---------------- 参数定义 ---------------- */
const GROUPS = [
  {
    title: "几何", open: true,
    items: [
      { k: "m", label: "模数 m", min: 1, max: 12, step: 0.05, dec: 2, unit: "mm" },
      { k: "z1", label: "小齿轮齿数 z₁", min: 8, max: 60, step: 1, dec: 0, unit: "" },
      { k: "z2", label: "面齿轮齿数 z₂", min: 20, max: 260, step: 1, dec: 0, unit: "" },
      { k: "zs", label: "插齿刀齿数 z_s", min: 8, max: 80, step: 1, dec: 0, unit: "" },
      { k: "alpha", label: "压力角 α", min: 14, max: 30, step: 0.5, dec: 1, unit: "°" },
      { k: "gamma", label: "轴交角 γ", min: 60, max: 120, step: 0.5, dec: 1, unit: "°" },
      { k: "ha_star", label: "齿顶高系数 ha*", min: 0.6, max: 1.2, step: 0.01, dec: 2, unit: "" },
      { k: "c_star", label: "顶隙系数 c*", min: 0.1, max: 0.4, step: 0.01, dec: 2, unit: "" },
      { k: "b", label: "齿宽 b", min: 5, max: 200, step: 1, dec: 1, unit: "mm" },
      { k: "r_in", label: "内半径", min: 20, max: 1200, step: 1, dec: 1, unit: "mm" },
      { k: "r_out", label: "外半径", min: 40, max: 1400, step: 1, dec: 1, unit: "mm" },
    ],
  },
  {
    title: "工况", open: true,
    items: [
      { k: "torque", label: "输入扭矩 T", min: 10, max: 8000, step: 10, dec: 0, unit: "N·m" },
      { k: "speed", label: "转速 n", min: 10, max: 8000, step: 10, dec: 0, unit: "rpm" },
      { k: "life", label: "设计寿命", min: 10, max: 20000, step: 10, dec: 0, unit: "h" },
    ],
  },
  {
    title: "材料", open: false,
    items: [
      { k: "s_h_lim", label: "接触疲劳极限 σ_Hlim", min: 300, max: 2000, step: 10, dec: 0, unit: "MPa" },
      { k: "s_f_lim", label: "弯曲疲劳极限 σ_Flim", min: 100, max: 800, step: 5, dec: 0, unit: "MPa" },
      { k: "e_mod", label: "弹性模量 E", min: 70000, max: 220000, step: 1000, dec: 0, unit: "MPa" },
      { k: "nu", label: "泊松比 ν", min: 0.2, max: 0.35, step: 0.005, dec: 3, unit: "" },
    ],
  },
  {
    title: "修正与精度", open: false,
    items: [
      { k: "k_hface", label: "面齿轮接触修正 K_Hface", min: 1.0, max: 2.0, step: 0.01, dec: 2, unit: "" },
      { k: "quality", label: "精度等级", min: 4, max: 12, step: 1, dec: 0, unit: "" },
      { k: "beta", label: "螺旋角 β（斜齿）", min: 0, max: 45, step: 0.5, dec: 1, unit: "°" },
    ],
  },
];

const PRESETS = [
  { id: "heli", name: "直升机", p: { m: 6.35, z1: 25, z2: 160, zs: 27, alpha: 25, b: 80, r_in: 480, r_out: 560, torque: 1600, speed: 1000, s_h_lim: 1500, s_f_lim: 480, k_hface: 1.45 } },
  { id: "ind", name: "减速器", p: { m: 4, z1: 20, z2: 100, zs: 22, alpha: 20, b: 50, r_in: 180, r_out: 230, torque: 800, speed: 1500, s_h_lim: 720, s_f_lim: 300, k_hface: 1.45 } },
  { id: "light", name: "轻载", p: { m: 3, z1: 18, z2: 60, zs: 20, alpha: 20, b: 30, r_in: 80, r_out: 110, torque: 150, speed: 2000, s_h_lim: 680, s_f_lim: 280, k_hface: 1.35 } },
  { id: "limit", name: "极限", p: { m: 6.35, z1: 25, z2: 160, zs: 27, alpha: 25, b: 80, r_in: 480, r_out: 560, torque: 5000, speed: 1000, s_h_lim: 1500, s_f_lim: 480, k_hface: 1.45 } },
];

function applyPreset(pr) {
  Object.assign(params, pr.p);
  activePreset.value = pr.id;
}
</script>

<template>
  <div class="pv">
    <!-- 课题 + 预设 -->
    <div class="head">
      <select v-model="params.subject" class="subj">
        <option v-for="(label, key) in SUBJECTS" :key="key" :value="key">
          {{ label }}{{ key === "OrthogonalSpur" ? "" : " · 规划中" }}
        </option>
      </select>
      <div class="presets">
        <button v-for="pr in PRESETS" :key="pr.id" class="btn sm"
                :class="{ on: activePreset === pr.id }"
                @click="applyPreset(pr)">{{ pr.name }}</button>
      </div>
    </div>

    <!-- 参数分组 -->
    <div class="scroll">
      <div v-for="g in GROUPS" :key="g.title" class="grp">
        <div class="ghead" @click="g.open = !g.open">
          <span class="chev" :class="{ open: g.open }">▸</span>
          <span class="gname">{{ g.title }}</span>
          <span class="gcount">{{ g.items.length }}</span>
        </div>
        <div v-if="g.open" class="gbody">
          <div v-for="it in g.items" :key="it.k" class="slider-row">
            <div class="slider-lab">
              <span>{{ it.label }}</span>
              <span class="val">{{ fmtParam(params[it.k], it.dec, it.unit) }}</span>
            </div>
            <input type="range" v-model.number="params[it.k]"
                   :min="it.min" :max="it.max" :step="it.step" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pv {
  display: flex; flex-direction: column;
  height: 100%; min-height: 0;
}

/* 顶部固定区 */
.head {
  flex-shrink: 0; padding: 12px 14px 10px;
  border-bottom: 1px solid var(--line);
  background: var(--panel2);
}
.subj { width: 100%; }
.presets { display: flex; gap: 5px; margin-top: 8px; }
.presets .btn {
  flex: 1; text-align: center; padding: 5px 2px;
  font-size: 11px; white-space: nowrap;
}

/* 可滚动参数区 */
.scroll {
  flex: 1; min-height: 0; overflow-y: auto;
  padding: 10px 14px 28px;
}

.grp { margin-bottom: 10px; }
.ghead {
  display: flex; align-items: center; gap: 7px;
  padding: 7px 0 6px; cursor: pointer;
  border-bottom: 1px solid var(--line);
  user-select: none;
}
.ghead:hover .gname { color: var(--brand); }
.chev {
  font-size: 9px; color: var(--dim2); transition: transform 0.16s;
  display: inline-block;
}
.chev.open { transform: rotate(90deg); }
.gname {
  font-size: 11px; font-weight: 600; letter-spacing: 0.1em;
  color: var(--dim); text-transform: uppercase;
  transition: color 0.15s;
}
.gcount {
  margin-left: auto; font-size: 10px; color: var(--dim2);
  font-family: Consolas, monospace;
  background: var(--panel3); padding: 1px 6px; border-radius: 4px;
}
.gbody { padding-top: 9px; }
</style>
