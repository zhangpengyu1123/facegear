/**
 * 函数库：所有可贴到函数画布上的观测量
 *
 * 分三类：
 *  - core  三个验收目标（承载 / 效率 / 紧凑）
 *  - proc  过程参数（应力、载荷、系数、几何、强度）
 *
 * 每个函数都能画：
 *  - 2D：f(x)   —— 单参数扫描
 *  - 3D：f(x,y) —— 双参数曲面 / 热力 / 等高线
 */

/** 可扫描的输入参数（X / Y 轴候选） */
export const SCAN_KEYS = [
  { k: "m", label: "模数 m", unit: "mm", span: (p) => [Math.max(0.6, p.m * 0.5), p.m * 1.8] },
  { k: "z1", label: "小齿轮齿数 z₁", unit: "", span: (p) => [Math.max(6, Math.round(p.z1 * 0.5)), Math.round(p.z1 * 1.8)] },
  { k: "z2", label: "面齿轮齿数 z₂", unit: "", span: (p) => [Math.max(12, Math.round(p.z2 * 0.5)), Math.round(p.z2 * 1.8)] },
  { k: "zs", label: "插齿刀齿数 z_s", unit: "", span: (p) => [Math.max(8, Math.round(p.zs * 0.6)), Math.round(p.zs * 1.6)] },
  { k: "alpha", label: "压力角 α", unit: "°", span: () => [15, 30] },
  { k: "b", label: "齿宽 b", unit: "mm", span: (p) => [Math.max(5, p.b * 0.4), p.b * 1.8] },
  { k: "r_in", label: "内半径", unit: "mm", span: (p) => [p.r_in * 0.6, p.r_in * 1.35] },
  { k: "r_out", label: "外半径", unit: "mm", span: (p) => [p.r_out * 0.7, p.r_out * 1.3] },
  { k: "torque", label: "扭矩 T", unit: "N·m", span: (p) => [p.torque * 0.2, p.torque * 2.5] },
  { k: "speed", label: "转速 n", unit: "rpm", span: (p) => [p.speed * 0.2, p.speed * 2.5] },
  { k: "k_hface", label: "K_Hface", unit: "", span: () => [1.0, 1.8] },
  { k: "life", label: "寿命", unit: "h", span: (p) => [Math.max(50, p.life * 0.1), p.life * 4] },
  { k: "s_h_lim", label: "σ_Hlim", unit: "MPa", span: (p) => [p.s_h_lim * 0.5, p.s_h_lim * 1.3] },
  { k: "s_f_lim", label: "σ_Flim", unit: "MPa", span: (p) => [p.s_f_lim * 0.5, p.s_f_lim * 1.3] },
];

/**
 * 全量函数集合
 * core: 三个验收目标
 * desc: 一句话说明（画在卡片副标题上）
 */
