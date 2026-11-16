# -*- coding: utf-8 -*-
"""示例 1：何飞(2023) 表1 算例复现

运行::

    python examples/01_hefei_2023.py

对应论文：何飞, 钱卫香, 付学中, 彭先龙.
《面齿轮副啮合强度的简化计算》机械强度, 2023, 45(5): 1192-1198.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from facegear import FaceGearParams, OperatingConditions, solve
from facegear.report import generate_report, render_report_html


def main() -> None:
    # ---- 论文表 1 参数 ----
    # 注意：内径/外径 480/560 是**半径**（面齿轮分度圆半径 m*z2/2 = 508
    # 落在两者之间），故齿宽 b = 80 mm。
    params = FaceGearParams(
        m=6.35,          # 模数 mm
        z1=25,           # 小齿轮齿数
        z2=160,          # 面齿轮齿数
        zs=27,           # 插齿刀齿数（= z1 + 2）
        alpha_deg=25.0,  # 压力角
        r_inner=480.0,   # 面齿轮内半径 mm
        r_outer=560.0,   # 面齿轮外半径 mm
    )
    op = OperatingConditions(
        speed_rpm=1000.0,
        torque_nm=1600.0,
        life_hours=5000.0,
    )

    res = solve(
        params, op,
        material_key="20CrMnTi-渗碳淬火",
        YF=1.60, YS=1.90,   # 何飞图 4(b) α=25°、N1=25、i=6.4 查图值
    )

    # ---- 打印与论文的对比 ----
    ci = res.stress["contact_iso"]
    bi = res.stress["bending_iso"]
    print("=" * 62)
    print("何飞(2023) 表1 算例复现")
    print("=" * 62)
    print(f"接触应力 σH        = {ci['sigma_H']:7.1f} MPa   "
          f"[论文有限元 823.2 MPa, 偏差 {(ci['sigma_H']/823.2-1)*100:+.1f}%]")
    print(f"名义弯曲应力 σF0   = {bi['sigma_F0']:7.1f} MPa   "
          f"[论文解析 85.8 MPa, 偏差 {(bi['sigma_F0']/85.8-1)*100:+.1f}%]")
    hf = res.stress.get("contact_hefei")
    if hf:
        print(f"何飞简化式弯曲 σb  = {hf['sigma_b']:7.1f} MPa   "
              f"[论文 76.3 MPa, 偏差 {(hf['sigma_b']/76.3-1)*100:+.1f}%]")
    print(f"\n接触安全系数 S_H   = {res.safety['S_H']:.3f}"
          f"（要求 ≥ {res.safety['S_H_min']:.2f}）")
    print(f"弯曲安全系数 S_F   = {res.safety['S_F']:.3f}"
          f"（要求 ≥ {res.safety['S_F_min']:.2f}）")
    print(f"结论               = {res.safety['verdict']}")

    # ---- 完整文本报告 ----
    print()
    print(generate_report(res))

    # ---- 导出 HTML ----
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "examples_out")
    os.makedirs(out, exist_ok=True)
    html_path = os.path.abspath(os.path.join(out, "hefei2023_report.html"))
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(render_report_html(res))
    print(f"\nHTML 报告已写出：{html_path}")


if __name__ == "__main__":
    main()
