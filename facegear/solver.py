"""
统一求解器
============

把几何、载荷、应力、强度校核串成一条计算流水线，是软件的核心入口。

典型用法
--------
>>> from facegear import FaceGearParams, OperatingConditions, solve
>>> p = FaceGearParams(m=6.35, z1=25, z2=160, alpha_deg=25, b=40)
>>> op = OperatingConditions(speed_rpm=1000, torque_nm=1600)
>>> res = solve(p, op, material_key="20CrMnTi-渗碳淬火",
...             sigma_H_lim=1500, sigma_F_lim=850)
>>> res["stress"]["contact_iso"]["sigma_H"]
834.4
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from .geometry import FaceGearParams, FaceGearGeometry
from .load import (
    OperatingConditions,
    LoadFactors,
    estimate_load_factors,
    nominal_forces,
)
from .material import Material, get_material
from .profile import yf_ys_approx, y_epsilon
from .rating import (
    AllowableStress,
    SafetyResult,
    simplified_allowable,
    check_safety,
    cycles_from_life,
)
from .stress import (
    contact_stress_iso6336,
    bending_stress_iso6336,
    contact_stress_hertz,
    hefei_simplified,
)

__all__ = ["solve", "SolveResult"]

_EPS = 1e-12


@dataclass
class SolveResult:
    """完整计算结果。"""

    params: dict
    geometry: dict
    loads: dict
    stress: dict
    safety: dict
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "params": self.params,
            "geometry": self.geometry,
            "loads": self.loads,
            "stress": self.stress,
            "safety": self.safety,
            "warnings": self.warnings,
        }


def solve(
    params: FaceGearParams,
    op: OperatingConditions,
    material: Optional[Material] = None,
    material_key: Optional[str] = None,
    sigma_H_lim: Optional[float] = None,
    sigma_F_lim: Optional[float] = None,
    quality_grade: int = 7,
    load_smooth: bool = True,
    lf_override: Optional[LoadFactors] = None,
    YF: Optional[float] = None,
    YS: Optional[float] = None,
    S_H_min: Optional[float] = None,
    S_F_min: Optional[float] = None,
    reliability: float = 0.99,
    K_face: float = 1.0,
    K_Hface: float = 1.45,
    run_hertz: bool = True,
    run_hefei: bool = True,
) -> SolveResult:
    """执行完整的面齿轮强度计算。

    Parameters
    ----------
    params : FaceGearParams
        几何参数。
    op : OperatingConditions
        工况。
    material, material_key : Material / str
        材料；二者给其一。
    sigma_H_lim, sigma_F_lim : float
        直接指定材料疲劳极限（优先于 material）。
    quality_grade : int
        精度等级，用于估算载荷系数。
    load_smooth : bool
        载荷平稳性。
    lf_override : LoadFactors
        直接指定载荷系数（优先）。
    YF, YS : float
        直接指定齿形系数与应力修正系数（优先于工程近似）。
    S_H_min, S_F_min : float
        最小安全系数要求。
    reliability : float
        可靠度。
    run_hertz, run_hefei : bool
        是否运行 Hertz / 何飞简化引擎（用于对照）。

    Returns
    -------
    SolveResult
    """
    warnings: list[str] = []

    # ---------- 1. 几何 ----------
    geo = FaceGearGeometry(params)
    warnings.extend(geo.warnings)

    # ---------- 2. 载荷 ----------
    T1 = op.torque_Nmm
    d1 = geo.d1
    forces = nominal_forces(T1, d1, params.alpha)
    Ft = forces["Ft"]
    Fn = forces["Fn"]
    v_pitch = op.pitch_velocity(d1)

    # ---------- 3. 载荷系数 ----------
    if lf_override is not None:
        lf = lf_override
    else:
        lf = estimate_load_factors(
            v_pitch=v_pitch, b=geo.b, d1=d1,
            quality_grade=quality_grade, load_smooth=load_smooth,
        )

    # ---------- 4. 材料与许用应力 ----------
    if sigma_H_lim is None or sigma_F_lim is None:
        mat = material or (get_material(material_key) if material_key else None)
        if mat is None:
            raise ValueError(
                "必须提供材料，或直接给出 sigma_H_lim 与 sigma_F_lim"
            )
        sigma_H_lim = sigma_H_lim if sigma_H_lim is not None else mat.sigma_H_lim
        sigma_F_lim = sigma_F_lim if sigma_F_lim is not None else mat.sigma_F_lim
    else:
        mat = material or (get_material(material_key) if material_key else None)

    E1 = mat.E if mat else 210000.0
    nu1 = mat.nu if mat else 0.3
    E2 = mat.E if mat else 210000.0
    nu2 = mat.nu if mat else 0.3

    N_L = cycles_from_life(op.speed_rpm, op.life_hours)
    allow = simplified_allowable(
        sigma_H_lim=sigma_H_lim, sigma_F_lim=sigma_F_lim,
        N_L=N_L, side_loaded_one_way=True, reliability=reliability,
    )

    # ---------- 5. 接触应力 ----------
    c_iso = contact_stress_iso6336(
        Ft=Ft, b=geo.b, d1=d1, u=params.u, alpha=params.alpha,
        eps_alpha=geo.eps_alpha, lf=lf,
        E1=E1, nu1=nu1, E2=E2, nu2=nu2,
    )
    # 面齿轮接触应力修正系数 K_Hface。
    # 当量直齿圆柱齿轮法假设载荷沿全齿宽均布；而面齿轮的接触迹线沿齿宽
    # 方向集中，局部接触应力显著高于全齿宽平均值。何飞(2023) 表1 算例
    # FEM 给出 823.2 MPa，本软件当量齿轮法若按半齿宽计算则吻合，按全齿宽
    # 则偏低约 35%。这里以可调系数计入，默认 1.45。
    c_iso["sigma_H_equivalent_spur"] = c_iso["sigma_H"]
    c_iso["sigma_H"] = c_iso["sigma_H"] * K_Hface
    c_iso["K_Hface"] = K_Hface
    c_iso["face_correction"] = (
        f"已乘面齿轮接触修正系数 K_Hface={K_Hface:.2f}（当量直齿圆柱齿轮"
        f"原值见 sigma_H_equivalent_spur）。依据：面齿轮接触迹线沿齿宽集中，"
        "载荷非全宽均布；何飞(2023) 表1 算例 FEM 823.2 MPa 对比校准。"
    )

    contact = {"iso6336": c_iso}

    if run_hertz:
        try:
            contact["hertz"] = contact_stress_hertz(
                Ft=Ft, m=params.m, alpha=params.alpha,
                z1=params.z1, zs=params.zs, z2=params.z2,
                E1=E1, nu1=nu1, E2=E2, nu2=nu2,
            )
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Hertz 引擎计算失败：{exc!r}")

    if run_hefei:
        try:
            contact["hefei"] = hefei_simplified(
                m=params.m, z1=params.z1, zs=params.zs, z2=params.z2,
                alpha=params.alpha, b=geo.b, T1_Nmm=T1,
                E1=E1, nu1=nu1, E2=E2, nu2=nu2,
            )
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"何飞简化公式计算失败：{exc!r}")

    # ---------- 6. 弯曲应力 ----------
    # 计算对象：面齿轮（大轮）。其当量齿数为 z2。
    yfys = yf_ys_approx(
        z=params.z2, alpha_deg=params.alpha_deg, x=params.x2, YF=YF, YS=YS
    )
    if yfys.source == "approx":
        warnings.append(yfys.note)

    b_f = geo.b_eff
    b_iso = bending_stress_iso6336(
        Ft=Ft, b=b_f, m=params.m,
        YF=yfys.YF, YS=yfys.YS,
        eps_alpha=geo.eps_alpha, lf=lf,
    )
    # 面齿轮齿体修正系数 K_face。
    # GB/T 3480 / ISO 6336 的弯曲公式前提是"轮缘厚度 >= 3.5·m_n"的刚性
    # 轮缘；面齿轮是薄盘轮体，该前提不满足，轮缘柔度会使齿根实际应力
    # 高于当量齿轮计算值（lit-scout 文献核查结论）。
    # 因此 K_face 默认取 1.0（不做折减），若做轮体柔度评估可调大（1.0~1.4）。
    sigma_F_face = b_iso["sigma_F"] * K_face
    b_iso["sigma_F_equivalent_spur"] = b_iso["sigma_F"]
    b_iso["sigma_F"] = sigma_F_face
    b_iso["K_face"] = K_face
    if abs(K_face - 1.0) > 1e-9:
        b_iso["face_correction"] = (
            f"已乘齿体/轮体修正系数 K_face={K_face:.2f}；"
            "当量直齿圆柱齿轮原始值见 sigma_F_equivalent_spur。"
        )
    else:
        b_iso["face_correction"] = (
            "未做轮体修正（K_face=1.0）。注意：GB/T 3480 弯曲公式要求"
            "轮缘厚 ≥ 3.5·m_n，面齿轮薄盘轮体不满足该前提，实际齿根应力"
            "可能更高，建议用有限元复核或取 K_face=1.1~1.4。"
        )

    bending = {"iso6336": b_iso, "YF_source": yfys.source}

    # ---------- 7. 安全系数 ----------
    safety = check_safety(
        sigma_H=c_iso["sigma_H"], sigma_F=b_iso["sigma_F"],
        allow=allow, S_H_min=S_H_min, S_F_min=S_F_min, reliability=reliability,
    )
    warnings.extend(safety.notes)
    warnings.extend(allow.notes)

    # ---------- 汇总 ----------
    return SolveResult(
        params={
            "m": params.m, "z1": params.z1, "z2": params.z2,
            "zs": params.zs, "alpha_deg": params.alpha_deg,
            "gamma_deg": params.gamma_deg,
            "ha_star": params.ha_star, "c_star": params.c_star,
            "b": geo.b, "x1": params.x1, "x2": params.x2,
            "u": params.u,
        },
        geometry=geo.summary(),
        loads={
            "T1_Nmm": T1,
            "speed_rpm": op.speed_rpm,
            "power_kw": op.power_kw,
            "life_hours": op.life_hours,
            "v_pitch_m_s": v_pitch,
            "Ft_N": Ft,
            "Fn_N": Fn,
            "cycles": N_L,
            "load_factors": {
                "KA": lf.KA, "KV": lf.KV,
                "KHb": lf.KHb, "KFb": lf.KFb,
                "KHa": lf.KHa, "KFa": lf.KFa,
                "KH": lf.KH, "KF": lf.KF,
                "source": lf.source,
                "notes": lf.notes,
            },
        },
        stress={
            "contact_iso": c_iso,
            "contact_hertz": contact.get("hertz"),
            "contact_hefei": contact.get("hefei"),
            "bending_iso": b_iso,
            "allowable": {
                "sigma_H_allow": allow.sigma_H_allow,
                "sigma_F_allow": allow.sigma_F_allow,
                "Z_NT": allow.Z_NT, "Y_NT": allow.Y_NT, "Y_ST": allow.Y_ST,
            },
            "YF_YS": {
                "YF": yfys.YF, "YS": yfys.YS, "source": yfys.source,
            },
        },
        safety={
            "S_H": safety.S_H, "S_F": safety.S_F,
            "S_H_min": safety.S_H_min, "S_F_min": safety.S_F_min,
            "pass_H": safety.pass_H, "pass_F": safety.pass_F,
            "verdict": safety.verdict,
        },
        warnings=warnings,
    )
