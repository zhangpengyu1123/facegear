/**
 * 全局数值格式化
 * 统一：千分位 + 固定小数位 + 数值与单位间不换行空格 + 等宽数字
 * 目标：同一个物理量在任何界面显示相同精度
 */

const NBSP = "\u00a0";

/** 按物理量 key 规定精度（小数位） */
const DECIMALS = {
  // 验收目标
  safety_margin: 3, efficiency: 2, eff_mesh: 2,
  volume_l: 2, power_density: 3,
  // 应力
  s_h: 1, s_h0: 1, s_f: 1, s_f0: 1, s_h_allow: 0, s_f_allow: 0,
  // 安全系数
  safety_h: 3, safety_f: 3, s_h_min: 2, s_f_min: 2,
  // 载荷
  torque: 0, power: 1, ft: 0, fn: 0, vel: 2,
  // 系数
  ka: 2, kv: 3, khb: 3, kh: 3, kf: 3,
  zh: 3, ze: 3, zeps: 3, yf: 3, ys: 3, yeps: 3,
  k_hface: 2,
  // 几何
  d1: 2, db1: 2, da1: 2, df1: 2, r_fp: 2,
  b: 1, r_in: 1, r_out: 1, m: 2, alpha: 1, gamma: 1,
  ha_star: 2, c_star: 2, beta: 1,
  // 无量纲
  u: 3, eps: 3,
  // 工况
  speed: 0, life: 0, quality: 0,
  // 材料
  s_h_lim: 0, s_f_lim: 0, e_mod: 0, nu: 3,
  // 齿数
  z1: 0, z2: 0, zs: 0,
};

/**
 * @param {number} v 数值
 * @param {string} [key] 物理量 key（用于查表精度）；给数字则直接当小数位
 * @param {string} [unit] 单位（可省）
 */
export function fmt(v, key, unit) {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  let dec;
  if (typeof key === "number") dec = key;
  else dec = DECIMALS[key] ?? 2;

  const s = v.toLocaleString("en-US", {
    minimumFractionDigits: dec,
    maximumFractionDigits: dec,
  });
  return unit ? s + NBSP + unit : s;
}

/** 纯数字（不带单位），用于表格右列 */
export function num(v, key) {
  return fmt(v, key);
}

/** 参数滑块的显示值：短格式，例如 6.35 mm */
export function fmtParam(v, dec, unit) {
  const s = Number(v).toFixed(dec);
  return unit ? s + NBSP + unit : s;
}

/** 利用率 -> 语义色（<70% 绿 / 70~90% 琥珀 / >90% 红） */
export function utilColor(ratio) {
  if (ratio > 0.9) return { fg: "#dc2626", bar: "linear-gradient(90deg,#f59e0b,#dc2626)", label: "超限" };
  if (ratio > 0.7) return { fg: "#b45309", bar: "linear-gradient(90deg,#10b981,#f59e0b)", label: "偏高" };
  return { fg: "#059669", bar: "linear-gradient(90deg,#10b981,#0891b2)", label: "正常" };
}
