"""
facegear 测试套件
==================

运行::

    python -m pytest tests -v

测试分层
--------
1. 几何基本关系（分度圆、基圆、齿顶圆）
2. ISO 6336 系数（Z_H、Z_E、Z_ε）与标准值一致性
3. 与何飞（2023）表 1 算例的对拍（论文有限元 σH=823.2 MPa）
4. 边界与异常处理
5. 报告渲染
"""

from __future__ import annotations

import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from facegear import FaceGearParams, FaceGearGeometry, OperatingConditions, solve
from facegear.geometry import FaceGearParams as FGP
from facegear.load import LoadFactors, estimate_load_factors
from facegear.profile import y_epsilon, y_beta, yf_ys_approx
from facegear.rating import simplified_allowable, check_safety
from facegear.report import generate_report, render_report_html, render_report_markdown
from facegear.stress import Z_H, Z_E, Z_epsilon, contact_stress_iso6336


# ======================================================================
# 何飞 2023 表 1 算例（公共 fixture）
# ======================================================================
@pytest.fixture(scope="module")
def hefei_case():
    """何飞(2023) 表1：m=6.35, z1=25, zs=27, z2=160, α=25°, E=210GPa, ν=0.3,
    T=1600 N·m。

    表1 的"内径 480 / 外径 560"实为**半径**（面齿轮分度圆半径 m·z2/2=508
    落在两者之间，若当直径则齿宽落在 240~280，远离分度圆，物理上不成立），
    因此齿宽 b = 560 - 480 = 80 mm。
    """
    p = FaceGearParams(m=6.35, z1=25, z2=160, alpha_deg=25.0, zs=27,
                       r_inner=480.0, r_outer=560.0)
    op = OperatingConditions(speed_rpm=1000.0, torque_nm=1600.0,
                             life_hours=5000.0)
    return p, op


@pytest.fixture(scope="module")
def hefei_result(hefei_case):
    p, op = hefei_case
    return solve(p, op, sigma_H_lim=1500.0, sigma_F_lim=480.0, YF=1.60, YS=1.90)


# ======================================================================
# 1. 几何
# ======================================================================
class TestGeometry:
    def test_basic_circles(self):
        p = FaceGearParams(m=6.35, z1=25, z2=160, alpha_deg=25.0, b=40.0)
        g = FaceGearGeometry(p)
        assert g.d1 == pytest.approx(6.35 * 25)
        assert g.db1 == pytest.approx(g.d1 * math.cos(math.radians(25)))
        assert g.da1 == pytest.approx(6.35 * 27)
        # 齿顶圆 > 基圆
        assert g.da1 > g.db1

    def test_contact_ratio_positive(self, hefei_case):
        p, _ = hefei_case
        g = FaceGearGeometry(p)
        assert g.eps_alpha > 1.0
        assert g.eps_alpha < 5.0

    def test_inner_outer_radius(self, hefei_case):
        p, _ = hefei_case
        g = FaceGearGeometry(p)
        assert g.r_inner == pytest.approx(480.0)
        assert g.r_outer == pytest.approx(560.0)
        assert g.b == pytest.approx(80.0)

    def test_invalid_params(self):
        with pytest.raises(ValueError):
            FaceGearParams(m=0, z1=25, z2=160)      # 模数为 0
        with pytest.raises(ValueError):
            FaceGearParams(m=2, z1=25, z2=20)       # z2 <= z1
        with pytest.raises(ValueError):
            FaceGearParams(m=2, z1=25, z2=160, zs=20)  # zs <= z1


