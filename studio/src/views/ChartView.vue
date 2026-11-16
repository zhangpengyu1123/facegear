<script setup>
import { ref, inject, computed } from "vue";
import FunctionCard from "./FunctionCard.vue";
import { FUNC_GROUPS, DEFAULT_CARDS } from "../functionLibrary";

const params = inject("params");

const cards = ref(DEFAULT_CARDS.map((c) => ({ ...c })));
const openLib = ref(false);
let seq = 100;

const addedIds = computed(() => new Set(cards.value.map((c) => c.fn)));

function addFunc(f) {
  cards.value.push({
    id: "c" + ++seq,
    fn: f.id,
    x: f.group === "验收目标" ? "torque" : "m",
    y: "b",
    mode: "line",
  });
  openLib.value = false;
}

function removeCard(id) {
  cards.value = cards.value.filter((c) => c.id !== id);
}

function resetCards() {
  cards.value = DEFAULT_CARDS.map((c) => ({ ...c }));
}
</script>

<template>
  <div class="board">
    <!-- 头部 -->
    <div class="bhead">
      <span class="btitle">函数画布</span>
      <span class="bcount">{{ cards.length }} 张</span>
      <div class="spacer"></div>
      <button class="btn sm" :class="{ on: openLib }" @click="openLib = !openLib">
        ＋ 贴函数
      </button>
      <button class="btn sm ghost" @click="resetCards" title="恢复默认四张">重置</button>
    </div>

    <!-- 函数库面板 -->
    <div v-if="openLib" class="lib">
      <div class="libhead">
        <span>函数库 · 点击贴到画布</span>
        <button class="btn sm ghost" @click="openLib = false">关闭</button>
      </div>
      <div class="libbody">
        <div v-for="[group, list] in FUNC_GROUPS" :key="group" class="lgroup">
          <div class="lgtitle">{{ group }}</div>
          <div class="lgrid">
            <button
              v-for="f in list" :key="f.id"
              class="fbtn" :class="{ core: f.core, added: addedIds.has(f.id) }"
              :title="f.desc"
              @click="addFunc(f)">
              <span class="fname">{{ f.name }}</span>
              <span class="funit" v-if="f.unit">{{ f.unit }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 卡片画布 -->
    <div class="cards">
      <FunctionCard
        v-for="c in cards" :key="c.id"
        :card="c" :params="params"
        @remove="removeCard"
      />
      <button v-if="!cards.length" class="empty" @click="openLib = true">
        ＋ 从函数库贴一张图
      </button>
    </div>
  </div>
</template>

<style scoped>
.board {
  display: flex; flex-direction: column;
  height: 100%; min-height: 0; position: relative;
  background: var(--bg2);
}

/* 头部 */
.bhead {
  flex-shrink: 0; display: flex; align-items: center; gap: 8px;
  padding: 6px 12px; border-bottom: 1px solid var(--line);
  background: var(--panel);
}
.btitle { font-size: 11.5px; font-weight: 600; color: var(--ink); letter-spacing: 0.02em; }
.bcount {
  font-size: 10px; color: var(--dim2); font-family: Consolas, monospace;
  background: var(--panel3); padding: 1px 6px; border-radius: 4px;
}
.spacer { flex: 1; }

/* 函数库 */
.lib {
  position: absolute; left: 8px; right: 8px; top: 34px;
  max-height: min(68%, 340px); z-index: 40;
  background: var(--panel); border: 1px solid var(--line2);
  border-radius: 10px; box-shadow: 0 14px 44px rgba(15, 23, 42, 0.18);
  display: flex; flex-direction: column; overflow: hidden;
}
.libhead {
  flex-shrink: 0; display: flex; justify-content: space-between; align-items: center;
  padding: 8px 12px; border-bottom: 1px solid var(--line);
  font-size: 11.5px; font-weight: 600; color: var(--ink);
  background: var(--panel2);
}
.libbody { padding: 10px 12px 14px; overflow-y: auto; }
.lgroup { margin-bottom: 11px; }
.lgroup:last-child { margin-bottom: 0; }
.lgtitle {
  font-size: 9.5px; color: var(--dim2); letter-spacing: 0.14em;
  font-weight: 600; text-transform: uppercase; margin-bottom: 6px;
}
.lgrid { display: grid; grid-template-columns: repeat(auto-fit, minmax(148px, 1fr)); gap: 5px; }

.fbtn {
  display: flex; align-items: baseline; justify-content: space-between; gap: 5px;
  background: var(--panel2); border: 1px solid var(--line);
  border-radius: 6px; padding: 5px 8px; cursor: pointer;
  font-family: inherit; text-align: left; transition: 0.13s;
}
.fbtn:hover { border-color: var(--brand); background: var(--brand-soft); }
.fbtn.core { border-color: #c7d9ff; background: #f6f9ff; }
.fbtn.core:hover { background: var(--brand-soft); border-color: var(--brand); }
.fbtn.added { opacity: 0.45; }
.fname { font-size: 11px; color: var(--ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.funit { font-size: 9px; color: var(--dim2); font-family: Consolas, monospace; flex-shrink: 0; }

/* 卡片网格 */
.cards {
  flex: 1; min-height: 0; overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  grid-auto-rows: minmax(232px, 1fr);
  gap: 7px; padding: 7px;
}
.empty {
  grid-column: 1 / -1; grid-row: 1;
  border: 1px dashed var(--line2); border-radius: 9px;
  background: transparent; color: var(--dim2); font-size: 12px;
  cursor: pointer; font-family: inherit;
}
.empty:hover { border-color: var(--brand); color: var(--brand); background: var(--brand-soft); }
</style>