export const FUNCTIONS = [
  /* ============ 一级：三个验收目标 ============ */
  {
    id: "safety_margin", name: "承载裕度", unit: "", group: "验收目标", core: true,
    desc: "min(S_H/1.18, S_F/1.76)，≥1 为合格",
  },
  {
    id: "efficiency", name: "传动总效率 η", unit: "%", group: "验收目标", core: true,
    desc: "η = η_mesh × η_bearing × η_churn",
  },
  {
    id: "power_density", name: "功率密度 P/V", unit: "kW/L", group: "验收目标", core: true,
    desc: "功率 ÷ 估算体积，越大越紧凑",
  },
  { id: "volume_l", name: "估算体积 V", unit: "L", group: "验收目标", core: true, desc: "面齿轮盘 + 小齿轮" },
  { id: "eff_mesh", name: "啮合效率 η_mesh", unit: "%", group: "验收目标", desc: "仅齿轮副啮合部分" },

  /* ============ 应力 ============ */
  { id: "s_h", name: "接触应力 σ_H", unit: "MPa", group: "应力", desc: "ISO 6336-2 当量齿轮法" },
  { id: "s_f", name: "齿根弯曲 σ_F", unit: "MPa", group: "应力", desc: "ISO 6336-3 当量齿轮法" },
  { id: "s_h0", name: "名义接触 σ_H0", unit: "MPa", group: "应力", desc: "未乘载荷系数" },
  { id: "s_f0", name: "名义弯曲 σ_F0", unit: "MPa", group: "应力", desc: "未乘载荷系数" },
  { id: "s_h_allow", name: "许用接触应力", unit: "MPa", group: "应力", desc: "σ_Hlim × Z_NT" },
  { id: "s_f_allow", name: "许用弯曲应力", unit: "MPa", group: "应力", desc: "σ_Flim × 2 × Y_NT" },

  /* ============ 强度 ============ */
  { id: "safety_h", name: "接触安全系数 S_H", unit: "", group: "强度", desc: "要求 ≥ 1.18" },
  { id: "safety_f", name: "弯曲安全系数 S_F", unit: "", group: "强度", desc: "要求 ≥ 1.76" },

  /* ============ 载荷 ============ */
  { id: "torque", name: "输入扭矩 T", unit: "N·m", group: "载荷", desc: "设计输入" },
  { id: "power", name: "功率 P", unit: "kW", group: "载荷", desc: "T × n / 9550" },
  { id: "ft", name: "切向力 F_t", unit: "N", group: "载荷", desc: "2T / d₁" },
  { id: "fn", name: "法向力 F_n", unit: "N", group: "载荷", desc: "F_t / cosα" },
  { id: "vel", name: "节线速度 v", unit: "m/s", group: "载荷", desc: "πd₁n / 60000" },
  { id: "ka", name: "使用系数 K_A", unit: "", group: "载荷", desc: "工况冲击" },
  { id: "kv", name: "动载系数 K_V", unit: "", group: "载荷", desc: "速度 + 精度" },
  { id: "khb", name: "齿向系数 K_Hβ", unit: "", group: "载荷", desc: "齿宽 / d₁ 与精度" },
  { id: "kh", name: "综合 K_H", unit: "", group: "载荷", desc: "K_A·K_V·K_Hβ" },
  { id: "kf", name: "综合 K_F", unit: "", group: "载荷", desc: "K_A·K_V·K_Fβ" },

  /* ============ 系数 ============ */
  { id: "zh", name: "节点区域系数 Z_H", unit: "", group: "系数", desc: "仅与压力角有关" },
  { id: "ze", name: "弹性系数 Z_E", unit: "√MPa", group: "系数", desc: "材料弹性模量" },
  { id: "zeps", name: "重合度系数 Z_ε", unit: "", group: "系数", desc: "随 ε_α 增大而减小" },
  { id: "yf", name: "齿形系数 Y_F", unit: "", group: "系数", desc: "随当量齿数增大而减小" },
  { id: "ys", name: "应力修正系数 Y_S", unit: "", group: "系数", desc: "齿根圆角效应" },
  { id: "yeps", name: "重合度系数 Y_ε", unit: "", group: "系数", desc: "0.25 + 0.75/ε" },

  /* ============ 几何 ============ */
  { id: "d1", name: "小齿轮分度圆 d₁", unit: "mm", group: "几何", desc: "m × z₁" },
  { id: "db1", name: "小齿轮基圆 d_b1", unit: "mm", group: "几何", desc: "d₁ cosα" },
  { id: "da1", name: "小齿轮齿顶圆 d_a1", unit: "mm", group: "几何", desc: "" },
  { id: "df1", name: "小齿轮齿根圆 d_f1", unit: "mm", group: "几何", desc: "" },
  { id: "r_fp", name: "面齿轮分度圆 r_fp", unit: "mm", group: "几何", desc: "m × z₂ / 2" },
  { id: "u", name: "传动比 u", unit: "", group: "几何", desc: "z₂ / z₁" },
  { id: "eps", name: "端面重合度 ε_α", unit: "", group: "几何", desc: "何飞 2023 式(27)" },
  { id: "b", name: "齿宽 b", unit: "mm", group: "几何", desc: "r_out − r_in" },

  /* ============ 修正 ============ */
  { id: "k_hface", name: "面齿轮接触修正", unit: "", group: "修正", desc: "接触迹线沿齿宽集中" },
];

/** 按组聚合，便于函数库面板分组展示 */
export const FUNC_GROUPS = (() => {
  const order = ["验收目标", "应力", "强度", "载荷", "系数", "几何", "修正"];
  const m = new Map(order.map((g) => [g, []]));
  FUNCTIONS.forEach((f) => {
    if (!m.has(f.group)) m.set(f.group, []);
    m.get(f.group).push(f);
  });
  return [...m.entries()].filter(([, list]) => list.length);
})();

export const FUNC_MAP = Object.fromEntries(FUNCTIONS.map((f) => [f.id, f]));

/** 默认贴到画布上的三张核心卡（三个验收目标，一屏可见） */
export const DEFAULT_CARDS = [
  { id: "c1", fn: "safety_margin", x: "torque", y: "b", mode: "surface" },
  { id: "c2", fn: "efficiency", x: "z2", y: "b", mode: "line" },
  { id: "c3", fn: "power_density", x: "m", y: "b", mode: "line" },
];
