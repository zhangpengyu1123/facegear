"""
命令行界面
============

用法示例
--------
.. code-block:: bash

    # 最简：仅给几何与工况，用默认材料
    python -m facegear.cli --m 6.35 --z1 25 --z2 160 --alpha 25 --b 40 \\
        --torque 1600 --speed 1000

    # 指定材料并输出 HTML 报告
    python -m facegear.cli --m 6.35 --z1 25 --z2 160 --alpha 25 \\
        --r-inner 240 --r-outer 280 --torque 1600 --speed 1000 \\
        --material 20CrMnTi-渗碳淬火 --html out.html

    # 列出可用材料
    python -m facegear.cli --list-materials

    # 输出 JSON（便于脚本/批处理）
    python -m facegear.cli ... --json result.json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from . import __version__
from .geometry import FaceGearParams
from .load import OperatingConditions, LoadFactors
from .material import list_materials
from .report import generate_report, render_report_html, render_report_markdown, to_json
from .solver import solve


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="facegear",
        description="面齿轮传动应力计算（接触应力 / 齿根弯曲应力 / 强度校核）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--version", action="version", version=f"facegear {__version__}")

    g = p.add_argument_group("几何参数")
    g.add_argument("--m", type=float, help="模数 mm")
    g.add_argument("--z1", type=int, help="小齿轮齿数")
    g.add_argument("--z2", type=int, help="面齿轮齿数")
    g.add_argument("--zs", type=int, default=None,
                   help="插齿刀齿数（默认 z1+2）")
    g.add_argument("--alpha", type=float, default=25.0, help="压力角 °（默认 25）")
    g.add_argument("--gamma", type=float, default=90.0, help="轴交角 °（默认 90）")
    g.add_argument("--ha", type=float, default=1.0, help="齿顶高系数（默认 1.0）")
    g.add_argument("--c", type=float, default=0.25, help="顶隙系数（默认 0.25）")
    g.add_argument("--b", type=float, default=None, help="齿宽 mm")
    g.add_argument("--r-inner", type=float, default=None, help="面齿轮内半径 mm")
    g.add_argument("--r-outer", type=float, default=None, help="面齿轮外半径 mm")
    g.add_argument("--x1", type=float, default=0.0, help="小齿轮变位系数")
    g.add_argument("--x2", type=float, default=0.0, help="面齿轮当量变位系数")

    o = p.add_argument_group("工况")
    o.add_argument("--torque", type=float, default=None, help="输入扭矩 N·m")
    o.add_argument("--power", type=float, default=None, help="输入功率 kW")
    o.add_argument("--speed", type=float, default=1000.0, help="转速 r/min")
    o.add_argument("--life", type=float, default=5000.0, help="设计寿命 h")
    o.add_argument("--grade", type=int, default=7, help="精度等级（默认 7）")
    o.add_argument("--shock", action="store_true", help="载荷有冲击（默认平稳）")

    m = p.add_argument_group("材料与强度")
    m.add_argument("--material", type=str, default=None,
                   help="材料键名，如 20CrMnTi-渗碳淬火")
    m.add_argument("--sigma-h-lim", type=float, default=None,
                   help="接触疲劳极限 MPa（覆盖材料库）")
    m.add_argument("--sigma-f-lim", type=float, default=None,
                   help="弯曲疲劳极限 MPa（覆盖材料库）")
    m.add_argument("--YF", type=float, default=None, help="齿形系数（查图值）")
    m.add_argument("--YS", type=float, default=None, help="应力修正系数（查图值）")
    m.add_argument("--K-face", type=float, default=1.0,
                   help="轮体柔度修正系数（默认 1.0，可 1.1~1.4）")
    m.add_argument("--S-H-min", type=float, default=None, help="要求最小接触安全系数")
    m.add_argument("--S-F-min", type=float, default=None, help="要求最小弯曲安全系数")

    c = p.add_argument_group("载荷系数（覆盖自动估算）")
    c.add_argument("--KA", type=float, default=None)
    c.add_argument("--KV", type=float, default=None)
    c.add_argument("--KHb", type=float, default=None)
    c.add_argument("--KHa", type=float, default=None)

    out = p.add_argument_group("输出")
    out.add_argument("--json", type=str, default=None, help="输出 JSON 文件路径")
    out.add_argument("--html", type=str, default=None, help="输出 HTML 报告路径")
    out.add_argument("--md", type=str, default=None, help="输出 Markdown 报告路径")
    out.add_argument("--quiet", action="store_true", help="不打印文本报告")
    out.add_argument("--list-materials", action="store_true", help="列出可用材料后退出")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_materials:
        for m in list_materials():
            print(f"{m['key']:24s} σH,lim={m['sigma_H_lim']:6.0f} MPa  "
                  f"σF,lim={m['sigma_F_lim']:6.0f} MPa  {m['hardness']}")
        return 0

    # ---- 必需参数校验 ----
    missing = []
    if args.m is None:
        missing.append("--m")
    if args.z1 is None:
        missing.append("--z1")
    if args.z2 is None:
        missing.append("--z2")
    if args.torque is None and args.power is None:
        missing.append("--torque 或 --power")
    if missing:
        parser.error("缺少必需参数：" + ", ".join(missing))

    try:
        params = FaceGearParams(
            m=args.m, z1=args.z1, z2=args.z2,
            alpha_deg=args.alpha, zs=args.zs, gamma_deg=args.gamma,
            ha_star=args.ha, c_star=args.c,
            b=args.b, r_inner=args.r_inner, r_outer=args.r_outer,
            x1=args.x1, x2=args.x2,
        )
        op = OperatingConditions(
            speed_rpm=args.speed, power_kw=args.power,
            torque_nm=args.torque, life_hours=args.life,
        )

        lf_override = None
        if any(v is not None for v in (args.KA, args.KV, args.KHb, args.KHa)):
            lf_override = LoadFactors(
                KA=args.KA if args.KA is not None else 1.0,
                KV=args.KV if args.KV is not None else 1.1,
                KHb=args.KHb if args.KHb is not None else 1.1,
                KFb=(args.KHb if args.KHb is not None else 1.1) ** 0.85,
                KHa=args.KHa if args.KHa is not None else 1.0,
                KFa=args.KHa if args.KHa is not None else 1.0,
                source="user",
            )

        res = solve(
            params=params, op=op,
            material_key=args.material,
            sigma_H_lim=args.sigma_h_lim, sigma_F_lim=args.sigma_f_lim,
            quality_grade=args.grade, load_smooth=not args.shock,
            lf_override=lf_override,
            YF=args.YF, YS=args.YS,
            S_H_min=args.S_H_min, S_F_min=args.S_F_min,
            K_face=args.K_face,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[错误] {exc}", file=sys.stderr)
        return 2

    if not args.quiet:
        print(generate_report(res))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            f.write(to_json(res))
        print(f"[已写出] {args.json}", file=sys.stderr)
    if args.html:
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(render_report_html(res))
        print(f"[已写出] {args.html}", file=sys.stderr)
    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(render_report_markdown(res))
        print(f"[已写出] {args.md}", file=sys.stderr)

    # 退出码：0 合格，1 不合格
    return 0 if (res.safety["pass_H"] and res.safety["pass_F"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
