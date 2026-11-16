"""
材料数据库
============

面齿轮常用材料及其疲劳强度参数。

数据来源与免责声明
------------------
下列数值为 **ISO 6336-5 / GB/T 3480.5 图表典型值**的工程参考数据，
按常见热处理工艺整理。实际设计必须依据：

* 材料实测性能（硬度、金相、疲劳试验）；
* 具体热处理规范与企业工艺文件；
* 尺寸系数、表面状况、可靠性要求的修正。

软件中的 ``strength`` 字段为「未修正的疲劳极限基准值」，实际许用应力
还应乘以 ``Y_ST``、``Y_NT``、``Y_δrelT``、``Y_RrelT``、``Y_X`` 等系数
（见 ``facegear.rating``）。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

__all__ = [
    "Material",
    "MATERIALS",
    "get_material",
    "list_materials",
]


@dataclass
class Material:
    """齿轮材料。

    Parameters
    ----------
    name : str
        材料牌号（中国 GB）。
    treatment : str
        热处理工艺。
    sigma_H_lim : float
        接触疲劳极限 σ_H,lim，MPa（ISO 6336-5 基准值）。
    sigma_F_lim : float
        弯曲疲劳极限 σ_F,lim，MPa（双侧受载基准；单侧受载需 ×1.0，
        GB/T 3480 中对称循环需 ×0.7）。
    E : float
        弹性模量，MPa。
    nu : float
        泊松比。
    hardness : str
        典型硬度范围。
    note : str
        备注。
    """

    name: str
    treatment: str
    sigma_H_lim: float
    sigma_F_lim: float
    E: float = 210000.0
    nu: float = 0.3
    hardness: str = ""
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ----------------------------------------------------------------------
# 常用齿轮材料（典型参考值）
# ----------------------------------------------------------------------
MATERIALS: dict[str, Material] = {
    "20CrMnTi-渗碳淬火": Material(
        name="20CrMnTi", treatment="渗碳淬火",
        sigma_H_lim=1500.0, sigma_F_lim=480.0,
        hardness="HRC 58~62 (表面)",
        note="航空/汽车面齿轮常用；典型渗碳层 0.8~1.2 mm",
    ),
    "18Cr2Ni4WA-渗碳淬火": Material(
        name="18Cr2Ni4WA", treatment="渗碳淬火",
        sigma_H_lim=1600.0, sigma_F_lim=520.0,
        hardness="HRC 58~62 (表面)",
        note="高淬透性航空齿轮钢，重载面齿轮首选",
    ),
    "20Cr2Ni4-渗碳淬火": Material(
        name="20Cr2Ni4", treatment="渗碳淬火",
        sigma_H_lim=1550.0, sigma_F_lim=500.0,
        hardness="HRC 58~62 (表面)",
        note="重型齿轮钢",
    ),
    "42CrMo-调质": Material(
        name="42CrMo", treatment="调质",
        sigma_H_lim=720.0, sigma_F_lim=300.0,
        hardness="HB 280~320",
        note="中载面齿轮，成本低",
    ),
    "40Cr-调质": Material(
        name="40Cr", treatment="调质",
        sigma_H_lim=680.0, sigma_F_lim=280.0,
        hardness="HB 250~280",
        note="轻载面齿轮",
    ),
    "38CrMoAl-渗氮": Material(
        name="38CrMoAl", treatment="渗氮",
        sigma_H_lim=900.0, sigma_F_lim=380.0,
        hardness="HV 900~1100 (表面)",
        note="变形小，适合精密面齿轮",
    ),
    "20CrMnMo-渗碳淬火": Material(
        name="20CrMnMo", treatment="渗碳淬火",
        sigma_H_lim=1450.0, sigma_F_lim=470.0,
        hardness="HRC 58~62 (表面)",
        note="替代 20CrMnTi 的较高强度选择",
    ),
}


def get_material(key: str) -> Material:
    """按名称或牌号获取材料。

    ``key`` 可以是字典键（如 ``"20CrMnTi-渗碳淬火"``）或牌号
    （如 ``"20CrMnTi"``）。
    """
    if key in MATERIALS:
        return MATERIALS[key]
    # 按牌号模糊匹配
    for m in MATERIALS.values():
        if m.name == key or m.name.lower() == key.lower():
            return m
    raise KeyError(f"未找到材料 '{key}'。可用：{list(MATERIALS)}")


def list_materials() -> list[dict]:
    """列出全部材料（便于 GUI 下拉框）。"""
    return [
        {
            "key": k,
            "name": m.name,
            "treatment": m.treatment,
            "sigma_H_lim": m.sigma_H_lim,
            "sigma_F_lim": m.sigma_F_lim,
            "hardness": m.hardness,
        }
        for k, m in MATERIALS.items()
    ]
