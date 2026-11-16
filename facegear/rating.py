"""
强度校核（安全系数）
======================

按 ISO 6336 / GB/T 3480 的安全系数法校核接触强度与弯曲强度。

安全系数定义
------------
.. math::

    S_H = \\frac{\\sigma_{H,lim}\\,Z_{NT} Z_L Z_V Z_R Z_W Z_X}{\\sigma_H}
    S_F = \\frac{\\sigma_{F,lim}\\,Y_{ST} Y_{NT} Y_{\\delta relT} Y_{RrelT} Y_X}{\\sigma_F}

工程简化
--------
完整 ISO 6336 需要寿命系数（Z_NT / Y_NT，依赖应力循环次数）、
润滑剂系数（Z_L）、速度系数（Z_V）、粗糙度系数（Z_R / Y_RrelT）、
尺寸系数（Z_X / Y_X）等多个系数。本模块提供：

1. ``simplified_allowable()``：按经验系数范围给出许用应力（初步设计）；
2. 用户可直接指定 ``sigma_H_allow`` / ``sigma_F_allow``（详细设计）。

出处
----
* ISO 6336-2/-3:2019
* GB/T 3480.2/-3-2021
* HB/Z 84.2/-84.3（航空）
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

__all__ = [
    "AllowableStress",
    "SafetyResult",
    "simplified_allowable",
    "check_safety",
    "cycles_from_life",
]


@dataclass
class AllowableStress:
    """许用应力（已含各项修正系数）。"""

    sigma_H_allow: float
    sigma_F_allow: float
    Z_NT: float = 1.0
    Y_NT: float = 1.0
    Y_ST: float = 2.0
    Z_LVR: float = 1.0
    Y_RrelT: float = 1.0
    Y_X: float = 1.0
    notes: list[str] = field(default_factory=list)


@dataclass
class SafetyResult:
    """安全系数校核结果。"""

    S_H: float
    S_F: float
    S_H_min: float
    S_F_min: float
    pass_H: bool
    pass_F: bool
    verdict: str
    notes: list[str] = field(default_factory=list)


def cycles_from_life(speed_rpm: float, life_hours: float) -> float:
    """由转速与寿命计算应力循环次数 N_L（单侧啮合）。"""
    if speed_rpm <= 0 or life_hours <= 0:
        raise ValueError("转速与寿命必须为正")
    return speed_rpm * 60.0 * life_hours


def _life_factor(N_L: float, limit_cycles: float = 3e6) -> float:
    """简化寿命系数（ISO 6336 曲线的工程近似）。

    * ``N_L >= limit_cycles``：取 1.0（无限寿命区）；
    * 有限寿命区按 ``(limit/N)^(1/m)`` 提升，``m`` 取 6（接触）/ 6（弯曲）
      的保守值，上限 1.6。
    """
    if N_L <= 0:
        return 1.6
    if N_L >= limit_cycles:
        return 1.0
    factor = (limit_cycles / N_L) ** (1.0 / 6.0)
    return min(factor, 1.6)


def simplified_allowable(
    sigma_H_lim: float,
    sigma_F_lim: float,
    N_L: float = 1e7,
    side_loaded_one_way: bool = True,
    reliability: float = 0.99,
) -> AllowableStress:
    """按 ISO 6336 工程简化计算许用应力。

    Parameters
    ----------
    sigma_H_lim, sigma_F_lim : float
        材料接触/弯曲疲劳极限基准值，MPa。
    N_L : float
        应力循环次数。
    side_loaded_one_way : bool
        单向受载（True）或对称循环（False）。单向受载时 Y_ST 取 2.0。
    reliability : float
        可靠度，0.90~0.999，用于调整最小安全系数建议值。

    Notes
    -----
    简化假设：``Z_L Z_V Z_R Z_W = 1.0``（良好润滑、中等速度、
    Ra ≤ 0.8 μm）；``Z_X = Y_X = 1.0``（m ≤ 5 mm 量级）；
    ``Y_δrelT = Y_RrelT = 1.0``。
    """
    notes: list[str] = []
    Z_NT = _life_factor(N_L, 3e6)
    Y_NT = _life_factor(N_L, 3e6)
    Y_ST = 2.0 if side_loaded_one_way else 1.4
    notes.append(
        f"寿命系数 Z_NT={Z_NT:.3f}、Y_NT={Y_NT:.3f}（N_L={N_L:.3e}）"
    )
    notes.append(
        "简化假设 Z_L=Z_V=Z_R=Z_W=1.0、Y_δrelT=Y_RrelT=1.0、"
        "Z_X=Y_X=1.0；详细设计应按 ISO 6336 逐项确定。"
    )

    sigma_H_allow = sigma_H_lim * Z_NT * 1.0 * 1.0 * 1.0 * 1.0 * 1.0
    sigma_F_allow = sigma_F_lim * Y_ST * Y_NT * 1.0 * 1.0 * 1.0

    return AllowableStress(
        sigma_H_allow=sigma_H_allow,
        sigma_F_allow=sigma_F_allow,
        Z_NT=Z_NT, Y_NT=Y_NT, Y_ST=Y_ST,
        notes=notes,
    )


def check_safety(
    sigma_H: float,
    sigma_F: float,
    allow: AllowableStress,
    S_H_min: Optional[float] = None,
    S_F_min: Optional[float] = None,
    reliability: float = 0.99,
) -> SafetyResult:
    """计算安全系数并判定。

    最小安全系数建议值（ISO 6336 / 工程实践）：

    * 一般工业传动：S_H ≥ 1.0~1.1，S_F ≥ 1.4~1.6
    * 航空传动（高可靠）：S_H ≥ 1.1~1.3，S_F ≥ 1.6~2.0

    未指定时按 ``reliability`` 插值：0.99 → (1.10, 1.50)。
    """
    notes: list[str] = []
    if S_H_min is None or S_F_min is None:
        # 按可靠度插值
        r = min(max(reliability, 0.90), 0.999)
        t = (r - 0.90) / (0.999 - 0.90)  # 0..1
        S_H_min = 1.0 + 0.2 * t
        S_F_min = 1.35 + 0.45 * t
        notes.append(
            f"最小安全系数按可靠度 {reliability:.3f} 插值："
            f"S_H,min={S_H_min:.2f}, S_F,min={S_F_min:.2f}"
        )

    if sigma_H <= 0 or sigma_F <= 0:
        raise ValueError("应力必须为正")

    S_H = allow.sigma_H_allow / sigma_H
    S_F = allow.sigma_F_allow / sigma_F
    pass_H = S_H >= S_H_min
    pass_F = S_F >= S_F_min
    if pass_H and pass_F:
        verdict = "合格"
    elif not pass_H and not pass_F:
        verdict = "不合格（接触与弯曲强度均不足）"
    elif not pass_H:
        verdict = "不合格（接触强度不足）"
    else:
        verdict = "不合格（弯曲强度不足）"

    return SafetyResult(
        S_H=S_H, S_F=S_F,
        S_H_min=S_H_min, S_F_min=S_F_min,
        pass_H=pass_H, pass_F=pass_F, verdict=verdict,
        notes=notes,
    )