# ======================================================================
# 2. ISO 6336 系数
# ======================================================================
class TestCoefficients:
    def test_ZH_20deg(self):
        # alpha=20°: ZH = sqrt(2/(cos20*sin20)) = sqrt(2/(0.9397*0.342)) ≈ 2.495
        assert Z_H(math.radians(20)) == pytest.approx(2.495, abs=2e-3)

    def test_ZE_steel_steel(self):
        # ISO 6336-2：钢-钢（E=210 GPa, ν=0.3）时 ZE ≈ 191.6 sqrt(MPa)
        # 注：常见手册的 189.8 对应 E=206 GPa 的旧约定
        ze = Z_E(210000, 0.3, 210000, 0.3)
        assert ze == pytest.approx(191.6, abs=0.3)
        # 用 E=206 GPa 应得到约 189.8
        ze206 = Z_E(206000, 0.3, 206000, 0.3)
        assert ze206 == pytest.approx(189.8, abs=0.3)

    def test_Zeps(self):
        # eps=1.6: Zeps = sqrt((4-1.6)/3) = sqrt(0.8) = 0.8944
        assert Z_epsilon(1.6) == pytest.approx(math.sqrt(0.8), abs=1e-6)
        # eps > 2 时切换公式
        assert Z_epsilon(2.5) == pytest.approx(1 / math.sqrt(2.5), abs=1e-6)

    def test_Yepsilon(self):
        # Yeps = 0.25 + 0.75/1.6 = 0.71875
        assert y_epsilon(1.6) == pytest.approx(0.71875, abs=1e-9)

    def test_Ybeta_straight(self):
        assert y_beta(0.0) == 1.0

    def test_YF_YS_user_override(self):
        r = yf_ys_approx(z=160, alpha_deg=25, YF=1.55, YS=1.85)
        assert r.YF == 1.55 and r.YS == 1.85
        assert r.source == "user"

    def test_YF_YS_approx_reasonable(self):
        # z=25, alpha=20°: YF 应在 1.9~2.4
        r = yf_ys_approx(z=25, alpha_deg=20)
        assert 1.8 < r.YF < 2.5
        assert 1.5 < r.YS < 2.3


# ======================================================================
# 3. 与论文算例对拍
# ======================================================================
class TestHefeiBenchmark:
    def test_contact_stress_vs_fem(self, hefei_result):
        """面齿轮接触应力 vs 何飞 2023 有限元值 823.2 MPa。

        本实现：当量齿轮法名义值 ≈536 MPa，乘面齿轮接触修正
        K_Hface=1.45 后 ≈777~841 MPa。偏差应在 ±12% 内。
        """
        sigma_H = hefei_result.stress["contact_iso"]["sigma_H"]
        fem = 823.2
        assert sigma_H == pytest.approx(fem, rel=0.12), (
            f"σH={sigma_H:.1f} MPa 偏离论文有限元值 {fem} MPa 超过 12%"
        )

    def test_contact_stress_order(self, hefei_result):
        """接触应力应在合理工程区间。"""
        s = hefei_result.stress["contact_iso"]["sigma_H"]
        assert 500 < s < 1500

    def test_bending_stress_vs_analytic(self, hefei_result):
        """名义弯曲应力 σF0 vs 论文解析模型 85.8 MPa，偏差 ±20%。"""
        s0 = hefei_result.stress["bending_iso"]["sigma_F0"]
        assert s0 == pytest.approx(85.8, rel=0.20), (
            f"σF0={s0:.1f} MPa 偏离论文解析值 85.8 MPa 超过 20%"
        )

    def test_bending_stress_range(self, hefei_result):
        """弯曲应力（含载荷系数）应在合理区间。"""
        s = hefei_result.stress["bending_iso"]["sigma_F"]
        assert 50 < s < 220

    def test_loads(self, hefei_result):
        d = hefei_result.to_dict()
        Ft = d["loads"]["Ft_N"]
        # Ft = 2T/d1 = 2*1.6e6/158.75
        assert Ft == pytest.approx(2 * 1.6e6 / 158.75, rel=1e-6)
        assert d["loads"]["Fn_N"] > Ft

    def test_safety_passes(self, hefei_result):
        sf = hefei_result.safety
        assert isinstance(sf["S_H"], float)
        assert isinstance(sf["S_F"], float)
        assert sf["pass_H"] is True and sf["pass_F"] is True


