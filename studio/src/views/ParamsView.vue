<script setup>
import { reactive, ref, watch, onMounted, inject, computed } from "vue";
import { solve, SUBJECTS } from "../api";

const params = inject("params");
const result = ref(null);
const busy = ref(false);
const err = ref("");
const showAll = ref(true);

/* ---------------- 参数表定义 ---------------- */
const GROUPS = [
  {
    title: "几何参数",
    items: [
      { k: "m", label: "模数 m", min: 1, max: 12, step: 0.05, dec: 2, unit: "mm" },
      { k: "z1", label: "小齿轮齿数 z₁", min: 8, max: 60, step: 1, dec: 0, unit: "" },
      { k: "z2", label: "面齿轮齿数 z₂", min: 20, max: 260, step: 1, dec: 0, unit: "" },
      { k: "zs", label: "插齿刀齿数 z_s", min: 8, max: 80, step: 1, dec: 0, unit: "" },
      { k: "alpha", label: "压力角 α", min: 14, max: 30, step: 0.5, dec: 1, unit: "°" },
      { k: "gamma", label: "轴交角 γ", min: 60, max: 120, step: 0.5, dec: 1, unit: "°" },
      { k: "ha_star", label: "齿顶高系数 ha*", min: 0.6, max: 1.2, step: 0.01, dec: 2, unit: "" },
      { k: "c_star", label: "顶隙系数 c*", min: 0.1, max: 0.4, step: 0.01, dec: 2, unit: "" },
      { k: "b", label: "齿宽 b", min: 5, max: 200, step: 1, dec: 0, unit: "mm" },
      { k: "r_in", label: "内半径", min: 20, max: 1200, step: 1, dec: 0, unit: "mm" },
      { k: "r_out", label: "外半径", min: 40, max: 1400, step: 1, dec: 0, unit: "mm" },
    ],
  },
  {
    title: "工况",
    items: [
      { k: "torque", label: "输入扭矩 T", min: 10, max: 8000, step: 10, dec: 0, unit: "N·m" },
      { k: "speed", label: "转速 n", min: 10, max: 8000, step: 10, dec: 0, unit: "rpm" },
      { k: "life", label: "设计寿命", min: 10, max: 20000, step: 10, dec: 0, unit: "h" },
    ],
  },
  {
    title: "材料",
    items: [
      { k: "s_h_lim", label: "接触疲劳极限 σ_Hlim", min: 300, max: 2000, step: 10, dec: 0, unit: "MPa" },
      { k: "s_f_lim", label: "弯曲疲劳极限 σ_Flim", min: 100, max: 800, step: 5, dec: 0, unit: "MPa" },
      { k: "e_mod", label: "弹性模量 E", min: 70000, max: 220000, step: 1000, dec: 0, unit: "MPa" },
      { k: "nu", label: "泊松比 ν", min: 0.2, max: 0.35, step: 0.005, dec: 3, unit: "" },
    ],
  },
  {
    title: "修正与精度",
    items: [
      { k: "k_hface", label: "面齿轮接触修正 K_Hface", min: 1.0, max: 2.0, step: 0.01, dec: 2, unit: "" },
      { k: "quality", label: "精度等级", min: 4, max: 12, step: 1, dec: 0, unit: "" },
      { k: "beta", label: "螺旋角 β（斜齿）", min: 0, max: 45, step: 0.5, dec: 1, unit: "°" },
    ],
  },
];

const PRESETS = [
  { name: "直升机", p: { m: 6.35, z1: 25, z2: 160, zs: 27, alpha: 25, b: 80, r_in: 480, r_out: 560, torque: 1600, speed: 1000, s_h_lim: 1500, s_f_lim: 480, k_hface: 1.45 } },
  { name: "工业减速器", p: { m: 4, z1: 20, z2: 100, zs: 22, alpha: 20, b: 50, r_in: 180, r_out: 230, torque: 800, speed: 1500, s_h_lim: 720, s_f_lim: 300, k_hface: 1.45 } },
  { name: "轻载", p: { m: 3, z1: 18, z2: 60, zs: 20, alpha: 20, b: 30, r_in: 80, r_out: 110, torque: 150, speed: 2000, s_h_lim: 680, s_f_lim: 280, k_hface: 1.35 } },
  { name: "极限", p: { m: 6.35, z1: 25, z2: 160, zs: 27, alpha: 25, b: 80, r_in: 480, r_out: 560, torque: 5000, speed: 1000, s_h_lim: 1500, s_f_lim: 480, k_hface: 1.45 } },
];

