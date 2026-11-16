/**
 * 共享求解层：三个区域（参数 / KPI / 图表 / 模型）消费同一份结果
 */
import { ref, watch, onMounted, onBeforeUnmount } from "vue";
import { solve } from "./api";

export function useSolve(params) {
  const result = ref(null);
  const busy = ref(false);
  const err = ref("");
  let timer = null;

  async function run() {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      busy.value = true;
      err.value = "";
      try {
        result.value = await solve({ ...params });
      } catch (e) {
        err.value = String(e);
      } finally {
        busy.value = false;
      }
    }, 80);
  }

  watch(params, run, { deep: true });
  onMounted(run);
  onBeforeUnmount(() => clearTimeout(timer));

  return { result, busy, err, refresh: run };
}

/** 把结果数组转成 key -> var 的字典 */
export function indexVars(result) {
  const m = {};
  (result?.vars || []).forEach((v) => (m[v.key] = v));
  return m;
}
