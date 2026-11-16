"""
facegear —— 面齿轮传动应力计算软件
=====================================

正交/非正交直齿面齿轮（face gear, 面齿轮传动）的接触应力与齿根弯曲
应力计算工具，理论基础来自：

* ISO 6336-2/-3 / GB/T 3480 / HB/Z 84 圆柱齿轮承载能力计算体系
* Litvin 面齿轮展成理论
* 何飞等（2023）面齿轮副啮合强度的简化计算
* 刘新胜（2016）基于航标的面齿轮传动弯曲强度计算方法研究

快速开始
--------
>>> from facegear import FaceGearParams, OperatingConditions, solve
>>> p = FaceGearParams(m=6.35, z1=25, z2=160, alpha_deg=25, b=40)
>>> op = OperatingConditions(speed_rpm=1000, torque_nm=1600)
>>> res = solve(p, op, sigma_H_lim=1500, sigma_F_lim=850)
>>> res.safety["verdict"]

命令行
------
.. code-block:: bash

    python -m facegear.cli --m 6.35 --z1 25 --z2 160 --alpha 25 --b 40 \\
        --torque 1600 --speed 1000 --material 20CrMnTi-渗碳淬火

图形界面
--------
.. code-block:: bash

    python -m facegear.gui
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = [
    "FaceGearParams",
    "FaceGearGeometry",
    "OperatingConditions",
    "LoadFactors",
    "LoadFactors",
    "Material",
    "get_material",
    "list_materials",
    "solve",
    "SolveResult",
    "generate_report",
    "render_report_html",
]

from .geometry import FaceGearParams, FaceGearGeometry
from .load import OperatingConditions, LoadFactors
from .material import Material, get_material, list_materials
from .solver import solve, SolveResult
from .report import generate_report, render_report_html
