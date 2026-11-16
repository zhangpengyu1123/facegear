"""
应力计算模块
==============

三个互相独立的计算引擎，便于交叉验证：

1. **ISO 6336 当量齿轮法**（``contact_stress_iso6336`` / ``bending_stress_iso6336``）
   —— 主引擎（推荐）。把面齿轮传动当量为一对直齿圆柱齿轮（z1, z2），
   按 ISO 6336-2/-3 / GB/T 3480 / HB/Z 84 计算。
   验证：对何飞 2023 表 1 算例（m=6.35, z1=25, z2=160, α=25°, b=40,
   T=1600 N·m），本引擎给出 σ_H ≈ 834 MPa，与论文有限元值 823.2 MPa
   高度吻合（偏差 1.3%）。

2. **Hertz 局部接触法**（``contact_stress_hertz``）—— 参考。
   用面齿轮齿面主曲率 + 赫兹点接触理论直接求最大接触应力。

3. **何飞简化公式**（``hefei_simplified``）—— 文献复现。
   原样实现何飞等（2023）的简化公式，用于与文献对照，并如实标注
   原公式体系内部的不自洽。

公式出处
--------
* ISO 6336-2:2019 / GB/T 3480.2-2021（接触强度）
* ISO 6336-3:2019 / GB/T 3480.3-2021（弯曲强度）
* HB/Z 84.2-84 / HB/Z 84.3-84
* 何飞等（2023）机械强度 45(5): 1192-1198
* 刘新胜（2016）南京航空航天大学硕士论文 3.2 节
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from .profile import y_epsilon, y_beta

__all__ = [
    "Z_H", "Z_E", "Z_epsilon",
    "contact_stress_iso6336", "bending_stress_iso6336",
    "contact_stress_hertz", "hefei_simplified",
]

_EPS = 1e-12


# ======================================================================
# ISO 6336 系数
# ======================================================================
def Z_H(alpha: float) -> float:
    """节点区域系数 Z_H（直齿，β=0，α_t = α_wt = α）。

    .. math:: Z_H = \\sqrt{2/(\\cos\\alpha\\sin\\alpha)}

    ISO 6336-2 式 (6)。
    """
    return math.sqrt(2.0 / (math.cos(alpha) * math.sin(alpha)))


def Z_E(E1: float, nu1: float, E2: float, nu2: float) -> float:
    """弹性系数 Z_E，(N/mm²)^0.5。

    .. math:: Z_E = \\sqrt{1/\\left[\\pi\\left(
              \\frac{1-\\nu_1^2}{E_1}+\\frac{1-\\nu_2^2}{E_2}\\right)\\right]}

    ISO 6336-2 式 (7)。
    """
    denom = math.pi * ((1.0 - nu1 ** 2) / E1 + (1.0 - nu2 ** 2) / E2)
    if denom <= 0:
        raise ValueError("材料参数无效")
    return math.sqrt(1.0 / denom)


def Z_epsilon(eps_alpha: float) -> float:
    """重合度系数 Z_ε（直齿）。

    ISO 6336-2：``Z_ε = sqrt((4-ε_α)/3)``（1 ≤ ε_α ≤ 2）；
    ``ε_α > 2`` 时取 ``1/sqrt(ε_α)``。
    """
    if eps_alpha <= 0:
        raise ValueError("重合度必须为正")
    if eps_alpha <= 2.0:
        return math.sqrt(max((4.0 - eps_alpha) / 3.0, 1e-9))
    return 1.0 / math.sqrt(eps_alpha)


# ======================================================================
# ISO 6336-2 接触应力
# ======================================================================
def contact_stress_iso6336(
    Ft: float,
    b: float,
    d1: float,
    u: float,
    alpha: float,
    eps_alpha: float,
    lf,
    E1: float = 210000.0,
    nu1: float = 0.3,
    E2: float = 210000.0,
    nu2: float = 0.3,
    Z_H_override: Optional[float] = None,
    Z_E_override: Optional[float] = None,
    Z_eps_override: Optional[float] = None,
) -> dict:
    """ISO 6336-2 接触应力（当量直齿圆柱齿轮副）。

    .. math::

        \\sigma_{H0} = Z_H Z_E Z_\\varepsilon Z_\\beta
                       \\sqrt{\\frac{F_t}{b d_1}\\frac{u+1}{u}}

        \\sigma_H = \\sigma_{H0}\\sqrt{K_A K_V K_{H\\beta} K_{H\\alpha}}

    Parameters
    ----------
    Ft : float
        名义切向力，N。
    b : float
        齿宽，mm。
    d1 : float
        小齿轮分度圆直径，mm。
    u : float
        传动比（z2/z1，> 1）。
    alpha : float
        压力角，rad。
    eps_alpha : float
        端面重合度。
    lf : LoadFactors
        载荷系数。
    E1, nu1, E2, nu2 : float
        弹性模量（MPa）与泊松比。

    Returns
    -------
    dict
        ``{"sigma_H", "sigma_H0", "ZH", "ZE", "Zeps", "KH", "stress_term"}``
    """
    if b <= 0 or d1 <= 0:
        raise ValueError("齿宽与分度圆直径必须为正")
    if u <= 0:
        raise ValueError("传动比必须为正")

    ZH = Z_H_override if Z_H_override is not None else Z_H(alpha)
    ZE = Z_E_override if Z_E_override is not None else Z_E(E1, nu1, E2, nu2)
    Zeps = Z_eps_override if Z_eps_override is not None else Z_epsilon(eps_alpha)

    stress_term = math.sqrt((Ft / (b * d1)) * ((u + 1.0) / u))
    sigma_H0 = ZH * ZE * Zeps * stress_term
    KH = lf.KH
    sigma_H = sigma_H0 * math.sqrt(KH)

    return {
        "sigma_H": sigma_H,
        "sigma_H0": sigma_H0,
        "ZH": ZH,
        "ZE": ZE,
        "Zeps": Zeps,
        "stress_term": stress_term,
        "KH": KH,
        "method": "ISO 6336-2 (equivalent spur gear)",
    }


# ======================================================================
# ISO 6336-3 弯曲应力
# ======================================================================
def bending_stress_iso6336(
    Ft: float,
    b: float,
    m: float,
    YF: float,
    YS: float,
    eps_alpha: float,
    lf,
    beta_deg: float = 0.0,
    eps_beta: float = 0.0,
    YF_override: Optional[float] = None,
    Yeps_override: Optional[float] = None,
) -> dict:
    """ISO 6336-3 齿根弯曲应力。

    .. math::

        \\sigma_{F0} = \\frac{F_t}{b m} Y_F Y_S Y_\\beta Y_\\varepsilon

        \\sigma_F = \\sigma_{F0} K_A K_V K_{F\\beta} K_{F\\alpha}

    Returns
    -------
    dict
        ``{"sigma_F", "sigma_F0", "YF", "YS", "Ybeta", "Yeps", "KF"}``
    """
    if b <= 0 or m <= 0:
        raise ValueError("齿宽与模数必须为正")

    Yeps = Yeps_override if Yeps_override is not None else y_epsilon(eps_alpha)
    Ybeta = y_beta(beta_deg, eps_beta)

    sigma_F0 = (Ft / (b * m)) * YF * YS * Ybeta * Yeps
    KF = lf.KF
    sigma_F = sigma_F0 * KF

    return {
        "sigma_F": sigma_F,
        "sigma_F0": sigma_F0,
        "YF": YF,
        "YS": YS,
        "Ybeta": Ybeta,
        "Yeps": Yeps,
        "KF": KF,
        "method": "ISO 6336-3 (equivalent spur gear)",
    }


# ======================================================================
# Hertz 局部接触（面齿轮曲率法）
# ======================================================================
def _elliptic_1st(e: float) -> float:
    """第一类完全椭圆积分 K(e)，AGM。"""
    if e <= 1e-12:
        return math.pi / 2.0
    a, b = 1.0, math.sqrt(max(1.0 - e * e, 1e-24))
    for _ in range(60):
        a2, b2 = 0.5 * (a + b), math.sqrt(a * b)
        if abs(a2 - b2) < 1e-16:
            a = a2
            break
        a, b = a2, b2
    return math.pi / (2.0 * a)


def _elliptic_2nd(e: float) -> float:
    """第二类完全椭圆积分 E(e)，级数展开。"""
    if e <= 1e-12:
        return math.pi / 2.0
    if e >= 1.0:
        return 1.0
    e2 = e * e
    s = 0.0
    coef = 1.0
    for n in range(1, 80):
        coef = coef * (2 * n - 1) / (2 * n)
        term = (coef ** 2) * (e2 ** n) / (2 * n - 1)
        s += term
        if abs(term) < 1e-17:
            break
    return (math.pi / 2.0) * (1.0 - s)


def _k_of_e(e: float) -> float:
    """由偏心率 e 计算曲率比 k = B/A。

    圆接触 e→0 ⇒ k→1；线接触 e→1 ⇒ k→0。
    采用标准关系 ``k = (K(e)-E(e))/(e²K(e))`` 的互补形式。
    """
    if e <= 1e-12:
        return 1.0
    Ke = _elliptic_1st(e)
    Ee = _elliptic_2nd(e)
    return (Ee - (1.0 - e * e) * Ke) / (e * e * Ke)


def _solve_eccentricity(k: float) -> float:
    """由曲率比 k 反解偏心率 e（二分法）。"""
    if k >= 1.0 - 1e-9:
        return 0.0
    lo, hi = 0.0, 1.0 - 1e-9
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if _k_of_e(mid) > k:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def contact_stress_hertz(
    Ft: float,
    m: float,
    alpha: float,
    z1: int,
    zs: int,
    z2: int,
    E1: float = 210000.0,
    nu1: float = 0.3,
    E2: float = 210000.0,
    nu2: float = 0.3,
) -> dict:
    """面齿轮节锥面处赫兹接触应力（何飞 2023 曲率公式 + 赫兹理论）。

    小齿轮主曲率按式(3)，面齿轮主曲率按式(5)(6)（节锥面 θ_s=tanα），
    再用赫兹点接触公式求最大接触应力::

        a = αc·∛(3 F Z_E / (2 Σρ)),  b = βc·∛(...)
        p0 = 3F/(2πab)

    注意：本引擎给出的是**单对齿承担全部载荷**时的局部赫兹应力，
    不考虑多齿分配与载荷系数，通常高于 ISO 6336 当量齿轮法结果，
    宜作为上限参考。
    """
    sin_a, cos_a, tan_a = math.sin(alpha), math.cos(alpha), math.tan(alpha)
    gamma = 0.5 * math.atan(-2.0 * z2 / (zs * cos_a))
    sin2g = math.sin(2.0 * gamma)

    # 小齿轮（节圆处渐开线展开角 theta_1 = tan(alpha)，何飞式(3)）
    # 注意：单位模数下的曲率 k，实际曲率 = k/m
    theta1 = tan_a
    k11 = -2.0 / (z1 * theta1 * cos_a)
    k12 = 0.0

    # 面齿轮（节锥面 theta_s = tan(alpha)）
    ts = tan_a
    a13 = -tan_a / ts
    a23 = zs * cos_a / z2
    a33 = (zs ** 3 / (2.0 * z2 ** 2) * (sin_a * cos_a ** 2 - ts * cos_a ** 3)
           + zs * sin_a ** 2 / (2.0 * ts * cos_a))
    base = -2.0 / (zs * ts * cos_a) + (a13 ** 2 + a23 ** 2) / a33
    cross = 2.0 * a13 * a23 / a33 * sin2g
    k21 = 0.5 * (base - cross)
    k22 = 0.5 * (base + cross)

    sum_rho = k11 + k12 + k21 + k22
    A = 0.5 * sum_rho
    n1, n2 = k11 - k12, k21 - k22
    B = 0.5 * math.sqrt(max(n1 ** 2 + n2 ** 2 + 2 * n1 * n2 * math.cos(2 * gamma), 0.0))

    k_ratio = abs(B / A) if abs(A) > _EPS else 1.0
    k_ratio = min(max(k_ratio, 1e-6), 1.0 - 1e-9)
    if k_ratio > 0.98:
        e = 0.0
        alpha_c = beta_c = 1.0
    else:
        e = _solve_eccentricity(k_ratio)
        Ee = _elliptic_2nd(e)
        alpha_c = (2.0 * Ee / (math.pi * (1.0 - e * e))) ** (1.0 / 3.0)
        beta_c = (2.0 * Ee * math.sqrt(1.0 - e * e) / math.pi) ** (1.0 / 3.0)

    sum_rho_phys = abs(sum_rho) / m  # 何飞 A、B 以单位模数计，故除 m 得 1/mm
    ZE_flex = (1.0 - nu1 ** 2) / E1 + (1.0 - nu2 ** 2) / E2

    a_axis = alpha_c * (3.0 * Ft * ZE_flex / (2.0 * sum_rho_phys)) ** (1.0 / 3.0)
    b_axis = beta_c * (3.0 * Ft * ZE_flex / (2.0 * sum_rho_phys)) ** (1.0 / 3.0)
    p0 = 3.0 * Ft / (2.0 * math.pi * a_axis * b_axis) if a_axis * b_axis > 0 else 0.0

    return {
        "p0": p0,
        "a_axis": a_axis,
        "b_axis": b_axis,
        "sum_rho": sum_rho_phys,
        "A_hat": A,
        "B_hat": B,
        "k_ratio": k_ratio,
        "e": e,
        "alpha_c": alpha_c,
        "beta_c": beta_c,
        "method": "Hertz point contact (Hefei 2023 curvature)",
    }


# ======================================================================
# 何飞简化公式（文献复现）
# ======================================================================
def hefei_simplified(
    m: float, z1: int, zs: int, z2: int, alpha: float,
    b: float, T1_Nmm: float,
    E1: float = 210000.0, nu1: float = 0.3,
    E2: float = 210000.0, nu2: float = 0.3,
    YFa: float = 1.61, Ysa: float = 1.90,
) -> dict:
    """何飞等（2023）面齿轮副啮合强度简化公式（原样实现）。

    严格按式 (25)~(33) 实现，返回中间量便于教学与对照。
    论文报告：对表 1 参数、T1=1600 N·m 给出 σ_c=660.3、σ_b=76.3 MPa。
    本实现复算结果见 ``consistency_note``（原公式体系内部不自洽，
    式(33) 实际需要 ε≈3.6 才能复现 76.3 MPa）。
    """
    sin_a, cos_a, tan_a = math.sin(alpha), math.cos(alpha), math.tan(alpha)
    m2s = zs / z2

    # 重合度（式(26)(27)）
    ra1 = 0.5 * m * (z1 + 2.0)
    rb1 = 0.5 * m * z1 * cos_a
    theta_a1 = math.sqrt(max(ra1 ** 2 - rb1 ** 2, 0.0)) / rb1
    numer = theta_a1 * z1 * sin_a * cos_a - (z1 - 2 - z1 * cos_a ** 2)
    denom = 2.0 * math.pi * sin_a * cos_a
    eps = numer / denom

    # A、B（式(29)(30)）
    A = (zs + z1 * m2s ** 2 * cos_a ** 2) / (z1 * zs * sin_a)
    gamma = 0.5 * math.atan(-2.0 * z2 / (zs * cos_a))
    sin2g = math.sin(2.0 * gamma)
    tan2g = math.tan(2.0 * gamma)
    ZH_c = 4.0 * m2s / (z1 * zs * sin_a * tan_a * tan2g)
    B = math.sqrt(max(
        1.0 / (z1 ** 2 * sin_a ** 2)
        + 4.0 * m2s ** 2 / (zs ** 2 * tan_a ** 2 * sin2g ** 2)
        + ZH_c, 0.0))

    F = 2.0 * T1_Nmm / (m * z1 * cos_a)  # 式(31)

    k_ratio = abs(B / A) if abs(A) > _EPS else 1.0
    k_ratio = min(max(k_ratio, 1e-6), 1.0 - 1e-9)
    if k_ratio > 0.98:
        e, alpha_c, beta_c = 0.0, 1.0, 1.0
    else:
        e = _solve_eccentricity(k_ratio)
        Ee = _elliptic_2nd(e)
        alpha_c = (2.0 * Ee / (math.pi * (1.0 - e * e))) ** (1.0 / 3.0)
        beta_c = (2.0 * Ee * math.sqrt(1.0 - e * e) / math.pi) ** (1.0 / 3.0)

    ZE = (1.0 - nu1 ** 2) / E1 + (1.0 - nu2 ** 2) / E2
    sigma_c = ((12.0 * T1_Nmm * A ** 2 / (m ** 3 * ZE ** 2 * z1 * cos_a)) ** (1.0 / 3.0)
               / (math.pi * alpha_c * beta_c * eps))
    sigma_b = 2.0 * T1_Nmm / (b * m ** 2 * z1 * eps) * YFa * Ysa

    return {
        "eps": eps, "A": A, "B": B, "k_ratio": k_ratio, "e": e,
        "alpha_c": alpha_c, "beta_c": beta_c, "F_n": F, "ZE": ZE,
        "sigma_c": sigma_c, "sigma_b": sigma_b,
        "YFa": YFa, "Ysa": Ysa,
        "paper_reported": {"sigma_c": 660.3, "sigma_b": 76.3},
        "consistency_note": (
            "论文报告 σ_c=660.3、σ_b=76.3 MPa；按式(27) ε="
            f"{eps:.3f} 复算得 σ_c={sigma_c:.1f}、σ_b={sigma_b:.1f} MPa。"
            "偏差源于原公式体系内部不自洽（式(33) 复现 76.3 需 ε≈3.6）。"
        ),
        "method": "Hefei 2023 simplified formulas",
    }
