<script setup>
import { ref, reactive, provide, computed, watch } from "vue";
import ParamsView from "./views/ParamsView.vue";
import ChartView from "./views/ChartView.vue";
import ModelView from "./views/ModelView.vue";
import { isTauri } from "./api";

const TABS = [
  { id: "params", label: "参数输入", icon: "⚙" },
  { id: "chart", label: "函数曲线", icon: "∿" },
  { id: "model", label: "模型展示", icon: "◈" },
];

const active = ref(
  ["params", "chart", "model"].includes(location.hash.slice(1))
    ? location.hash.slice(1)
    : "params"
);
watch(active, (v) => { location.hash = v; });

// 全局共享参数（三个界面共用同一份，改一处全联动）
const params = reactive({
  subject: "OrthogonalSpur",
  m: 6.35, z1: 25, z2: 160, zs: 27,
  alpha: 25, gamma: 90, ha_star: 1, c_star: 0.25,
  b: 80, r_in: 480, r_out: 560,
  torque: 1600, speed: 1000, life: 5000,
  s_h_lim: 1500, s_f_lim: 480, e_mod: 210000, nu: 0.3,
  k_hface: 1.45, quality: 7, beta: 0,
});

provide("params", params);
provide("goto", (id) => (active.value = id));

const statusText = computed(() =>
  isTauri ? "Tauri · Rust 内核" : "浏览器预览 · JS 降级"
);
</script>

<template>
  <div class="app">
    <div class="topbar">
      <div class="brand">
        <span class="mark"></span>FaceGear Studio<small>面齿轮设计与分析</small>
      </div>
      <div class="tabs">
        <div
          v-for="t in TABS" :key="t.id"
          class="tab" :class="{ active: active === t.id }"
          @click="active = t.id"
        >
          <span style="opacity:.7;margin-right:6px">{{ t.icon }}</span>{{ t.label }}
        </div>
      </div>
      <div class="spacer"></div>
      <div class="status"><b>{{ statusText }}</b></div>
    </div>

    <div class="body">
      <ParamsView v-show="active === 'params'" />
      <ChartView v-show="active === 'chart'" />
      <ModelView v-show="active === 'model'" />
    </div>
  </div>
</template>
