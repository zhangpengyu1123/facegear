"""
载荷与载荷系数
================

计算面齿轮传动的名义切向力、法向力，以及 ISO 6336 / HB/Z 84 体系中的
四个载荷系数：

* ``K_A`` 使用系数（application factor）
* ``K_V`` 动载系数（dynamic factor）
* ``K_Hβ`` / ``K_Fβ`` 齿向载荷分布系数
* ``K_Hα`` / ``K_Fα`` 齿间载荷分配系数

设计原则
--------
面齿轮的载荷系数没有专门标准，工程上沿用圆柱齿轮（ISO 6336-1 / HB/Z 84.1）
的做法。本模块提供：

1. **经验默认值**（按节线速度、齿宽比、精度等级估算），适合初步设计；
2. **完全可覆盖**（所有系数均可由用户直接给定），适合详细设计。

出处
----
* ISO 6336-1:2019 / GB/T 3480.1-2021
* HB/Z 84.1-84
* 刘新胜（2016）南京航空航天大学硕士论文 3.2.1 节
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

__all__ = [
    "OperatingConditions",
    "LoadFactors",
    "nominal_forces",
    "estimate_load_factors",
    "equivalent_torque",
]

_EPS = 1e-12


@dataclass
class OperatingConditions:
    """工况输入。

    功率与扭矩二者给其一即可（若都给，以扭矩为准）。

    Parameters
    ----------
    power_kw : float or None
        输入功率，kW。
    torque_nm : float or None
        小齿轮输入扭矩，N·m。
    speed_rpm : float
        小齿轮转速，r/min。
    life_hours : float
        设计寿命，小时（用于疲劳强度校核）。
    load_spectrum : float
        载荷谱系数（等效扭矩/额定扭矩），默认 1.0。
    """

    speed_rpm: float
    power_kw: Optional[float] = None
    torque_nm: Optional[float] = None
    life_hours: float = 5000.0
    load_spectrum: float = 1.0

    def __post_init__(self) -> None:
        if self.speed_rpm <= 0:
            raise ValueError("转速必须为正")
        if self.power_kw is None and self.torque_nm is None:
            raise ValueError("必须给出功率或扭矩之一")
        if self.life_hours <= 0:
            raise ValueError("寿命必须为正")

    @property
    def torque_Nmm(self) -> float:
        """小齿轮输入扭矩，N·mm。"""
        if self.torque_nm is not None:
            return self.torque_nm * 1000.0
        assert self.power_kw is not None
        # T[N·m] = 9550 * P[kW] / n[rpm]
        return 9550.0 * self.power_kw / self.speed_rpm * 1000.0

    @property
    def pitch_line_velocity(self) -> float:
        """小齿轮节线速度估算，m/s（取分度圆，需 geometry 提供 d1）。"""
        return float("nan")

    def pitch_velocity(self, d1_mm: float) -> float:
        """小齿轮分度圆处节线速度，m/s。"""
        return math.pi * d1_mm * 1e-3 * self.speed_rpm / 60.0


@dataclass
class LoadFactors:
    """载荷系数（ISO 6336 体系）。"""

    KA: float = 1.0    # 使用系数
    KV: float = 1.1    # 动载系数
    KHb: float = 1.1   # 接触强度齿向载荷分布系数
    KFb: float = 1.0   # 弯曲强度齿向载荷分布系数
    KHa: float = 1.0   # 接触强度齿间载荷分配系数
    KFa: float = 1.0   # 弯曲强度齿间载荷分配系数
    source: str = "estimate"
    notes: list[str] = field(default_factory=list)

    @property
    def KH(self) -> float:
        """接触应力总载荷系数 K_H = KA*KV*KHb*KHa。"""
        return self.KA * self.KV * self.KHb * self.KHa

    @property
    def KF(self) -> float:
        """弯曲应力总载荷系数 K_F = KA*KV*KFb*KFa。"""
        return self.KA * self.KV * self.KFb * self.KFa


def estimate_load_factors(
    v_pitch: float,
    b: float,
    d1: float,
    quality_grade: int = 7,
    load_smooth: bool = True,
    KA: Optional[float] = None,
    KV: Optional[float] = None,
    KHb: Optional[float] = None,
    KHa: Optional[float] = None,
) -> LoadFactors:
    """由节线速度、齿宽等估算载荷系数（ISO 6336-1 工程简化）。

    Parameters
    ----------
    v_pitch : float
        小齿轮节线速度，m/s。
    b : float
        齿宽，mm。
    d1 : float
        小齿轮分度圆直径，mm。
    quality_grade : int
        齿轮精度等级（GB/T 10095 / ISO 1328），1~12，常用 6~8。
    load_smooth : bool
        载荷是否平稳（True：平稳；False：有冲击）。
    KA, KV, KHb, KHa : float or None
        显式覆盖值；给出则不再估算。

    Returns
    -------
    LoadFactors
    """
    notes: list[str] = []

    # ---- 使用系数 K_A ----
    if KA is None:
        KA = 1.0 if load_smooth else 1.25
        notes.append(
            f"K_A 取经验值 {KA:.2f}（{'平稳载荷' if load_smooth else '冲击载荷'}）"
        )

    # ---- 动载系数 K_V ----
    # ISO 6336-1 的 K_V 依赖临界转速比；工程简化按精度等级 + 节线速度估算
    if KV is None:
        # 基准：精度 7 级、v=10 m/s 时 KV≈1.10
        q = max(1, min(12, quality_grade))
        # 速度项（超线性）
        speed_term = 1.0 + (v_pitch / 25.0) ** 1.6
        # 精度项：每高 1 级约降 0.02
        grade_term = 1.0 + 0.03 * (q - 7)
        KV = speed_term * grade_term
        KV = max(1.0, min(KV, 1.8))
        notes.append(
            f"K_V 按节线速度 {v_pitch:.2f} m/s、精度 {q} 级估算为 {KV:.3f}"
            "（ISO 6336-1 简化）"
        )

    # ---- 齿向载荷分布系数 ----
    if KHb is None:
        # ISO 6336-1: 与 b/d1 比、精度、装配有关。简化经验式
        ratio = b / d1 if d1 > 0 else 0.5
        KHb = 1.0 + 0.35 * max(0.0, ratio - 0.5) + 0.02 * (quality_grade - 7)
        KHb = max(1.0, min(KHb, 1.6))
        notes.append(f"K_Hβ 按 b/d1={ratio:.2f} 估算为 {KHb:.3f}")

    if KHa is None:
        KHa = 1.0
        notes.append("K_Hα 取 1.0（直齿面齿轮，重合度分配影响由 Y_ε/Z_ε 计入）")

    # ---- 弯曲强度用系数 ----
    # ISO 6336-1: K_Fβ ≈ K_Hβ^N，N = (b/h)^2/(1+b/h+(b/h)^2)
    KFb = KHb ** 0.85
    KFa = KHa

    return LoadFactors(KA=KA, KV=KV, KHb=KHb, KFb=KFb, KHa=KHa, KFa=KFa,
                       source="estimate", notes=notes)


def nominal_forces(
    T1_Nmm: float, d1: float, alpha: float
) -> dict:
    """名义切向力与法向力。

    .. math::

        F_t = 2 T_1 / d_1, \\qquad F_n = F_t / \\cos\\alpha

    返回 ``{"Ft", "Fn", "Ft_per_width"}``（N、N、N/mm）。
    """
    if d1 <= 0:
        raise ValueError("d1 必须为正")
    Ft = 2.0 * T1_Nmm / d1
    Fn = Ft / math.cos(alpha)
    return {"Ft": Ft, "Fn": Fn}


def equivalent_torque(T_nominal_Nmm: float, load_spectrum: float = 1.0) -> float:
    """按载荷谱折算等效扭矩（简化线性折算）。

    ``T_eq = T_nominal * load_spectrum``
    """
    return T_nominal_Nmm * load_spectrum
