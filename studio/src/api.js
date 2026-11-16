/**
 * 后端桥接层
 * - 在 Tauri 中：调用 Rust 命令
 * - 在纯浏览器中（vite dev 直接预览）：用等价的 JS 实现降级
 *   两套实现共用同一组公式，数值一致；JS 仅用于浏览器预览验证 UI。
 */

const HAS_TAURI = typeof window !== "undefined" && !!window.__TAURI__;
const invoke = HAS_TAURI ? window.__TAURI__.core.invoke : null;

/* ================= JS 降级实现（与 Rust core.rs 对齐） ================= */
const TAU = Math.PI * 2;

function lifeFactor(nl) {
  const limit = 3e6;
  if (nl >= limit) return 1.0;
  if (nl <= 0) return 1.6;
  return Math.min(Math.pow(limit / nl, 1 / 6), 1.6);
}

function computeCore(p) {
  const al = (p.alpha * Math.PI) / 180;
  const sinA = Math.sin(al), cosA = Math.cos(al);

  const d1 = p.m * p.z1;
  const db1 = d1 * cosA;
  const da1 = p.m * (p.z1 + 2 * p.ha_star);
  const df1 = p.m * (p.z1 - 2 * p.ha_star - 2 * p.c_star);
  const r_fp = (p.m * p.z2) / 2;
  const u = p.z2 / p.z1;
  const b = p.b > 0 ? p.b : p.r_out - p.r_in;

  const ra1 = da1 / 2, rb1 = db1 / 2;
  const tha = Math.sqrt(Math.max(ra1 * ra1 - rb1 * rb1, 0)) / rb1;
  const numer = tha * p.z1 * sinA * cosA - (p.z1 - 2 - p.z1 * cosA * cosA);
  const denom = 2 * Math.PI * sinA * cosA;
  let eps = numer / denom;
  if (!isFinite(eps) || eps <= 0) eps = 1.2;

  const tNmm = p.torque * 1000;
  const ft = (2 * tNmm) / d1;
  const fn = ft / cosA;
  const vel = (Math.PI * d1 * 1e-3 * p.speed) / 60;
  const power = (p.torque * p.speed) / 9550;

  const ka = 1.0;
  const speedTerm = 1 + Math.pow(vel / 25, 1.6);
  const gradeTerm = 1 + 0.03 * (p.quality - 7);
  const kv = Math.min(Math.max(speedTerm * gradeTerm, 1), 1.8);
  const ratio = b / d1;
  const khb = Math.min(Math.max(1 + 0.35 * Math.max(0, ratio - 0.5) + 0.02 * (p.quality - 7), 1), 1.6);
  const kfb = Math.pow(khb, 0.85);
  const kh = ka * kv * khb;
  const kf = ka * kv * kfb;

  const zh = Math.sqrt(2 / (cosA * sinA));
  const ze = Math.sqrt(1 / (Math.PI * 2 * (1 - p.nu * p.nu) / p.e_mod));
  const zeps = eps <= 2 ? Math.sqrt(Math.max(4 - eps, 0.05) / 3) : 1 / Math.sqrt(eps);

  const yf0 = 1.646 + 9.41 / Math.max(p.z2, 6);
  const ys0 = 1.682 + 3.82 / Math.max(p.z2, 6);
  const dA = (p.alpha - 20) / 10;
  const yf = yf0 * (1 - 0.15 * dA);
  const ys = ys0;
  const yeps = 0.25 + 0.75 / eps;

  const sH0 = zh * ze * zeps * Math.sqrt((ft / (b * d1)) * ((u + 1) / u));
  const sH = sH0 * Math.sqrt(kh) * p.k_hface;
  const sF0 = (ft / (b * p.m)) * yf * ys * yeps;
  const sF = sF0 * kf;

  const nL = p.speed * 60 * p.life;
  const znt = lifeFactor(nL);
  const sHallow = p.s_h_lim * znt;
  const sFallow = p.s_f_lim * 2 * znt;

  return {
    d1, db1, da1, df1, r_fp, u, eps, b,
    ft, fn, vel, ka, kv, khb, kfb, kh, kf,
    zh, ze, zeps, yf, ys, yeps,
    sH0, sH, sF0, sF,
    sHallow, sFallow,
    safetyH: sHallow / sH, safetyF: sFallow / sF,
    sHmin: 1.18, sFmin: 1.76, power,
  };
}

