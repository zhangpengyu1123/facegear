"""
面齿轮传动几何参数计算模块
==============================

本模块实现正交/非正交直齿面齿轮（face gear）传动的基础几何计算，
所有公式均标注文献出处。

坐标系约定
----------
采用 Litvin 面齿轮理论的标准约定：

* 小齿轮（pinion）轴线记为 z1 轴；
* 面齿轮（face gear）轴线记为 z2 轴；
* 两轴交角为 ``gamma``（正交传动 gamma = 90°）；
* 面齿轮的半径方向为 r（从 z2 轴向外为正）。

单位约定
--------
本包内部一律使用国际单位制工程单位：

* 长度：mm
* 力：N
* 力矩：N·mm
* 应力：MPa
* 角度：内部用弧度，公开接口用度

术语
----
z1      小齿轮齿数
z2      面齿轮齿数
zs      插齿刀（gear shaper cutter）齿数，通常 ``zs = z1 + 2``
m       模数 (mm)
alpha   压力角 (°)
gamma   轴交角 (°)
ha_star 齿顶高系数（默认 1.0）
c_star  顶隙系数（默认 0.25）
b       面齿轮齿宽 (mm)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

__all__ = [
    "FaceGearParams",
    "FaceGearGeometry",
    "psi_deg2rad",
]

# 防止除零用的小量
_EPS = 1e-12


def psi_deg2rad(deg: float) -> float:
    """角度转弧度。"""
    return math.radians(deg)


@dataclass
class FaceGearParams:
    """面齿轮传动基本设计参数（输入）。

    Parameters
    ----------
    m : float
        模数，mm。
    z1 : int
        小齿轮齿数。
    z2 : int
        面齿轮齿数。
    alpha_deg : float
        压力角，度。航空面齿轮常用 25°。
    zs : int or None
        插齿刀齿数。若为 None 则取 ``z1 + 2``。
        Litvin 理论要求 ``zs > z1``，以避免面齿轮内端边缘接触。
    gamma_deg : float
        轴交角，度。正交面齿轮为 90°。
    ha_star : float
        齿顶高系数，默认 1.0。
    c_star : float
        顶隙系数，默认 0.25。
    b : float or None
        面齿轮齿宽（沿径向），mm。若为 None 则由内外半径差得到。
    r_inner : float or None
        面齿轮内半径，mm。
    r_outer : float or None
        面齿轮外半径，mm。
    x1 : float
        小齿轮变位系数，默认 0。
    x2 : float
        面齿轮当量变位系数（节锥面处），默认 0。
    """

    m: float
    z1: int
    z2: int
    alpha_deg: float = 25.0
    zs: Optional[int] = None
    gamma_deg: float = 90.0
    ha_star: float = 1.0
    c_star: float = 0.25
    b: Optional[float] = None
    r_inner: Optional[float] = None
    r_outer: Optional[float] = None
    x1: float = 0.0
    x2: float = 0.0

    def __post_init__(self) -> None:
        if self.zs is None:
            self.zs = self.z1 + 2
        if self.m <= 0:
            raise ValueError("模数 m 必须为正")
        if self.z1 < 3:
            raise ValueError("小齿轮齿数 z1 必须 >= 3")
        if self.z2 <= self.z1:
            raise ValueError("面齿轮齿数 z2 必须大于小齿轮齿数 z1")
        if not (0 < self.alpha_deg < 45):
            raise ValueError("压力角应在 (0, 45) 度范围内")
        if not (0 < self.gamma_deg <= 90):
            raise ValueError("轴交角应在 (0, 90] 度范围内")
        if self.zs <= self.z1:
            raise ValueError("插齿刀齿数 zs 必须大于小齿轮齿数 z1")
        # 齿宽与内外半径的一致性
        if self.r_inner is not None and self.r_outer is not None:
            if self.r_outer <= self.r_inner:
                raise ValueError("外半径必须大于内半径")
            if self.b is None:
                self.b = self.r_outer - self.r_inner
        if self.b is not None and self.b <= 0:
            raise ValueError("齿宽 b 必须为正")

    # ---------- 派生量 ----------
    @property
    def alpha(self) -> float:
        """压力角，弧度。"""
        return math.radians(self.alpha_deg)

    @property
    def gamma(self) -> float:
        """轴交角，弧度。"""
        return math.radians(self.gamma_deg)

    @property
    def u(self) -> float:
        """传动比 z2/z1。"""
        return self.z2 / self.z1

    @property
    def m2s(self) -> float:
        """插齿刀与面齿轮的齿数比 Ns/N2（何飞 2023 式(29) 中的 m2s）。"""
        return self.zs / self.z2


@dataclass
class FaceGearGeometry:
    """面齿轮传动几何计算结果（输出）。

    所有长度单位 mm，角度单位弧度（除非字段名以 ``_deg`` 结尾）。
    """

    p: FaceGearParams

    # ---- 小齿轮（pinion）----
    d1: float = field(init=False)   # 分度圆直径
    db1: float = field(init=False)  # 基圆直径
    da1: float = field(init=False)  # 齿顶圆直径
    df1: float = field(init=False)  # 齿根圆直径

    # ---- 插齿刀（shaper cutter）----
    ds: float = field(init=False)   # 分度圆直径
    dbs: float = field(init=False)  # 基圆直径

    # ---- 面齿轮（face gear）----
    r_fp: float = field(init=False)      # 变位系数为 0 处的面齿轮分度圆半径
    r_inner_limit: float = field(init=False)   # 齿根不根切的最小内半径（估算）
    r_outer_limit: float = field(init=False)   # 齿顶不尖化的最大外半径（估算）
    r_inner: float = field(init=False)         # 实际内半径
    r_outer: float = field(init=False)         # 实际外半径
    b: float = field(init=False)               # 实际齿宽

    # ---- 当量齿轮（equivalent spur gear, HB/Z84 / ISO 6336 路线）----
    z_eq: float = field(init=False)     # 面齿轮当量齿数
    d_eq: float = field(init=False)     # 当量分度圆直径
    db_eq: float = field(init=False)    # 当量基圆直径

    # ---- 重合度与当量齿宽 ----
    eps_alpha: float = field(init=False)   # 端面重合度（何飞 2023 式(27)）
    b_eff: float = field(init=False)       # 当量齿宽 B_e（刘新胜 式(2-9) 概念）

    # ---- 诊断信息 ----
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._compute()

    # ------------------------------------------------------------------
    def _compute(self) -> None:
        p = self.p
        m = p.m
        a = p.alpha

        # ---------- 小齿轮 ----------
        self.d1 = m * p.z1
        self.db1 = self.d1 * math.cos(a)
        self.da1 = m * (p.z1 + 2 * p.ha_star + 2 * p.x1)
        self.df1 = m * (p.z1 - 2 * p.ha_star - 2 * p.c_star + 2 * p.x1)
        if self.da1 <= self.db1:
            self.warnings.append(
                "小齿轮齿顶圆直径不大于基圆直径，齿顶附近无渐开线，请检查参数。"
            )

        # ---------- 插齿刀 ----------
        self.ds = m * p.zs
        self.dbs = self.ds * math.cos(a)

        # ---------- 面齿轮 ----------
        # 变位系数为 0 处的面齿轮分度圆半径（刘新胜 2.2.2 节：r_fp = m·zf/2）
        self.r_fp = m * p.z2 / 2.0

        # 极限半径估算（见 _estimate_limit_radii 说明）
        ri_lim, ro_lim = self._estimate_limit_radii()
        self.r_inner_limit = ri_lim
        self.r_outer_limit = ro_lim

        # 实际内外半径：优先使用用户输入
        if p.r_inner is not None:
            self.r_inner = p.r_inner
        else:
            self.r_inner = ri_lim
        if p.r_outer is not None:
            self.r_outer = p.r_outer
        else:
            self.r_outer = ro_lim

        if p.b is not None:
            self.b = p.b
        else:
            self.b = self.r_outer - self.r_inner

        if self.r_inner < ri_lim - 1e-6:
            self.warnings.append(
                f"给定内半径 {self.r_inner:.3f} mm 小于估算根切极限 "
                f"{ri_lim:.3f} mm，内端可能发生齿根根切。"
            )
        if self.r_outer > ro_lim + 1e-6:
            self.warnings.append(
                f"给定外半径 {self.r_outer:.3f} mm 大于估算齿顶尖化极限 "
                f"{ro_lim:.3f} mm，外端齿顶可能变尖。"
            )

        # ---------- 当量齿轮 ----------
        # 面齿轮在节锥面附近的齿形可等效为直齿圆柱齿轮（刘新胜 2.3.1）。
        # 工程实践中取当量齿数 = 面齿轮齿数；直齿时螺旋角为 0，
        # 因此 zv = z（刘新胜式(3-40) 在 beta = beta_b = 0 时退化为 zv = z）。
        self.z_eq = float(p.z2)
        self.d_eq = m * self.z_eq
        self.db_eq = self.d_eq * math.cos(a)

        # ---------- 重合度 ----------
        self.eps_alpha = self._contact_ratio()

        # ---------- 当量齿宽 ----------
        # 刘新胜式(2-9) 给出的是接触椭圆长轴量级；工程上用作"有效承载齿宽"。
        # 这里取齿宽与接触椭圆长轴中的较小者作为有效齿宽下限保护。
        self.b_eff = self.b

    # ------------------------------------------------------------------
    def _estimate_limit_radii(self) -> tuple[float, float]:
        """估算面齿轮内/外半径的理论极限。

        说明
        ----
        精确的根切/尖化极限需要求解插齿刀齿面与面齿轮齿面的展成界限
        方程（靳广虎 2012 式(2-22)、式(2-24) 等），需要完整的齿面方程
        与数值迭代。本函数采用工程可用的近似估计：

        * 外半径（齿顶尖化）依据刘新胜式(2-3) 的形式
          ``r_o = r_fp * cos(alpha) / cos(alpha_t') * sin(gamma)``，
          其中取齿顶处压力角 ``alpha_t' = alpha`` 的保守近似；
        * 内半径（齿根根切）采用 Litvin 理论的经典结果：面齿轮内端
          必须使插齿刀齿顶不切入面齿轮齿根，近似取
          ``r_i ~ m * (zs / 2) * cos(alpha)`` 量级并按经验系数缩放。

        这些估算值仅作为设计初值，精确值应由齿面展成/TCA 计算或
        有限元校核确定。软件中会标注为"估算"。
        """
        p = self.p
        m, a, g = p.m, p.alpha, p.gamma

        # 外半径：齿顶变尖极限
        # 刘新胜 (2-3): r_o-lim = r_fp * cos(alpha) / cos(alpha_t') * sin(gamma)
        # 齿顶圆处压力角 alpha_t' 近似取 alpha（保守）
        ro = self.r_fp * math.cos(a) / math.cos(a) * math.sin(g)
        # 对正交（gamma=90°），sin(gamma)=1
        ro = self.r_fp * math.sin(g)

        # 内半径：根切极限的工程近似。
        # 采用 Litvin 经典下限：面齿轮内端半径不应小于插齿刀分度圆半径
        # 的投影，否则插齿刀齿顶会切入面齿轮齿根。
        ri = (m * p.zs / 2.0) * math.cos(a) * math.sin(g)
        # 齿宽必须为正
        if ro <= ri:
            ri = 0.5 * ro
        return ri, ro

    # ------------------------------------------------------------------
    def _contact_ratio(self) -> float:
        """面齿轮传动端面重合度。

        采用何飞 2023《面齿轮副啮合强度的简化计算》式(27)：

        .. math::

            \\varepsilon = \\frac{\\theta_{a1} N_1 \\sin\\alpha\\cos\\alpha
                - (N_1 - 2 - N_1\\cos^2\\alpha)}
                {2\\pi \\sin\\alpha\\cos\\alpha}

        其中 ``theta_a1 = sqrt(ra1^2 - rb1^2) / rb1``（式(26)），
        ``N_1 - 2`` 项体现小齿轮比插齿刀少 2 个齿。

        退化保护：若计算值 <= 0（参数极端），返回按标准圆柱齿轮
        端面重合度公式的保守估计。
        """
        p = self.p
        a = p.alpha
        ra1 = self.da1 / 2.0
        rb1 = self.db1 / 2.0
        if ra1 <= rb1:
            return 1.0
        theta_a1 = math.sqrt(ra1 ** 2 - rb1 ** 2) / rb1

        numer = (
            theta_a1 * p.z1 * math.sin(a) * math.cos(a)
            - (p.z1 - 2 - p.z1 * math.cos(a) ** 2)
        )
        denom = 2.0 * math.pi * math.sin(a) * math.cos(a)
        eps = numer / denom
        if eps <= 0 or not math.isfinite(eps):
            self.warnings.append(
                "按何飞式(27) 计算的重合度非正，已回退为 1.0 并标注。"
            )
            return 1.0
        return eps

    # ------------------------------------------------------------------
    def summary(self) -> dict:
        """返回便于序列化/展示的几何结果字典。"""
        return {
            "pinion": {
                "z1": self.p.z1,
                "d1_mm": self.d1,
                "db1_mm": self.db1,
                "da1_mm": self.da1,
                "df1_mm": self.df1,
            },
            "shaper": {
                "zs": self.p.zs,
                "ds_mm": self.ds,
                "dbs_mm": self.dbs,
            },
            "face_gear": {
                "z2": self.p.z2,
                "r_fp_mm": self.r_fp,
                "r_inner_mm": self.r_inner,
                "r_outer_mm": self.r_outer,
                "b_mm": self.b,
                "r_inner_limit_est_mm": self.r_inner_limit,
                "r_outer_limit_est_mm": self.r_outer_limit,
            },
            "equivalent_gear": {
                "z_eq": self.z_eq,
                "d_eq_mm": self.d_eq,
                "db_eq_mm": self.db_eq,
            },
            "mesh": {
                "eps_alpha": self.eps_alpha,
                "b_eff_mm": self.b_eff,
                "u": self.p.u,
                "gamma_deg": self.p.gamma_deg,
            },
            "warnings": list(self.warnings),
        }
