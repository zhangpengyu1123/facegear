//! 面齿轮计算内核（移植自 Python 版 facegear，数值一致）
//!
//! 提供三个入口：
//! * [`solve`]    单点求解
//! * [`sweep`]    一维参数扫描（给折线/散点/柱状图）
//! * [`sweep2d`]  二维参数扫描（给热力图/等高线/3D 曲面）

use serde::{Deserialize, Serialize};

// ======================================================================
// 课题枚举
// ======================================================================
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Subject {
    /// 正交直齿（已实现完整计算）
    OrthogonalSpur,
    /// 斜齿
    Helical,
    /// 非正交
    NonOrthogonal,
    /// 偏置
    Offset,
    /// 弧线齿
    ArcTooth,
    /// 端曲面
    EndCurved,
    /// 修形
    Modified,
}

impl Subject {
    pub fn label(&self) -> &'static str {
        match self {
            Subject::OrthogonalSpur => "正交直齿面齿轮",
            Subject::Helical => "斜齿面齿轮",
            Subject::NonOrthogonal => "非正交面齿轮",
            Subject::Offset => "偏置面齿轮",
            Subject::ArcTooth => "弧线齿面齿轮",
            Subject::EndCurved => "端曲面齿轮",
            Subject::Modified => "修形面齿轮",
        }
    }
    /// 是否已实现完整计算
    pub fn implemented(&self) -> bool {
        matches!(self, Subject::OrthogonalSpur)
    }
}

// ======================================================================
// 输入
// ======================================================================
#[derive(Debug, Clone, Deserialize)]
pub struct Params {
    pub subject: Subject,

    // 几何
    pub m: f64,        // 模数 mm
    pub z1: f64,       // 小齿轮齿数
    pub z2: f64,       // 面齿轮齿数
    pub zs: f64,       // 插齿刀齿数
    pub alpha: f64,    // 压力角 (°)
    pub gamma: f64,    // 轴交角 (°)
    pub ha_star: f64,  // 齿顶高系数
    pub c_star: f64,   // 顶隙系数
    pub b: f64,        // 齿宽 mm
    pub r_in: f64,     // 内半径 mm
    pub r_out: f64,    // 外半径 mm

    // 工况
    pub torque: f64,   // N·m
    pub speed: f64,    // rpm
    pub life: f64,     // h

    // 材料
    pub s_h_lim: f64,  // 接触疲劳极限 MPa
    pub s_f_lim: f64,  // 弯曲疲劳极限 MPa
    pub e_mod: f64,    // 弹性模量 MPa
    pub nu: f64,       // 泊松比

    // 修正
    pub k_hface: f64,  // 面齿轮接触修正
    pub quality: f64,  // 精度等级
    pub beta: f64,     // 螺旋角 (°)（斜齿用）
}

impl Default for Params {
    fn default() -> Self {
        Self {
            subject: Subject::OrthogonalSpur,
            m: 6.35, z1: 25.0, z2: 160.0, zs: 27.0,
            alpha: 25.0, gamma: 90.0, ha_star: 1.0, c_star: 0.25,
            b: 80.0, r_in: 480.0, r_out: 560.0,
            torque: 1600.0, speed: 1000.0, life: 5000.0,
            s_h_lim: 1500.0, s_f_lim: 480.0, e_mod: 210000.0, nu: 0.3,
            k_hface: 1.45, quality: 7.0, beta: 0.0,
        }
    }
}

