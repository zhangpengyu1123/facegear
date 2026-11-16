"""
图形界面（Tkinter，零额外依赖）
==================================

启动::

    python -m facegear.gui

界面布局
--------
* 左侧：参数输入（几何 / 工况 / 材料与强度）
* 右侧：计算结果（几何、应力、安全系数、提示）
* 底部：计算 / 导出 HTML / 导出 JSON / 重置

所有计算调用 :func:`facegear.solver.solve`，与 CLI 完全一致。
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Optional

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "当前 Python 未包含 tkinter，无法启动图形界面。\n"
        "请改用命令行：python -m facegear.cli --help\n"
        f"原始错误：{exc}"
    )

from .geometry import FaceGearParams
from .load import OperatingConditions, LoadFactors
from .material import list_materials
from .report import generate_report, render_report_html, to_json
from .solver import solve


FIELDS_GEOMETRY = [
    ("m", "模数 m (mm)", "6.35"),
    ("z1", "小齿轮齿数 z1", "25"),
    ("z2", "面齿轮齿数 z2", "160"),
    ("zs", "插齿刀齿数 zs（空=z1+2）", "27"),
    ("alpha", "压力角 α (°)", "25"),
    ("gamma", "轴交角 γ (°)", "90"),
    ("b", "齿宽 b (mm)", "40"),
    ("r_inner", "面齿轮内半径 (mm)", "240"),
    ("r_outer", "面齿轮外半径 (mm)", "280"),
]

FIELDS_OP = [
    ("torque", "输入扭矩 T (N·m)", "1600"),
    ("speed", "转速 n (r/min)", "1000"),
    ("power", "输入功率 P (kW，可选)", ""),
    ("life", "设计寿命 (h)", "5000"),
    ("grade", "精度等级", "7"),
]


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("面齿轮传动应力计算  ·  facegear v0.1.0")
        self.geometry("1180x780")
        self.minsize(980, 680)

        self._result = None
        self._entries: dict[str, tk.Entry] = {}
        self._mat_combo: Optional[ttk.Combobox] = None
        self._shock_var = tk.BooleanVar(value=False)
        self._kface_var = tk.StringVar(value="1.0")

        self._build_style()
        self._build_layout()

    # ------------------------------------------------------------------
    def _build_style(self) -> None:
        style = ttk.Style(self)
        for name in ("clam", "vista", "winnative", "default"):
            if name in style.theme_names():
                style.theme_use(name)
                break
        style.configure("Header.TLabel", font=("Microsoft YaHei", 13, "bold"))
        style.configure("Sub.TLabel", foreground="#555")
        style.configure("Result.TLabel", font=("Consolas", 10))
        style.configure("Big.TLabel", font=("Microsoft YaHei", 12, "bold"))
        style.configure("Ok.TLabel", foreground="#166534",
                        font=("Microsoft YaHei", 12, "bold"))
        style.configure("Bad.TLabel", foreground="#b91c1c",
                        font=("Microsoft YaHei", 12, "bold"))

    def _build_layout(self) -> None:
        outer = ttk.Frame(self, padding=10)
        outer.pack(fill="both", expand=True)

        left = ttk.Frame(outer)
        left.pack(side="left", fill="y", padx=(0, 10))
        right = ttk.Frame(outer)
        right.pack(side="left", fill="both", expand=True)

        # ------------- 左：输入 -------------
        ttk.Label(left, text="参数输入", style="Header.TLabel").pack(anchor="w")

        geo = ttk.LabelFrame(left, text="几何参数", padding=8)
        geo.pack(fill="x", pady=6)
        for i, (key, label, default) in enumerate(FIELDS_GEOMETRY):
            ttk.Label(geo, text=label).grid(row=i, column=0, sticky="w", pady=2)
            e = ttk.Entry(geo, width=14)
            e.insert(0, default)
            e.grid(row=i, column=1, padx=6, pady=2)
            self._entries[key] = e

        op = ttk.LabelFrame(left, text="工况", padding=8)
        op.pack(fill="x", pady=6)
        for i, (key, label, default) in enumerate(FIELDS_OP):
            ttk.Label(op, text=label).grid(row=i, column=0, sticky="w", pady=2)
            e = ttk.Entry(op, width=14)
            e.insert(0, default)
            e.grid(row=i, column=1, padx=6, pady=2)
            self._entries[key] = e
        ttk.Checkbutton(op, text="载荷有冲击（否则视为平稳）",
                        variable=self._shock_var).grid(
            row=len(FIELDS_OP), column=0, columnspan=2, sticky="w", pady=4)

        mat = ttk.LabelFrame(left, text="材料与强度", padding=8)
        mat.pack(fill="x", pady=6)
        ttk.Label(mat, text="材料").grid(row=0, column=0, sticky="w", pady=2)
        mats = list_materials()
        self._mat_combo = ttk.Combobox(
            mat, values=[m["key"] for m in mats], width=22, state="readonly")
        self._mat_combo.current(0)
        self._mat_combo.grid(row=0, column=1, padx=6, pady=2)

        ttk.Label(mat, text="轮体修正 K_face").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(mat, textvariable=self._kface_var, width=14).grid(
            row=1, column=1, padx=6, pady=2)

        ttk.Label(mat, text="（可选）YF / YS 查图值").grid(
            row=2, column=0, sticky="w", pady=2)
        yf_frame = ttk.Frame(mat)
        yf_frame.grid(row=2, column=1, padx=6, pady=2)
        self._entries["YF"] = ttk.Entry(yf_frame, width=6)
        self._entries["YF"].pack(side="left")
        ttk.Label(yf_frame, text=" / ").pack(side="left")
        self._entries["YS"] = ttk.Entry(yf_frame, width=6)
        self._entries["YS"].pack(side="left")

        btns = ttk.Frame(left)
        btns.pack(fill="x", pady=10)
        ttk.Button(btns, text="计  算", command=self.on_calc).pack(
            side="left", fill="x", expand=True, padx=2)
        ttk.Button(btns, text="导出 HTML", command=self.on_export_html).pack(
            side="left", fill="x", expand=True, padx=2)
        ttk.Button(btns, text="导出 JSON", command=self.on_export_json).pack(
            side="left", fill="x", expand=True, padx=2)

        # ------------- 右：结果 -------------
        ttk.Label(right, text="计算结果", style="Header.TLabel").pack(anchor="w")

        self._verdict_label = ttk.Label(right, text="尚未计算",
                                        style="Sub.TLabel")
        self._verdict_label.pack(anchor="w", pady=(4, 6))

        nb = ttk.Notebook(right)
        nb.pack(fill="both", expand=True)

        self._text_report = tk.Text(nb, wrap="none", font=("Consolas", 10))
        self._text_report.pack(fill="both", expand=True) if False else None
        f1 = ttk.Frame(nb)
        nb.add(f1, text="完整报告")
        sb = ttk.Scrollbar(f1, orient="vertical",
                           command=self._text_report.yview)
        self._text_report.configure(yscrollcommand=sb.set)
        self._text_report.pack(in_=f1, side="left", fill="both", expand=True)
        sb.pack(in_=f1, side="right", fill="y")

        f2 = ttk.Frame(nb)
        nb.add(f2, text="关键结果")
        self._key_text = tk.Text(f2, wrap="word", font=("Consolas", 10))
        self._key_text.pack(fill="both", expand=True)

        ttk.Label(right, text="说明：面齿轮尚无专用强度标准，本软件采用 ISO 6336 "
                              "当量齿轮法；结果不替代试验与有限元校核。",
                  style="Sub.TLabel", wraplength=700).pack(
            anchor="w", pady=(6, 0))

    # ------------------------------------------------------------------
    def _num(self, key: str) -> Optional[float]:
        s = self._entries[key].get().strip()
        return float(s) if s else None

    def _collect(self):
        p = FaceGearParams(
            m=self._num("m"), z1=int(self._num("z1")),
            z2=int(self._num("z2")),
            alpha_deg=self._num("alpha") or 25.0,
            zs=int(self._num("zs")) if self._num("zs") else None,
            gamma_deg=self._num("gamma") or 90.0,
            b=self._num("b"),
            r_inner=self._num("r_inner"),
            r_outer=self._num("r_outer"),
        )
        op = OperatingConditions(
            speed_rpm=self._num("speed") or 1000.0,
            torque_nm=self._num("torque"),
            power_kw=self._num("power"),
            life_hours=self._num("life") or 5000.0,
        )
        return p, op

    def on_calc(self) -> None:
        try:
            params, op = self._collect()
            mat_key = self._mat_combo.get() if self._mat_combo else None
            kface = float(self._kface_var.get() or 1.0)
            res = solve(
                params=params, op=op, material_key=mat_key,
                quality_grade=int(self._num("grade") or 7),
                load_smooth=not self._shock_var.get(),
                YF=self._num("YF"), YS=self._num("YS"),
                K_face=kface,
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("计算失败", f"{exc}\n\n{traceback.format_exc(limit=2)}")
            return

        self._result = res
        self._text_report.delete("1.0", "end")
        self._text_report.insert("1.0", generate_report(res))

        d = res.to_dict()
        ci = d["stress"]["contact_iso"]
        bi = d["stress"]["bending_iso"]
        sf = d["safety"]
        ch = d["stress"].get("contact_hertz")
        hf = d["stress"].get("contact_hefei")

        lines = [
            f"材料：{mat_key}",
            f"传动比 u = {d['params']['u']:.3f}    端面重合度 εα = "
            f"{d['geometry']['mesh']['eps_alpha']:.3f}",
            f"切向力 Ft = {d['loads']['Ft_N']:.1f} N    "
            f"节线速度 v = {d['loads']['v_pitch_m_s']:.2f} m/s",
            "",
            "── 应力 ──",
            f"接触应力 σH  (ISO 6336)  = {ci['sigma_H']:8.1f} MPa",
        ]
        if ch:
            lines.append(f"接触应力 p0  (Hertz)     = {ch['p0']:8.1f} MPa  (单齿全载上限)")
        if hf:
            lines.append(f"接触应力 σc  (何飞2023)  = {hf['sigma_c']:8.1f} MPa  (文献公式)")
        lines.append(f"弯曲应力 σF  (ISO 6336)  = {bi['sigma_F']:8.1f} MPa")
        if hf:
            lines.append(f"弯曲应力 σb  (何飞2023)  = {hf['sigma_b']:8.1f} MPa  (文献公式)")
        lines += [
            "",
            "── 强度校核 ──",
            f"许用接触应力 = {d['stress']['allowable']['sigma_H_allow']:.1f} MPa",
            f"许用弯曲应力 = {d['stress']['allowable']['sigma_F_allow']:.1f} MPa",
            f"接触安全系数 S_H = {sf['S_H']:.3f}  (要求 ≥ {sf['S_H_min']:.2f})  "
            f"{'通过' if sf['pass_H'] else '不通过'}",
            f"弯曲安全系数 S_F = {sf['S_F']:.3f}  (要求 ≥ {sf['S_F_min']:.2f})  "
            f"{'通过' if sf['pass_F'] else '不通过'}",
            "",
            f"结论：{sf['verdict']}",
        ]
        if d["warnings"]:
            lines += ["", "── 提示 ──"] + [f"· {w}" for w in d["warnings"]]

        self._key_text.delete("1.0", "end")
        self._key_text.insert("1.0", "\n".join(lines))

        ok = sf["pass_H"] and sf["pass_F"]
        self._verdict_label.configure(
            text=f"结论：{sf['verdict']}   |   S_H={sf['S_H']:.2f}   "
                 f"S_F={sf['S_F']:.2f}   |   σH={ci['sigma_H']:.1f} MPa",
            style="Ok.TLabel" if ok else "Bad.TLabel",
        )

    # ------------------------------------------------------------------
    def on_export_html(self) -> None:
        if self._result is None:
            messagebox.showinfo("提示", "请先点击「计算」")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML 报告", "*.html")],
            initialfile="facegear_report.html",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(render_report_html(self._result))
        messagebox.showinfo("完成", f"已导出：\n{path}")

    def on_export_json(self) -> None:
        if self._result is None:
            messagebox.showinfo("提示", "请先点击「计算」")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="facegear_result.json",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(to_json(self._result))
        messagebox.showinfo("完成", f"已导出：\n{path}")


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
