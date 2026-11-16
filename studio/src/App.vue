<script setup>
import { reactive, provide, ref } from "vue";
import ParamsView from "./views/ParamsView.vue";
import KpiBar from "./views/KpiBar.vue";
import ChartView from "./views/ChartView.vue";
import ModelView from "./views/ModelView.vue";
import { useSolve } from "./useSolve";

// 全局共享参数（四个区域共用同一份，改一处全联动）
const params = reactive({
  subject: "OrthogonalSpur",
  m: 6.35, z1: 25, z2: 160, zs: 27,
  alpha: 25, gamma: 90, ha_star: 1, c_star: 0.25,
  b: 80, r_in: 480, r_out: 560,
  torque: 1600, speed: 1000, life: 5000,
  s_h_lim: 1500, s_f_lim: 480, e_mod: 210000, nu: 0.3,
  k_hface: 1.45, quality: 7, beta: 0,
});

const { result, busy, err } = useSolve(params);

provide("params", params);
provide("result", result);
provide("busy", busy);
provide("err", err);

const showVars = ref(false);
provide("showVars", showVars);
</script>

<template>
  <div class="app">
    <header class="topbar">
      <div class="brand">
        <span class="mark"></span>FaceGear Studio<small>面齿轮设计与分析</small>
      </div>
      <div class="spacer"></div>
      <slot name="status"></slot>
    </header>

    <!-- 单页三区：左参数 / 右上函数 / 右下模型 -->
    <main class="grid">
      <section class="area area-left">
        <ParamsView />
      </section>

      <section class="area area-kpi">
        <KpiBar />
      </section>

      <section class="area area-chart">
        <ChartView />
      </section>

      <section class="area area-model">
        <ModelView />
      </section>
    </main>
  </div>
</template>

<style scoped>
.grid {
  flex: 1; min-height: 0;
  display: grid;
  grid-template-columns: minmax(360px, 1fr) 2fr;
  grid-template-rows: auto minmax(0, 1fr) minmax(0, 1fr);
  gap: 9px;
  padding: 9px;
}
.area {
  position: relative;
  min-width: 0; min-height: 0;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow: hidden;
}
.area-left { grid-column: 1; grid-row: 1 / span 3; background: var(--panel2); }
.area-kpi { grid-column: 2; grid-row: 1; }
.area-chart { grid-column: 2; grid-row: 2; }
.area-model { grid-column: 2; grid-row: 3; }

@media (max-width: 1080px) {
  .grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto minmax(0, 1fr) minmax(0, 1fr);
  }
  .area-left { grid-column: 1; grid-row: 1; }
  .area-kpi { grid-column: 1; grid-row: 2; }
  .area-chart { grid-column: 1; grid-row: 3; }
  .area-model { grid-column: 1; grid-row: 4; }
}
</style>
