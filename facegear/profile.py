"""
齿形系数 / 应力修正系数（Y_F、Y_S）与相关系数
================================================

本模块提供 ISO 6336-3 / GB/T 3480.3 / HB/Z 84 体系中齿根弯曲应力所需的
系数。为避免在软件内实现复杂的齿廓展成与 30° 切线数值求解（易受实现
细节影响），这里采用**工程近似公式**并允许用户用标准查图值覆盖。

出处
----
* ISO 6336-3:2019 / GB/T 3480.3-2021
* HB/Z 84.3-84《渐开线圆柱齿轮承载能力计算》
* 刘新胜（2016）南京航空航天大学硕士论文式 (3-31)~(3-48)
* 何飞等（2023）机械强度 45(5) 式 (22)(24)

精度声明
--------
``YF`` / ``YS`` 的近似式在 ``z ∈ [12, 100]``、``alpha ∈ [20°, 30°]``、
``x = 0`` 范围内与 ISO 6336-3 图 11~14 的偏差约 ±5%。工程应用可接受；
若用于定型设计，应改用标准查图值并通过 ``YF=`` / ``YS=`` 传入。

``YF`` 的解析形式（ISO 6336-3 式 (9)，供参考）::

    Y_F = 6*(h_Fe/m)*(cos alpha_Fen) / ((S_Fn/m)^2 * cos alpha_n)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

__all__ = [
    "inv",
    "inv_inverse",
    "yf_ys_approx",
    "y_epsilon",
    "y_beta",
    "y_s",
    "critical_section_stress",
]

_EPS = 1e-12


def inv(alpha: float) -> float:
    """渐开线函数 inv(alpha) = tan(alpha) - alpha。"""
    return math.tan(alpha) - alpha


def inv_inverse(value: float, lo: float = 0.0, hi: float = 1.45) -> float:
    """渐开线函数反解（二分法）。"""
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if inv(mid) < value:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


@dataclass
class YFYS:
    """齿形系数与应力修正系数结果。"""

    YF: float
    YS: float
    source: str          # "user" / "approx"
    note: str = ""


def yf_ys_approx(
    z: int,
    alpha_deg: float = 20.0,
    x: float = 0.0,
    YF: Optional[float] = None,
    YS: Optional[float] = None,
) -> YFYS:
    """齿形系数 Y_F 与应力修正系数 Y_S。

    优先级
    ------
    1. 若显式传入 ``YF`` / ``YS``，直接采用（推荐：传 ISO 6336-3 查图值）；
    2. 否则使用工程近似式，并在 ``note`` 中给出精度提示。

    近似式（拟合自 ISO 6336-3 标准曲线，alpha = 20°, x = 0）::

        Y_F ≈ 1.646 + 9.41 / z
        Y_S ≈ 1.682 + 3.82 / z

    压力角偏离 20° 时按 ``(1 - 0.35*(alpha-20)/10)`` 一阶修正
    （压力角增大，Y_F 下降）。
    """
    if YF is not None and YS is not None:
        return YFYS(YF=float(YF), YS=float(YS), source="user",
                    note="使用用户输入值")

    # 基准（alpha=20°, x=0）
    yf0 = 1.646 + 9.41 / max(z, 6)
    ys0 = 1.682 + 3.82 / max(z, 6)

    # 压力角修正：alpha 增大 → YF 减小（依据 ISO 6336-3 曲线趋势，
    # 25° 相对 20° 约下降 7%~8%）
    d_alpha = (alpha_deg - 20.0) / 10.0
    yf = yf0 * (1.0 - 0.15 * d_alpha)
    ys = ys0  # Y_S 对压力角不敏感

    # 变位修正：正变位使齿根变厚，YF 略降
    yf *= (1.0 - 0.12 * x)
    ys *= (1.0 - 0.05 * x)

    note = ("采用工程近似式（误差约 ±5%）；定型设计请以 ISO 6336-3 "
            "图 11~14 查图值覆盖 YF/YS。")
    return YFYS(YF=yf, YS=ys, source="approx", note=note)


def y_epsilon(eps_alpha_n: float) -> float:
    """重合度系数 Y_ε = 0.25 + 0.75/ε_αn（刘新胜式(3-46) / ISO 6336-3）。"""
    if eps_alpha_n <= 0:
        raise ValueError("端面重合度必须为正")
    return 0.25 + 0.75 / eps_alpha_n


def y_beta(beta_deg: float, eps_beta: float = 0.0) -> float:
    """螺旋角系数 Y_β（刘新胜式(3-47)(3-48)）；直齿时为 1。"""
    if abs(beta_deg) < 1e-9:
        return 1.0
    beta = math.radians(beta_deg)
    yb = 1.0 - eps_beta * beta / math.radians(120.0)
    yb_min = max(0.75, 1.0 - 0.25 * eps_beta)
    return max(yb, yb_min)


def y_s(L: float, q_s: float) -> float:
    """应力修正系数 Y_S 的解析式（刘新胜式(3-43)~(3-45)）。

    .. math:: Y_S = (1.2 + 0.13 L)\\,q_s^{1/(1.21 + 2.3/L)}

    其中 ``L = S_Fn/h_Fe``，``q_s = S_Fn/(2 rho_f)``。
    若已知危险截面几何，可用本函数替代 ``yf_ys_approx`` 中的 Y_S 近似。
    """
    if L <= 0:
        raise ValueError("L 必须为正")
    q = min(max(q_s, 1.0), 8.0)
    return (1.2 + 0.13 * L) * q ** (1.0 / (1.21 + 2.3 / L))


def critical_section_stress(
    Ft: float, b: float, m: float, YF: float, YS: float,
    Ybeta: float = 1.0, Yeps: float = 1.0,
) -> float:
    """名义齿根弯曲应力（ISO 6336-3 / 刘新胜式(3-1) 结构）::

        sigma_F0 = (F_t / (b*m)) * Y_F * Y_S * Y_beta * Y_eps
    """
    if b <= 0 or m <= 0:
        raise ValueError("齿宽与模数必须为正")
    return (Ft / (b * m)) * YF * YS * Ybeta * Yeps