function applyPreset(pr) { Object.assign(params, pr.p); }

/* ---------------- 计算 ---------------- */
let timer = null;
async function run() {
  clearTimeout(timer);
  timer = setTimeout(async () => {
    busy.value = true;
    err.value = "";
    try {
      const p = { ...params };
      // Rust 端需要 subject 是枚举字符串
      result.value = await solve(p);
    } catch (e) {
      err.value = String(e);
    } finally {
      busy.value = false;
    }
  }, 90);
}

watch(params, run, { deep: true });
onMounted(run);

/* ---------------- 结果视图 ---------------- */
const byKey = computed(() => {
  const m = {};
  (result.value?.vars || []).forEach((v) => (m[v.key] = v));
  return m;
});

function val(k, dec = 2) {
  const v = byKey.value[k];
  if (!v) return "—";
  return v.value.toLocaleString(undefined, { maximumFractionDigits: dec, minimumFractionDigits: 0 });
}
function unit(k) { return byKey.value[k]?.unit || ""; }

const sH = computed(() => byKey.value.s_h?.value ?? 0);
const sHallow = computed(() => byKey.value.s_h_allow?.value ?? 1);
const sF = computed(() => byKey.value.s_f?.value ?? 0);
const sFallow = computed(() => byKey.value.s_f_allow?.value ?? 1);

const ratioH = computed(() => Math.min(sH.value / sHallow.value, 1.5));
const ratioF = computed(() => Math.min(sF.value / sFallow.value, 1.5));

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
  <div class="pv">
    <!-- ============ 左：参数 ============ -->
    <aside class="pv-left">
      <div class="block">
        <p class="panel-title">课题方向</p>
        <select v-model="params.subject" style="width:100%">
          <option v-for="(label, key) in SUBJECTS" :key="key" :value="key">
            {{ label }}{{ key === "OrthogonalSpur" ? "（完整）" : "（规划中）" }}
          </option>
        </select>
        <div class="presets">
          <button v-for="pr in PRESETS" :key="pr.name" class="btn sm"
                  @click="applyPreset(pr)">{{ pr.name }}</button>
        </div>
      </div>

      <div v-for="g in GROUPS" :key="g.title" class="block">
        <p class="panel-title">{{ g.title }}</p>
        <div v-for="it in g.items" :key="it.k" class="slider-row">
          <div class="slider-lab">
            <span>{{ it.label }}</span>
            <span class="val">{{ Number(params[it.k]).toFixed(it.dec) }}{{ it.unit }}</span>
          </div>
          <input type="range" v-model.number="params[it.k]"
                 :min="it.min" :max="it.max" :step="it.step" />
        </div>
      </div>
    </aside>

    <!-- ============ 右：结果 ============ -->
    <section class="pv-right">
      <div v-if="err" class="warnbox">计算错误：{{ err }}</div>
      <div v-for="(w, i) in result?.warnings || []" :key="i" class="warnbox">{{ w }}</div>

      <div class="cards">
        <div class="metric">
          <div class="t">接触应力 σ_H</div>
          <div class="n">{{ sH.toFixed(0) }}<small>MPa</small></div>
          <div class="sub">许用 {{ sHallow.toFixed(0) }} MPa · 占比 {{ (ratioH*100).toFixed(0) }}%</div>
          <div class="bar"><i :style="{
            width: Math.min(ratioH/1.5*100,100).toFixed(1)+'%',
            background: ratioH>1 ? 'linear-gradient(90deg,#f59e0b,#dc2626)' : 'linear-gradient(90deg,#10b981,#0891b2)'
          }"></i></div>
        </div>
        <div class="metric">
          <div class="t">齿根弯曲 σ_F</div>
          <div class="n">{{ sF.toFixed(0) }}<small>MPa</small></div>
          <div class="sub">许用 {{ sFallow.toFixed(0) }} MPa · 占比 {{ (ratioF*100).toFixed(0) }}%</div>
          <div class="bar"><i :style="{
            width: Math.min(ratioF/1.5*100,100).toFixed(1)+'%',
            background: ratioF>1 ? 'linear-gradient(90deg,#f59e0b,#dc2626)' : 'linear-gradient(90deg,#10b981,#0891b2)'
          }"></i></div>
        </div>
        <div class="metric">
          <div class="t">安全系数</div>
          <div class="n" style="font-size:18px">
            S_H {{ val('safety_h') }} <span style="color:var(--dim2)">/</span> S_F {{ val('safety_f') }}
          </div>
          <div class="sub">要求 ≥ {{ byKey.safety_h ? result.vars.find(v=>v.key==='safety_h')?.value>=1.18?'1.18':'1.18' : '1.18' }} / 1.76</div>
        </div>
      </div>

      <div class="verdict" :class="result?.verdict_ok ? 'ok' : 'bad'">
        {{ result?.verdict_text || '计算中…' }}
      </div>

      <div class="quick">
        <div class="kv"><span>传动比 u</span><b>{{ val('u', 2) }}</b></div>
        <div class="kv"><span>重合度 ε_α</span><b>{{ val('eps', 3) }}</b></div>
        <div class="kv"><span>切向力 F_t</span><b>{{ val('ft', 0) }} N</b></div>
        <div class="kv"><span>节线速度 v</span><b>{{ val('vel', 2) }} m/s</b></div>
        <div class="kv"><span>功率 P</span><b>{{ val('power', 1) }} kW</b></div>
        <div class="kv"><span>面齿轮分度圆 r_fp</span><b>{{ val('r_fp', 1) }} mm</b></div>
      </div>

      <div class="allhead" @click="showAll = !showAll">
        <span>{{ showAll ? '▾' : '▸' }} 全部变量（{{ result?.vars?.length || 0 }} 项）</span>
      </div>
      <div v-if="showAll" class="allvars">
        <div v-for="[g, list] in grouped" :key="g" class="grp">
          <div class="gtitle">{{ g }}</div>
          <div class="grow" v-for="v in list" :key="v.key">
            <span class="gl">{{ v.label }}</span>
            <span class="gv">{{ v.value.toLocaleString(undefined, { maximumFractionDigits: 3 }) }} <em>{{ v.unit }}</em></span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.pv { display: flex; flex: 1; min-width: 0; min-height: 0; }