const SUBJECTS = {
  OrthogonalSpur: "正交直齿面齿轮",
  Helical: "斜齿面齿轮",
  NonOrthogonal: "非正交面齿轮",
  Offset: "偏置面齿轮",
  ArcTooth: "弧线齿面齿轮",
  EndCurved: "端曲面齿轮",
  Modified: "修形面齿轮",
};

function mkVar(key, label, value, unit, group) {
  return { key, label, value, unit, group };
}

function localSolve(p) {
  const c = computeCore(p);
  const warnings = [];
  const implemented = p.subject === "OrthogonalSpur";
  if (!implemented) {
    warnings.push(`课题「${SUBJECTS[p.subject] || p.subject}」的计算链尚未实现，数值按正交直齿模型给出。`);
  }
  if (p.r_in > 0 && p.r_in < 0.6 * c.r_fp) {
    warnings.push(`内半径 ${p.r_in.toFixed(1)} mm 偏小（分度圆 ${c.r_fp.toFixed(1)} mm 的 ${((100 * p.r_in) / c.r_fp).toFixed(0)}%），内端可能根切。`);
  }
  const ok = c.safetyH >= c.sHmin && c.safetyF >= c.sFmin;
  const verdict_text = ok
    ? `合格　S_H=${c.safetyH.toFixed(2)} ≥ ${c.sHmin}　S_F=${c.safetyF.toFixed(2)} ≥ ${c.sFmin}`
    : `不合格　S_H=${c.safetyH.toFixed(2)}/${c.sHmin}　S_F=${c.safetyF.toFixed(2)}/${c.sFmin}`;

  const vars = [
    mkVar("d1", "小齿轮分度圆 d₁", c.d1, "mm", "几何"),
    mkVar("db1", "小齿轮基圆 d_b1", c.db1, "mm", "几何"),
    mkVar("da1", "小齿轮齿顶圆 d_a1", c.da1, "mm", "几何"),
    mkVar("df1", "小齿轮齿根圆 d_f1", c.df1, "mm", "几何"),
    mkVar("r_fp", "面齿轮分度圆 r_fp", c.r_fp, "mm", "几何"),
    mkVar("u", "传动比 u", c.u, "", "几何"),
    mkVar("eps", "端面重合度 ε_α", c.eps, "", "几何"),
    mkVar("b", "齿宽 b", c.b, "mm", "几何"),
    mkVar("torque", "输入扭矩 T", p.torque, "N·m", "载荷"),
    mkVar("power", "功率 P", c.power, "kW", "载荷"),
    mkVar("ft", "切向力 F_t", c.ft, "N", "载荷"),
    mkVar("fn", "法向力 F_n", c.fn, "N", "载荷"),
    mkVar("vel", "节线速度 v", c.vel, "m/s", "载荷"),
    mkVar("ka", "使用系数 K_A", c.ka, "", "载荷"),
    mkVar("kv", "动载系数 K_V", c.kv, "", "载荷"),
    mkVar("khb", "齿向系数 K_Hβ", c.khb, "", "载荷"),
    mkVar("kh", "综合 K_H", c.kh, "", "载荷"),
    mkVar("kf", "综合 K_F", c.kf, "", "载荷"),
    mkVar("zh", "节点区域系数 Z_H", c.zh, "", "系数"),
    mkVar("ze", "弹性系数 Z_E", c.ze, "√MPa", "系数"),
    mkVar("zeps", "重合度系数 Z_ε", c.zeps, "", "系数"),
    mkVar("yf", "齿形系数 Y_F", c.yf, "", "系数"),
    mkVar("ys", "应力修正系数 Y_S", c.ys, "", "系数"),
    mkVar("yeps", "重合度系数 Y_ε", c.yeps, "", "系数"),
    mkVar("s_h0", "名义接触应力 σ_H0", c.sH0, "MPa", "应力"),
    mkVar("s_h", "接触应力 σ_H", c.sH, "MPa", "应力"),
    mkVar("s_f0", "名义弯曲应力 σ_F0", c.sF0, "MPa", "应力"),
    mkVar("s_f", "弯曲应力 σ_F", c.sF, "MPa", "应力"),
    mkVar("s_h_allow", "许用接触应力", c.sHallow, "MPa", "强度"),
    mkVar("s_f_allow", "许用弯曲应力", c.sFallow, "MPa", "强度"),
    mkVar("safety_h", "接触安全系数 S_H", c.safetyH, "", "强度"),
    mkVar("safety_f", "弯曲安全系数 S_F", c.safetyF, "", "强度"),
    mkVar("k_hface", "面齿轮接触修正 K_Hface", p.k_hface, "", "修正"),
  ];

  return {
    subject_label: SUBJECTS[p.subject] || p.subject,
    implemented,
    vars,
    verdict_ok: ok,
    verdict_text,
    warnings,
  };
}

