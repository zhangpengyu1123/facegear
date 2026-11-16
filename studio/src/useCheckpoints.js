/**
 * 打点（参数快照）管理
 * - snap()    记录当前全部参数
 * - restore() 跳回某次打点
 * - 支持重命名、删除、清空
 */
import { ref, computed } from "vue";

let seq = 0;

export function useCheckpoints(params) {
  const list = ref([]);
  const activeId = ref(null);

  /** 当前参数的一句话摘要，用作打点默认名 */
  function summary() {
    const p = params;
    return `m${(+p.m).toFixed(2)} z${p.z1}/${p.z2} T${Math.round(p.torque)}`;
  }

  /** 记录一次打点 */
  function snap(name) {
    seq += 1;
    const cp = {
      id: "cp" + seq,
      index: seq,
      name: name || `#${seq}`,
      time: Date.now(),
      summary: summary(),
      params: JSON.parse(JSON.stringify(params)),
    };
    list.value.push(cp);
    activeId.value = cp.id;
    return cp;
  }

  /** 跳回某次打点 */
  function restore(cp) {
    Object.assign(params, cp.params);
    activeId.value = cp.id;
  }

  function remove(id) {
    const i = list.value.findIndex((c) => c.id === id);
    if (i < 0) return;
    list.value.splice(i, 1);
    if (activeId.value === id) activeId.value = null;
  }

  function clear() {
    list.value = [];
    activeId.value = null;
  }

  function rename(id, name) {
    const cp = list.value.find((c) => c.id === id);
    if (cp) cp.name = name || cp.name;
  }

  const count = computed(() => list.value.length);
  const active = computed(() => list.value.find((c) => c.id === activeId.value) || null);

  return { list, count, active, activeId, snap, restore, remove, clear, rename };
}
