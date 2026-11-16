<script setup>
import { computed, ref, onBeforeUnmount } from "vue";

const props = defineProps({
  list: { type: Array, default: () => [] },
  activeId: { type: String, default: null },
});
const emit = defineEmits(["snap", "restore", "remove", "clear"]);

const hover = ref(null);
const trackEl = ref(null);

/** 打点等距排布在轨道上（首个 2%，末个 98%） */
function posOf(i, n) {
  if (n === 1) return 50;
  return 2 + (i / (n - 1)) * 96;
}

const positioned = computed(() =>
  props.list.map((cp, i) => ({ ...cp, pct: posOf(i, props.list.length) }))
);

function fmtTime(ts) {
  const d = new Date(ts);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}:${String(d.getSeconds()).padStart(2, "0")}`;
}

let pressTimer = null;
function onDown(cp) {
  pressTimer = setTimeout(() => emit("remove", cp.id), 750);
}
function onUp() {
  clearTimeout(pressTimer);
}
</script>

<template>
  <footer class="tl">
    <!-- 左：打点按钮 -->
    <div class="tl-left">
      <button class="snap" @click="emit('snap')" title="记录当前全部参数">
        <span class="plus">⊕</span> 打点
      </button>
    </div>

    <!-- 中：轨道 -->
    <div class="tl-track" ref="trackEl">
      <div class="rail"></div>
      <div class="rail-fill" v-if="positioned.length > 1"
           :style="{ width: (positioned[positioned.length - 1].pct - positioned[0].pct) + '%',
                     left: positioned[0].pct + '%' }"></div>

      <div
        v-for="cp in positioned" :key="cp.id"
        class="cp" :class="{ active: cp.id === activeId }"
        :style="{ left: cp.pct + '%' }"
        @click="emit('restore', cp)"
        @mouseenter="hover = cp.id"
        @mouseleave="hover = null; onUp()"
        @mousedown="onDown(cp)"
        @mouseup="onUp">
        <span class="dot"></span>
        <span class="idx">{{ cp.index }}</span>

        <!-- 悬停详情 -->
        <div class="tip" v-if="hover === cp.id">
          <div class="tip-name">{{ cp.name }}</div>
          <div class="tip-sum">{{ cp.summary }}</div>
          <div class="tip-time">{{ fmtTime(cp.time) }}</div>
          <div class="tip-hint">点击回到 · 长按删除</div>
        </div>
      </div>

      <span v-if="!positioned.length" class="empty-tip">
        还没有打点 —— 调好参数后点左侧「⊕ 打点」，随时可回到这一刻
      </span>
    </div>

    <!-- 右：计数 + 清空 -->
    <div class="tl-right">
      <span class="cnt">{{ list.length }} 个</span>
      <button v-if="list.length" class="clr" @click="emit('clear')" title="清空全部打点">清空</button>
    </div>
  </footer>
</template>

<style scoped>
.tl {
  flex-shrink: 0; height: 50px;
  display: flex; align-items: center; gap: 12px;
  padding: 0 14px;
  background: var(--panel);
  border-top: 1px solid var(--line);
  box-shadow: 0 -1px 3px rgba(15, 23, 42, 0.04);
  z-index: 20;
}

/* 打点按钮 */
.snap {
  display: flex; align-items: center; gap: 5px;
  background: var(--brand); border: 1px solid var(--brand2);
  color: #fff; font-size: 12px; font-weight: 600;
  padding: 6px 14px; border-radius: 7px; cursor: pointer;
  font-family: inherit; transition: 0.15s;
  box-shadow: 0 1px 3px rgba(37, 99, 235, 0.28);
}
.snap:hover { background: var(--brand2); box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35); }
.snap:active { transform: translateY(1px); }
.plus { font-size: 13px; line-height: 1; }

/* 轨道 */
.tl-track {
  position: relative; flex: 1; height: 100%;
  display: flex; align-items: center; min-width: 0;
}
.rail {
  position: absolute; left: 0; right: 0; top: 50%;
  height: 2px; background: #e6ebf3; transform: translateY(-1px);
  border-radius: 1px;
}
.rail-fill {
  position: absolute; top: 50%; height: 2px;
  background: linear-gradient(90deg, #bfd3f5, #7ba6e8);
  transform: translateY(-1px); border-radius: 1px;
  transition: width 0.3s, left 0.3s;
}

/* 打点 */
.cp {
  position: absolute; top: 50%; transform: translate(-50%, -50%);
  cursor: pointer; padding: 6px 4px;
  display: flex; flex-direction: column; align-items: center; gap: 2px;
}
.dot {
  width: 11px; height: 11px; border-radius: 50%;
  background: var(--panel); border: 2px solid var(--brand);
  transition: 0.15s; box-shadow: 0 0 0 2px var(--panel);
}
.cp.active .dot {
  background: var(--brand); border-color: var(--brand);
  box-shadow: 0 0 0 2px var(--panel), 0 0 0 4px rgba(37, 99, 235, 0.22);
}
.cp:hover .dot { transform: scale(1.18); border-color: var(--brand2); }
.idx {
  font-size: 8.5px; color: var(--dim2); font-family: Consolas, monospace;
  line-height: 1; opacity: 0.85;
}
.cp.active .idx { color: var(--brand2); font-weight: 600; }

/* 悬停详情 */
.tip {
  position: absolute; bottom: calc(100% + 6px); left: 50%;
  transform: translateX(-50%);
  background: var(--panel); border: 1px solid var(--line2);
  border-radius: 8px; padding: 8px 11px;
  box-shadow: 0 8px 28px rgba(15, 23, 42, 0.16);
  white-space: nowrap; z-index: 60; pointer-events: none;
}
.tip::after {
  content: ""; position: absolute; top: 100%; left: 50%; margin-left: -5px;
  border: 5px solid transparent; border-top-color: var(--line2);
}
.tip-name { font-size: 11.5px; font-weight: 600; color: var(--ink); margin-bottom: 2px; }
.tip-sum { font-size: 10.5px; color: var(--dim); font-family: Consolas, monospace; }
.tip-time { font-size: 10px; color: var(--dim2); font-family: Consolas, monospace; margin-top: 2px; }
.tip-hint {
  font-size: 9px; color: var(--dim2); margin-top: 5px;
  padding-top: 4px; border-top: 1px solid var(--line);
}

.empty-tip {
  font-size: 11px; color: var(--dim2); margin-left: 6px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

/* 右侧 */
.tl-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.cnt {
  font-size: 11px; color: var(--dim2); font-family: Consolas, monospace;
  background: var(--panel3); padding: 2px 7px; border-radius: 5px;
}
.clr {
  border: 1px solid var(--line); background: transparent;
  color: var(--dim2); font-size: 11px; padding: 3px 9px;
  border-radius: 6px; cursor: pointer; font-family: inherit;
}
.clr:hover { border-color: var(--bad); color: var(--bad); background: var(--bad-soft); }
</style>