/* 左栏 */
.pv-left {
  width: 336px; flex-shrink: 0; overflow-y: auto;
  padding: 16px 18px 34px;
  border-right: 1px solid var(--line);
  background: var(--panel2);
}
.block { margin-bottom: 18px; }
.presets { display: flex; gap: 6px; margin-top: 10px; flex-wrap: wrap; }
.presets .btn { flex: 1; min-width: 62px; text-align: center; }

/* 右栏 */
.pv-right { flex: 1; overflow-y: auto; padding: 16px 22px 34px; min-width: 0; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(196px, 1fr)); gap: 11px; }
.quick { margin-top: 14px; max-width: 540px; }

.allhead {
  margin-top: 18px; font-size: 12px; color: var(--dim); cursor: pointer;
  padding: 9px 0; border-top: 1px solid var(--line); letter-spacing: 0.02em;
  font-weight: 500;
}
.allhead:hover { color: var(--brand); }
.allvars {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(286px, 1fr));
  gap: 12px; margin-top: 8px;
}
.grp {
  background: var(--panel); border: 1px solid var(--line);
  border-radius: 9px; padding: 11px 13px; box-shadow: var(--shadow-sm);
}
.gtitle {
  font-size: 10.5px; color: var(--dim2); letter-spacing: 0.14em;
  margin-bottom: 7px; font-weight: 600; text-transform: uppercase;
}
.grow {
  display: flex; justify-content: space-between; padding: 3px 0;
  font-size: 11.5px; border-bottom: 1px solid #f2f5f9;
}
.grow:last-child { border-bottom: none; }
.gl { color: var(--dim); }
.gv { color: var(--ink); font-family: Consolas, monospace; font-weight: 500; }
.gv em { color: var(--dim2); font-style: normal; font-size: 10px; }
</style>