// ======================================================================
// 输出
// ======================================================================
#[derive(Debug, Clone, Serialize)]
pub struct Var {
    pub key: String,
    pub label: String,
    pub value: f64,
    pub unit: String,
    pub group: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct SolveOut {
    pub subject_label: String,
    pub implemented: bool,
    pub vars: Vec<Var>,
    pub verdict_ok: bool,
    pub verdict_text: String,
    pub warnings: Vec<String>,
}

fn v(key: &str, label: &str, value: f64, unit: &str, group: &str) -> Var {
    Var { key: key.into(), label: label.into(), value, unit: unit.into(), group: group.into() }
}

// ======================================================================
// 核心计算
// ======================================================================
#[derive(Debug, Clone, Serialize)]
pub struct Core {
    // 几何
    pub d1: f64,
    pub db1: f64,
    pub da1: f64,
    pub df1: f64,
    pub r_fp: f64,
    pub u: f64,
    pub eps: f64,
    pub b: f64,
    // 载荷
    pub ft: f64,
    pub fn_: f64,
    pub vel: f64,
    pub ka: f64,
    pub kv: f64,
    pub khb: f64,
    pub kfb: f64,
    pub kh: f64,
    pub kf: f64,
    // 系数
    pub zh: f64,
    pub ze: f64,
    pub zeps: f64,
    pub yf: f64,
    pub ys: f64,
    pub yeps: f64,
    // 应力
    pub s_h0: f64,
    pub s_h: f64,
    pub s_f0: f64,
    pub s_f: f64,
    // 许用与安全
    pub s_h_allow: f64,
    pub s_f_allow: f64,
    pub safety_h: f64,
    pub safety_f: f64,
    pub s_h_min: f64,
    pub s_f_min: f64,
    // 功率
    pub power_kw: f64,
}

pub fn compute_core(p: &Params) -> Core {
    let al = p.alpha.to_radians();
    let (sin_a, cos_a) = (al.sin(), al.cos());

    // ---- 几何 ----
    let d1 = p.m * p.z1;
    let db1 = d1 * cos_a;
    let da1 = p.m * (p.z1 + 2.0 * p.ha_star);
    let df1 = p.m * (p.z1 - 2.0 * p.ha_star - 2.0 * p.c_star);
    let r_fp = p.m * p.z2 / 2.0;
    let u = p.z2 / p.z1;
    let b = if p.b > 0.0 { p.b } else { p.r_out - p.r_in };

    // 端面重合度（何飞 2023 式27）
    let ra1 = da1 / 2.0;
    let rb1 = db1 / 2.0;
    let theta_a1 = ((ra1 * ra1 - rb1 * rb1).max(0.0)).sqrt() / rb1;
    let numer = theta_a1 * p.z1 * sin_a * cos_a - (p.z1 - 2.0 - p.z1 * cos_a * cos_a);
    let denom = 2.0 * std::f64::consts::PI * sin_a * cos_a;
    let mut eps = numer / denom;
    if !eps.is_finite() || eps <= 0.0 {
        eps = 1.2;
    }

    // ---- 载荷 ----
    let t_nmm = p.torque * 1000.0;
    let ft = 2.0 * t_nmm / d1;
    let fn_ = ft / cos_a;
    let vel = std::f64::consts::PI * d1 * 1e-3 * p.speed / 60.0;
    let power_kw = p.torque * p.speed / 9550.0;

    // 载荷系数（ISO 6336-1 工程简化）
    let ka = 1.0;
    let speed_term = 1.0 + (vel / 25.0).powf(1.6);
    let grade_term = 1.0 + 0.03 * (p.quality - 7.0);
    let kv = (speed_term * grade_term).clamp(1.0, 1.8);
    let ratio = b / d1;
    let khb = (1.0 + 0.35 * (ratio - 0.5).max(0.0) + 0.02 * (p.quality - 7.0)).clamp(1.0, 1.6);
    let kfb = khb.powf(0.85);
    let kh = ka * kv * khb;
    let kf = ka * kv * kfb;

    // ---- 系数 ----
    let zh = (2.0 / (cos_a * sin_a)).sqrt();
    let ze = (1.0 / (std::f64::consts::PI * 2.0 * (1.0 - p.nu * p.nu) / p.e_mod)).sqrt();
    let zeps = if eps <= 2.0 {
        ((4.0 - eps) / 3.0).max(0.05).sqrt()
    } else {
        1.0 / eps.sqrt()
    };

    // YF / YS 工程近似
    let yf0 = 1.646 + 9.41 / p.z2.max(6.0);
    let ys0 = 1.682 + 3.82 / p.z2.max(6.0);
    let d_alpha = (p.alpha - 20.0) / 10.0;
    let yf = yf0 * (1.0 - 0.15 * d_alpha);
    let ys = ys0;
    let yeps = 0.25 + 0.75 / eps;

    // ---- 应力 ----
    let s_h0 = zh * ze * zeps * ((ft / (b * d1)) * ((u + 1.0) / u)).sqrt();
    let s_h = s_h0 * kh.sqrt() * p.k_hface;
    let s_f0 = (ft / (b * p.m)) * yf * ys * yeps;
    let s_f = s_f0 * kf;

    // ---- 许用 ----
    let n_l = p.speed * 60.0 * p.life;
    let z_nt = life_factor(n_l);
    let y_nt = life_factor(n_l);
    let s_h_allow = p.s_h_lim * z_nt;
    let s_f_allow = p.s_f_lim * 2.0 * y_nt;

    let s_h_safety = s_h_allow / s_h;
    let s_f_safety = s_f_allow / s_f;
    let s_h_min = 1.18;
    let s_f_min = 1.76;

    Core {
        d1, db1, da1, df1, r_fp, u, eps, b,
        ft, fn_, vel, ka, kv, khb, kfb, kh, kf,
        zh, ze, zeps, yf, ys, yeps,
        s_h0, s_h, s_f0, s_f,
        s_h_allow, s_f_allow,
        safety_h: s_h_safety, safety_f: s_f_safety,
        s_h_min, s_f_min, power_kw,
    }
}

fn life_factor(n_l: f64) -> f64 {
    let limit = 3e6;
    if n_l >= limit {
        1.0
    } else if n_l <= 0.0 {
        1.6
    } else {
        ((limit / n_l).powf(1.0 / 6.0)).min(1.6)
    }
}

// ======================================================================
// solve
// ======================================================================
pub fn solve(p: &Params) -> SolveOut {
    let c = compute_core(p);
    let mut warnings = Vec::new();

    if !p.subject.implemented() {
        warnings.push(format!(
            "课题「{}」的计算链尚未实现，下方数值按正交直齿模型给出，仅供参考。",
            p.subject.label()
        ));
    }
    if p.r_in > 0.0 && p.r_in < 0.6 * c.r_fp {
        warnings.push(format!(
            "内半径 {:.1} mm 偏小（分度圆半径 {:.1} mm 的 {:.0}%），内端可能根切。",
            p.r_in, c.r_fp, 100.0 * p.r_in / c.r_fp
        ));
    }

    let ok = c.safety_h >= c.s_h_min && c.safety_f >= c.s_f_min;
    let verdict_text = if ok {
        format!("合格　S_H={:.2} ≥ {:.2}　S_F={:.2} ≥ {:.2}", c.safety_h, c.s_h_min, c.safety_f, c.s_f_min)
    } else {
        format!("不合格　S_H={:.2}/{:.2}　S_F={:.2}/{:.2}", c.safety_h, c.s_h_min, c.safety_f, c.s_f_min)
    };

    let vars = vec![
        // 几何
        v("d1", "小齿轮分度圆 d₁", c.d1, "mm", "几何"),
        v("db1", "小齿轮基圆 d_b1", c.db1, "mm", "几何"),
        v("da1", "小齿轮齿顶圆 d_a1", c.da1, "mm", "几何"),
        v("df1", "小齿轮齿根圆 d_f1", c.df1, "mm", "几何"),
        v("r_fp", "面齿轮分度圆 r_fp", c.r_fp, "mm", "几何"),
        v("u", "传动比 u", c.u, "", "几何"),
        v("eps", "端面重合度 ε_α", c.eps, "", "几何"),
        v("b", "齿宽 b", c.b, "mm", "几何"),
        // 载荷
        v("torque", "输入扭矩 T", p.torque, "N·m", "载荷"),
        v("power", "功率 P", c.power_kw, "kW", "载荷"),
        v("ft", "切向力 F_t", c.ft, "N", "载荷"),
        v("fn", "法向力 F_n", c.fn_, "N", "载荷"),
        v("vel", "节线速度 v", c.vel, "m/s", "载荷"),
        v("ka", "使用系数 K_A", c.ka, "", "载荷"),
        v("kv", "动载系数 K_V", c.kv, "", "载荷"),
        v("khb", "齿向系数 K_Hβ", c.khb, "", "载荷"),
        v("kh", "综合 K_H", c.kh, "", "载荷"),
        v("kf", "综合 K_F", c.kf, "", "载荷"),
        // 系数
        v("zh", "节点区域系数 Z_H", c.zh, "", "系数"),
        v("ze", "弹性系数 Z_E", c.ze, "√MPa", "系数"),
        v("zeps", "重合度系数 Z_ε", c.zeps, "", "系数"),
        v("yf", "齿形系数 Y_F", c.yf, "", "系数"),
        v("ys", "应力修正系数 Y_S", c.ys, "", "系数"),
        v("yeps", "重合度系数 Y_ε", c.yeps, "", "系数"),
        // 应力
        v("s_h0", "名义接触应力 σ_H0", c.s_h0, "MPa", "应力"),
        v("s_h", "接触应力 σ_H", c.s_h, "MPa", "应力"),
        v("s_f0", "名义弯曲应力 σ_F0", c.s_f0, "MPa", "应力"),
        v("s_f", "弯曲应力 σ_F", c.s_f, "MPa", "应力"),
        v("s_h_allow", "许用接触应力", c.s_h_allow, "MPa", "强度"),
        v("s_f_allow", "许用弯曲应力", c.s_f_allow, "MPa", "强度"),
        v("safety_h", "接触安全系数 S_H", c.safety_h, "", "强度"),
        v("safety_f", "弯曲安全系数 S_F", c.safety_f, "", "强度"),
        v("k_hface", "面齿轮接触修正 K_Hface", p.k_hface, "", "修正"),
    ];

    SolveOut {
        subject_label: p.subject.label().to_string(),
        implemented: p.subject.implemented(),
        vars,
        verdict_ok: ok,
        verdict_text,
        warnings,
    }
}

// ======================================================================
// sweep / sweep2d
// ======================================================================
#[derive(Debug, Clone, Deserialize)]
pub struct SweepReq {
    pub params: Params,
    pub key: String,          // 扫描哪个输入参数
    pub from: f64,
    pub to: f64,
    pub steps: usize,
    pub out_key: String,      // 看哪个输出变量
}

#[derive(Debug, Clone, Serialize)]
pub struct SweepOut {
    pub xs: Vec<f64>,
    pub ys: Vec<f64>,
    pub x_label: String,
    pub y_label: String,
    pub x_unit: String,
    pub y_unit: String,
    pub out_unit: String,
}

fn apply_param(p: &mut Params, key: &str, val: f64) {
    match key {
        "m" => p.m = val,
        "z1" => p.z1 = val,
        "z2" => p.z2 = val,
        "zs" => p.zs = val,
        "alpha" => p.alpha = val,
        "gamma" => p.gamma = val,
        "ha_star" => p.ha_star = val,
        "c_star" => p.c_star = val,
        "b" => p.b = val,
        "r_in" => p.r_in = val,
        "r_out" => p.r_out = val,
        "torque" => p.torque = val,
        "speed" => p.speed = val,
        "life" => p.life = val,
        "k_hface" => p.k_hface = val,
        "quality" => p.quality = val,
        "beta" => p.beta = val,
        _ => {}
    }
}

fn read_out(p: &Params, key: &str) -> (f64, String, String) {
    let c = compute_core(p);
    let (val, label, unit) = match key {
        "s_h" => (c.s_h, "接触应力 σ_H", "MPa"),
        "s_f" => (c.s_f, "弯曲应力 σ_F", "MPa"),
        "safety_h" => (c.safety_h, "接触安全系数 S_H", ""),
        "safety_f" => (c.safety_f, "弯曲安全系数 S_F", ""),
        "eps" => (c.eps, "端面重合度 ε_α", ""),
        "u" => (c.u, "传动比 u", ""),
        "ft" => (c.ft, "切向力 F_t", "N"),
        "vel" => (c.vel, "节线速度 v", "m/s"),
        "kv" => (c.kv, "动载系数 K_V", ""),
        "kh" => (c.kh, "综合 K_H", ""),
        "yf" => (c.yf, "齿形系数 Y_F", ""),
        "zh" => (c.zh, "节点区域系数 Z_H", ""),
        "ze" => (c.ze, "弹性系数 Z_E", "√MPa"),
        "power" => (c.power_kw, "功率 P", "kW"),
        "d1" => (c.d1, "小齿轮分度圆 d₁", "mm"),
        "s_h0" => (c.s_h0, "名义接触应力 σ_H0", "MPa"),
        "s_f0" => (c.s_f0, "名义弯曲应力 σ_F0", "MPa"),
        _ => (c.s_h, "接触应力 σ_H", "MPa"),
    };
    (val, label.to_string(), unit.to_string())
}

fn param_meta(key: &str) -> (String, String) {
    let (l, u) = match key {
        "m" => ("模数 m", "mm"),
        "z1" => ("小齿轮齿数 z₁", ""),
        "z2" => ("面齿轮齿数 z₂", ""),
        "zs" => ("插齿刀齿数 z_s", ""),
        "alpha" => ("压力角 α", "°"),
        "gamma" => ("轴交角 γ", "°"),
        "b" => ("齿宽 b", "mm"),
        "r_in" => ("内半径", "mm"),
        "r_out" => ("外半径", "mm"),
        "torque" => ("扭矩 T", "N·m"),
        "speed" => ("转速 n", "rpm"),
        "life" => ("寿命", "h"),
        "k_hface" => ("接触修正 K_Hface", ""),
        "quality" => ("精度等级", ""),
        "beta" => ("螺旋角 β", "°"),
        _ => (key, ""),
    };
    (l.to_string(), u.to_string())
}

pub fn sweep(req: &SweepReq) -> SweepOut {
    let steps = req.steps.clamp(2, 400);
    let mut xs = Vec::with_capacity(steps);
    let mut ys = Vec::with_capacity(steps);
    for i in 0..steps {
        let t = i as f64 / (steps - 1) as f64;
        let x = req.from + (req.to - req.from) * t;
        let mut p = req.params.clone();
        apply_param(&mut p, &req.key, x);
        let (y, _, _) = read_out(&p, &req.out_key);
        xs.push(x);
        ys.push(y);
    }
    let (xl, xu) = param_meta(&req.key);
    let (_, yl, yu) = read_out(&req.params, &req.out_key);
    SweepOut {
        xs, ys, x_label: xl, y_label: yl, x_unit: xu, y_unit: yu.clone(), out_unit: yu,
    }
}

#[derive(Debug, Clone, Deserialize)]
pub struct Sweep2dReq {
    pub params: Params,
    pub key_x: String,
    pub from_x: f64,
    pub to_x: f64,
    pub key_y: String,
    pub from_y: f64,
    pub to_y: f64,
    pub steps: usize,
    pub out_key: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct Sweep2dOut {
    pub x: Vec<f64>,
    pub y: Vec<f64>,
    pub z: Vec<Vec<f64>>, // z[row][col] -> y index, x index
    pub x_label: String,
    pub y_label: String,
    pub z_label: String,
    pub z_unit: String,
}

pub fn sweep2d(req: &Sweep2dReq) -> Sweep2dOut {
    let n = req.steps.clamp(3, 120);
    let mut x = Vec::with_capacity(n);
    let mut y = Vec::with_capacity(n);
    for i in 0..n {
        let t = i as f64 / (n - 1) as f64;
        x.push(req.from_x + (req.to_x - req.from_x) * t);
        y.push(req.from_y + (req.to_y - req.from_y) * t);
    }
    let mut z = vec![vec![0.0; n]; n];
    for (j, &yv) in y.iter().enumerate() {
        for (i, &xv) in x.iter().enumerate() {
            let mut p = req.params.clone();
            apply_param(&mut p, &req.key_x, xv);
            apply_param(&mut p, &req.key_y, yv);
            let (val, _, _) = read_out(&p, &req.out_key);
            z[j][i] = val;
        }
    }
    let (xl, _xu) = param_meta(&req.key_x);
    let (yl, _yu) = param_meta(&req.key_y);
    let (_, zl, zu) = read_out(&req.params, &req.out_key);
    Sweep2dOut {
        x, y, z,
        x_label: xl, y_label: yl, z_label: zl, z_unit: zu,
    }
}