function applyParam(p, key, val) {
  const q = { ...p };
  const numeric = ["m","z1","z2","zs","alpha","gamma","ha_star","c_star","b","r_in","r_out","torque","speed","life","k_hface","quality","beta"];
  if (numeric.includes(key)) q[key] = val;
  return q;
}

function readOut(p, key) {
  const c = computeCore(p);
  const map = {
    s_h: [c.sH, "接触应力 σ_H", "MPa"],
    s_f: [c.sF, "弯曲应力 σ_F", "MPa"],
    safety_h: [c.safetyH, "接触安全系数 S_H", ""],
    safety_f: [c.safetyF, "弯曲安全系数 S_F", ""],
    eps: [c.eps, "端面重合度 ε_α", ""],
    u: [c.u, "传动比 u", ""],
    ft: [c.ft, "切向力 F_t", "N"],
    vel: [c.vel, "节线速度 v", "m/s"],
    kv: [c.kv, "动载系数 K_V", ""],
    kh: [c.kh, "综合 K_H", ""],
    yf: [c.yf, "齿形系数 Y_F", ""],
    zh: [c.zh, "节点区域系数 Z_H", ""],
    ze: [c.ze, "弹性系数 Z_E", "√MPa"],
    power: [c.power, "功率 P", "kW"],
    d1: [c.d1, "小齿轮分度圆 d₁", "mm"],
    s_h0: [c.sH0, "名义接触应力 σ_H0", "MPa"],
    s_f0: [c.sF0, "名义弯曲应力 σ_F0", "MPa"],
  };
  return map[key] || map.s_h;
}

function paramMeta(key) {
  const m = {
    m: ["模数 m", "mm"], z1: ["小齿轮齿数 z₁", ""], z2: ["面齿轮齿数 z₂", ""],
    zs: ["插齿刀齿数 z_s", ""], alpha: ["压力角 α", "°"], gamma: ["轴交角 γ", "°"],
    b: ["齿宽 b", "mm"], r_in: ["内半径", "mm"], r_out: ["外半径", "mm"],
    torque: ["扭矩 T", "N·m"], speed: ["转速 n", "rpm"], life: ["寿命", "h"],
    k_hface: ["接触修正 K_Hface", ""], quality: ["精度等级", ""], beta: ["螺旋角 β", "°"],
  };
  return m[key] || [key, ""];
}

function localSweep(req) {
  const steps = Math.min(Math.max(req.steps, 2), 400);
  const xs = [], ys = [];
  for (let i = 0; i < steps; i++) {
    const t = i / (steps - 1);
    const x = req.from + (req.to - req.from) * t;
    const p = applyParam(req.params, req.key, x);
    const [y] = readOut(p, req.out_key);
    xs.push(x); ys.push(y);
  }
  const [xl, xu] = paramMeta(req.key);
  const [, yl, yu] = readOut(req.params, req.out_key);
  return { xs, ys, x_label: xl, y_label: yl, x_unit: xu, y_unit: yu, out_unit: yu };
}

function localSweep2d(req) {
  const n = Math.min(Math.max(req.steps, 3), 120);
  const x = [], y = [];
  for (let i = 0; i < n; i++) {
    const t = i / (n - 1);
    x.push(req.from_x + (req.to_x - req.from_x) * t);
    y.push(req.from_y + (req.to_y - req.from_y) * t);
  }
  const z = [];
  for (let j = 0; j < n; j++) {
    const row = [];
    for (let i = 0; i < n; i++) {
      let p = applyParam(req.params, req.key_x, x[i]);
      p = applyParam(p, req.key_y, y[j]);
      const [val] = readOut(p, req.out_key);
      row.push(val);
    }
    z.push(row);
  }
  const [xl] = paramMeta(req.key_x);
  const [yl] = paramMeta(req.key_y);
  const [, zl, zu] = readOut(req.params, req.out_key);
  return { x, y, z, x_label: xl, y_label: yl, z_label: zl, z_unit: zu };
}

/* ================= 对外 API ================= */
export async function solve(params) {
  if (invoke) return invoke("solve_cmd", { p: params });
  return localSolve(params);
}

export async function sweep(req) {
  if (invoke) return invoke("sweep_cmd", { req });
  return localSweep(req);
}

export async function sweep2d(req) {
  if (invoke) return invoke("sweep2d_cmd", { req });
  return localSweep2d(req);
}

export const isTauri = HAS_TAURI;
export { SUBJECTS };
