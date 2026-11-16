# -*- coding: utf-8 -*-
"""示例 2：几何参数对弯曲应力的影响（复现文献趋势）

刘新胜(2016) 3.3.2 节的结论：
  * 模数增大 → 弯曲应力减小（幅值递减）
  * 压力角增大 → 弯曲应力减小
  * 传动比增大 → 弯曲应力减小
  且三者中**模数影响最大、传动比次之、压力角最小**。

运行::

    python examples/02_parameter_sweep.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from facegear import FaceGearParams, OperatingConditions, solve


BASE = dict(alpha_deg=20.0, ha_star=1.0, c_star=0.25)


def one(**kw) -> dict:
    p = FaceGearParams(**{**BASE, **kw})
    op = OperatingConditions(speed_rpm=1000.0, torque_nm=500.0)
    r = solve(p, op, sigma_H_lim=1500.0, sigma_F_lim=480.0)
    return {
        "sigma_H": r.stress["contact_iso"]["sigma_H"],
        "sigma_F": r.stress["bending_iso"]["sigma_F"],
        "eps": r.geometry["mesh"]["eps_alpha"],
    }


def sweep(name: str, values, **fixed) -> None:
    print(f"\n--- {name} ---")
    print(f"{'值':>8} {'σH (MPa)':>12} {'σF (MPa)':>12} {'εα':>8}")
    base = None
    for v in values:
        kw = dict(fixed)
        kw[name] = v
        r = one(**kw)
        if base is None:
            base = r
        print(f"{v:>8.2f} {r['sigma_H']:>12.1f} {r['sigma_F']:>12.1f} "
              f"{r['eps']:>8.3f}")


def main() -> None:
    print("=" * 56)
    print("几何参数敏感度（z1=25, z2=100, b=40, T=500 N·m）")
    print("=" * 56)

    sweep("m", [3, 4, 5, 6, 8],
          z1=25, z2=100, b=40)

    sweep("alpha_deg", [17.5, 20, 22.5, 25, 27.5],
          m=4, z1=25, z2=100, b=40)

    sweep("z2", [50, 75, 100, 150, 200],
          m=4, z1=25, b=40)

    print("\n" + "=" * 64)
    print("与刘新胜(2016) 3.3.2 节结论的对照：")
    print("  ✓ 模数 ↑ → σF ↓（影响最大，235.8→39.0 MPa）")
    print("  ✓ 传动比 ↑ → σF ↓（影响次之，145.6→130.0 MPa）")
    print("  ✗ 压力角 ↑ → σF 在本模型中略升（132.5→136.6 MPa）")
    print()
    print("  压力角趋势不一致的原因：")
    print("  σF ∝ YF·YS·Yε。压力角增大使 YF 减小（齿根变厚），但端面重合度")
    print("  εα 同时减小，使 Yε = 0.25+0.75/εα 增大。本模型中后者占优。")
    print("  文献（刘新胜 图3.5）给出'压力角 ↑ → σF 均匀下降'，说明真实齿形")
    print("  系数随压力角的变化比本软件的线性近似更陡。若要准确复现压力角")
    print("  效应，请按 ISO 6336-3 图 11 查图并通过 YF= 传入。")
    print("=" * 64)


if __name__ == "__main__":
    main()