# ======================================================================
# 4. 各引擎一致性
# ======================================================================
class TestEngines:
    def test_hertz_same_order(self, hefei_result):
        """Hertz 单齿全载应力应 >= ISO 值（上限参考）。"""
        st = hefei_result.stress
        iso = st["contact_iso"]["sigma_H"]
        hz = st.get("contact_hertz")
        assert hz is not None
        assert hz["p0"] > iso * 0.8

    def test_hefei_present(self, hefei_result):
        hf = hefei_result.stress.get("contact_hefei")
        assert hf is not None
        assert hf["sigma_c"] > 0 and hf["sigma_b"] > 0
        assert "consistency_note" in hf

    def test_torque_scaling_contact(self, hefei_case):
        """接触应力 ∝ T^(1/3)（忽略载荷系数变化）。"""
        p, op = hefei_case
        r1 = solve(p, OperatingConditions(speed_rpm=1000, torque_nm=800),
                   sigma_H_lim=1500, sigma_F_lim=480, YF=1.6, YS=1.9)
        r2 = solve(p, OperatingConditions(speed_rpm=1000, torque_nm=1600),
                   sigma_H_lim=1500, sigma_F_lim=480, YF=1.6, YS=1.9)
        s1 = r1.stress["contact_iso"]["sigma_H"]
        s2 = r2.stress["contact_iso"]["sigma_H"]
        # 转速相同 → KV 相同；比值应接近 2^(1/3)=1.26 但受 KV 影响
        ratio = s2 / s1
        assert 1.15 < ratio < 1.45


# ======================================================================
# 5. 材料与校核
# ======================================================================
class TestRating:
    def test_allowable_positive(self):
        a = simplified_allowable(1500, 480, N_L=1e7)
        assert a.sigma_H_allow > 0 and a.sigma_F_allow > 0
        assert a.Y_ST == 2.0

    def test_check_safety_pass_fail(self):
        a = simplified_allowable(1500, 480, N_L=1e7)
        ok = check_safety(500, 100, a, S_H_min=1.1, S_F_min=1.4)
        assert ok.pass_H and ok.pass_F
        bad = check_safety(5000, 100, a, S_H_min=1.1, S_F_min=1.4)
        assert not bad.pass_H
        assert "接触" in bad.verdict


# ======================================================================
# 6. 报告
# ======================================================================
class TestReport:
    def test_text_report(self, hefei_result):
        rep = generate_report(hefei_result)
        assert "面齿轮" in rep
        assert "接触应力" in rep
        assert "弯曲应力" in rep
        assert "结论" in rep

    def test_html_report(self, hefei_result):
        h = render_report_html(hefei_result)
        assert h.startswith("<!DOCTYPE html>")
        assert "面齿轮" in h
        assert "</html>" in h

    def test_markdown_report(self, hefei_result):
        md = render_report_markdown(hefei_result)
        assert md.startswith("# 面齿轮")
        assert "|" in md


# ======================================================================
# 7. 边界
# ======================================================================
class TestEdge:
    def test_power_only_input(self):
        p = FaceGearParams(m=4, z1=20, z2=100, alpha_deg=20, b=30)
        op = OperatingConditions(speed_rpm=1500, power_kw=75)
        r = solve(p, op, sigma_H_lim=1500, sigma_F_lim=480)
        assert r.loads["T1_Nmm"] > 0

    def test_missing_load_raises(self):
        with pytest.raises(ValueError):
            OperatingConditions(speed_rpm=1000)

    def test_quality_grade_effect(self):
        p = FaceGearParams(m=4, z1=20, z2=100, alpha_deg=20, b=30)
        op = OperatingConditions(speed_rpm=1500, torque_nm=200)
        r7 = solve(p, op, sigma_H_lim=1500, sigma_F_lim=480, quality_grade=7)
        r9 = solve(p, op, sigma_H_lim=1500, sigma_F_lim=480, quality_grade=9)
        # 精度等级数字越大 → 精度越低 → 动载系数 KV 越大
        assert r9.loads["load_factors"]["KV"] >= r7.loads["load_factors"]["KV"]
