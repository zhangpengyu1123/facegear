"""
报告生成
==========

把 ``SolveResult`` 渲染为：

* 纯文本报告（控制台 / 日志）
* HTML 报告（可存档、可打印）
* Markdown 报告

设计目标：不依赖第三方库即可产出可读报告；若安装了 matplotlib，
可额外生成应力对比图。
"""

from __future__ import annotations

import datetime
import html
import json
import math
import os
from typing import Optional

__all__ = [
    "generate_report",
    "render_report_html",
    "render_report_markdown",
    "to_json",
]

_FORMULA_SOURCES = {
    "contact_iso": "ISO 6336-2 / GB/T 3480.2（当量直齿圆柱齿轮副）",
    "bending_iso": "ISO 6336-3 / GB/T 3480.3（当量直齿圆柱齿轮副）",
    "contact_hertz": "赫兹点接触理论 + 何飞(2023) 面齿轮曲率公式",
    "contact_hefei": "何飞等(2023) 简化公式式(27)(29)~(33)",
}


def _fmt(x: Optional[float], nd: int = 3) -> str:
    if x is None:
        return "—"
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x):
            return "—"
        return f"{x:.{nd}f}"
    return str(x)


def to_json(result) -> str:
    """序列化为 JSON 字符串。"""
    return json.dumps(result.to_dict(), ensure_ascii=False, indent=2, default=str)


def generate_report(result) -> str:
    """生成纯文本报告。"""
    d = result.to_dict()
    p, g, ld, st, sf = d["params"], d["geometry"], d["loads"], d["stress"], d["safety"]
    lines: list[str] = []
    A = lines.append

    A("=" * 74)
    A("面齿轮传动应力计算报告".center(64))
    A("facegear v0.1.0".center(64))
    A("=" * 74)
    A(f"生成时间：{datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
    A("")

    A("─" * 74)
    A("一、设计参数")
    A("─" * 74)
    A(f"  模数 m                     : {_fmt(p['m'])} mm")
    A(f"  小齿轮齿数 z1              : {p['z1']}")
    A(f"  插齿刀齿数 zs              : {p['zs']}")
    A(f"  面齿轮齿数 z2              : {p['z2']}")
    A(f"  压力角 α                   : {_fmt(p['alpha_deg'], 1)} °")
    A(f"  轴交角 γ                   : {_fmt(p['gamma_deg'], 1)} °")
    A(f"  齿顶高系数 ha*             : {_fmt(p['ha_star'], 2)}")
    A(f"  顶隙系数 c*                : {_fmt(p['c_star'], 2)}")
    A(f"  齿宽 b                     : {_fmt(p['b'])} mm")
    A(f"  传动比 u = z2/z1           : {_fmt(p['u'], 3)}")
    A("")

    A("─" * 74)
    A("二、几何计算结果")
    A("─" * 74)
    pin = g["pinion"]
    A(f"  小齿轮分度圆 d1            : {_fmt(pin['d1_mm'])} mm")
    A(f"  小齿轮基圆  db1            : {_fmt(pin['db1_mm'])} mm")
    A(f"  小齿轮齿顶圆 da1           : {_fmt(pin['da1_mm'])} mm")
    A(f"  小齿轮齿根圆 df1           : {_fmt(pin['df1_mm'])} mm")
    fg = g["face_gear"]
    A(f"  面齿轮内半径 r_in          : {_fmt(fg['r_inner_mm'])} mm")
    A(f"  面齿轮外半径 r_out         : {_fmt(fg['r_outer_mm'])} mm")
    A(f"  面齿轮分度圆半径 r_fp      : {_fmt(fg['r_fp_mm'])} mm")
    A(f"  内半径极限（估算）         : {_fmt(fg['r_inner_limit_est_mm'])} mm")
    A(f"  外半径极限（估算）         : {_fmt(fg['r_outer_limit_est_mm'])} mm")
    msh = g["mesh"]
    A(f"  端面重合度 εα              : {_fmt(msh['eps_alpha'])}")
    A("")

    A("─" * 74)
    A("三、载荷")
    A("─" * 74)
    A(f"  输入扭矩 T1                : {_fmt(ld['T1_Nmm'] / 1000.0, 2)} N·m")
    A(f"  转速 n1                    : {_fmt(ld['speed_rpm'], 1)} r/min")
    A(f"  节线速度 v                 : {_fmt(ld['v_pitch_m_s'])} m/s")
    A(f"  切向力 Ft                  : {_fmt(ld['Ft_N'], 1)} N")
    A(f"  法向力 Fn                  : {_fmt(ld['Fn_N'], 1)} N")
    lf = ld["load_factors"]
    A(f"  载荷系数 KA / KV           : {_fmt(lf['KA'], 2)} / {_fmt(lf['KV'], 3)}")
    A(f"  KHβ / KHα                  : {_fmt(lf['KHb'], 3)} / {_fmt(lf['KHa'], 3)}")
    A(f"  综合 KH / KF               : {_fmt(lf['KH'], 3)} / {_fmt(lf['KF'], 3)}")
    A("")

    A("─" * 74)
    A("四、应力计算结果")
    A("─" * 74)
    ci = st["contact_iso"]
    A(f"  [主] 接触应力 σH (ISO 6336)      : {_fmt(ci['sigma_H'], 1)} MPa")
    A(f"       其中 ZH={_fmt(ci['ZH'], 3)}, ZE={_fmt(ci['ZE'], 1)},"
      f" Zε={_fmt(ci['Zeps'], 3)}")
    if st.get("contact_hertz"):
        ch = st["contact_hertz"]
        A(f"  [参] 接触应力 p0 (Hertz)         : {_fmt(ch['p0'], 1)} MPa")
        A(f"       接触椭圆 a×b={_fmt(ch['a_axis'], 2)}×{_fmt(ch['b_axis'], 2)} mm,"
          f" 曲率比 B/A={_fmt(ch['k_ratio'], 3)}")
    if st.get("contact_hefei"):
        hf = st["contact_hefei"]
        A(f"  [文] 接触应力 σc (何飞2023)      : {_fmt(hf['sigma_c'], 1)} MPa")
        A(f"       εα={_fmt(hf['eps'], 3)}, A={_fmt(hf['A'], 4)}, B={_fmt(hf['B'], 4)}")
    A("")
    bi = st["bending_iso"]
    A(f"  [主] 弯曲应力 σF (ISO 6336)      : {_fmt(bi['sigma_F'], 1)} MPa")
    A(f"       其中 YF={_fmt(bi['YF'], 3)}, YS={_fmt(bi['YS'], 3)},"
      f" Yε={_fmt(bi['Yeps'], 3)}")
    A(f"       YF/YS 来源: {st['YF_YS']['source']}")
    if st.get("contact_hefei"):
        A(f"  [文] 弯曲应力 σb (何飞2023)      : {_fmt(st['contact_hefei']['sigma_b'], 1)} MPa")
    A("")

    A("─" * 74)
    A("五、强度校核")
    A("─" * 74)
    al = st["allowable"]
    A(f"  许用接触应力 σH,allow         : {_fmt(al['sigma_H_allow'], 1)} MPa")
    A(f"  许用弯曲应力 σF,allow         : {_fmt(al['sigma_F_allow'], 1)} MPa")
    A(f"  接触安全系数 S_H              : {_fmt(sf['S_H'], 3)}"
      f"  (要求 ≥ {_fmt(sf['S_H_min'], 2)})  "
      f"{'✓' if sf['pass_H'] else '✗'}")
    A(f"  弯曲安全系数 S_F              : {_fmt(sf['S_F'], 3)}"
      f"  (要求 ≥ {_fmt(sf['S_F_min'], 2)})  "
      f"{'✓' if sf['pass_F'] else '✗'}")
    A(f"  结论                          : {sf['verdict']}")
    A("")

    if d.get("warnings"):
        A("─" * 74)
        A("六、提示与警告")
        A("─" * 74)
        for w in d["warnings"]:
            A(f"  · {w}")
        A("")

    A("─" * 74)
    A("计算依据")
    A("─" * 74)
    for k, v in _FORMULA_SOURCES.items():
        A(f"  {k:16s}: {v}")
    A("")
    A("免责声明：本软件为工程辅助计算工具，计算结果不替代试验验证与")
    A("有限元校核。面齿轮尚无专用强度标准，采用当量齿轮法，存在固有误差。")
    A("=" * 74)
    return "\n".join(lines)


def render_report_markdown(result) -> str:
    """生成 Markdown 报告。"""
    d = result.to_dict()
    p, st, sf = d["params"], d["stress"], d["safety"]
    ci, bi = st["contact_iso"], st["bending_iso"]
    L = []
    L.append(f"# 面齿轮传动应力计算报告\n")
    L.append(f"*生成时间：{datetime.datetime.now():%Y-%m-%d %H:%M:%S}*\n")
    L.append("## 1. 设计参数\n")
    L.append("| 参数 | 数值 |")
    L.append("| --- | --- |")
    for k, v, u in [
        ("模数 m", p["m"], "mm"), ("小齿轮齿数 z1", p["z1"], ""),
        ("插齿刀齿数 zs", p["zs"], ""), ("面齿轮齿数 z2", p["z2"], ""),
        ("压力角 α", p["alpha_deg"], "°"), ("轴交角 γ", p["gamma_deg"], "°"),
        ("齿宽 b", p["b"], "mm"), ("传动比 u", p["u"], ""),
    ]:
        L.append(f"| {k} | {_fmt(v)} {u} |")
    L.append("")
    L.append("## 2. 应力结果\n")
    L.append("| 项目 | 数值 | 方法 |")
    L.append("| --- | --- | --- |")
    L.append(f"| 接触应力 σH | {_fmt(ci['sigma_H'], 1)} MPa | ISO 6336-2 |")
    if st.get("contact_hertz"):
        L.append(f"| 接触应力 p0 | {_fmt(st['contact_hertz']['p0'], 1)} MPa | Hertz |")
    if st.get("contact_hefei"):
        L.append(f"| 接触应力 σc | {_fmt(st['contact_hefei']['sigma_c'], 1)} MPa | 何飞2023 |")
    L.append(f"| 弯曲应力 σF | {_fmt(bi['sigma_F'], 1)} MPa | ISO 6336-3 |")
    if st.get("contact_hefei"):
        L.append(f"| 弯曲应力 σb | {_fmt(st['contact_hefei']['sigma_b'], 1)} MPa | 何飞2023 |")
    L.append("")
    L.append("## 3. 强度校核\n")
    L.append(f"- 接触安全系数 **S_H = {_fmt(sf['S_H'], 3)}**"
             f"（要求 ≥ {_fmt(sf['S_H_min'], 2)}）{'✅' if sf['pass_H'] else '❌'}")
    L.append(f"- 弯曲安全系数 **S_F = {_fmt(sf['S_F'], 3)}**"
             f"（要求 ≥ {_fmt(sf['S_F_min'], 2)}）{'✅' if sf['pass_F'] else '❌'}")
    L.append(f"- 结论：**{sf['verdict']}**")
    L.append("")
    if d.get("warnings"):
        L.append("## 4. 提示\n")
        for w in d["warnings"]:
            L.append(f"- {w}")
        L.append("")
    return "\n".join(L)


_HTML_CSS = """
body{font-family:"Segoe UI","Microsoft YaHei",sans-serif;max-width:960px;
  margin:32px auto;padding:0 20px;color:#1f2937;line-height:1.65;background:#fff}
h1{border-bottom:3px solid #2563eb;padding-bottom:10px;font-size:1.7em}
h2{margin-top:34px;color:#1e40af;font-size:1.25em;border-left:5px solid #2563eb;
  padding-left:10px}
table{border-collapse:collapse;width:100%;margin:14px 0;font-size:.94em}
th,td{border:1px solid #d1d5db;padding:7px 11px;text-align:left}
th{background:#eff6ff;font-weight:600}
tr:nth-child(even) td{background:#f9fafb}
.verdict{padding:14px 18px;border-radius:8px;font-size:1.1em;font-weight:600;
  margin:18px 0}
.pass{background:#dcfce7;border-left:6px solid #16a34a;color:#14532d}
.fail{background:#fee2e2;border-left:6px solid #dc2626;color:#7f1d1d}
.warn{background:#fef3c7;border-left:6px solid #f59e0b;padding:10px 14px;
  border-radius:6px;font-size:.92em;margin:8px 0}
.foot{margin-top:44px;padding-top:14px;border-top:1px solid #e5e7eb;
  font-size:.84em;color:#6b7280}
code{background:#f3f4f6;padding:1px 5px;border-radius:4px;font-size:.9em}
"""


def render_report_html(result, title: str = "面齿轮传动应力计算报告") -> str:
    """生成自包含 HTML 报告（不依赖外部资源）。"""
    d = result.to_dict()
    p, g = d["params"], d["geometry"]
    ld, st, sf = d["loads"], d["stress"], d["safety"]
    ci, bi = st["contact_iso"], st["bending_iso"]

    def row(k, v, unit=""):
        return f"<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))} {unit}</td></tr>"

    parts: list[str] = []
    A = parts.append
    A(f"<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>")
    A(f"<title>{html.escape(title)}</title><style>{_HTML_CSS}</style></head><body>")
    A(f"<h1>{html.escape(title)}</h1>")
    A(f"<p style='color:#6b7280'>facegear v0.1.0 · "
      f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}</p>")

    # 结论先给
    cls = "pass" if (sf["pass_H"] and sf["pass_F"]) else "fail"
    A(f"<div class='verdict {cls}'>结论：{html.escape(sf['verdict'])}<br>"
      f"<span style='font-size:.9em;font-weight:400'>"
      f"S_H = {_fmt(sf['S_H'], 3)}（要求 ≥ {_fmt(sf['S_H_min'], 2)}），"
      f"S_F = {_fmt(sf['S_F'], 3)}（要求 ≥ {_fmt(sf['S_F_min'], 2)}）</span></div>")

    A("<h2>1. 设计参数</h2><table>")
    for k, v, u in [
        ("模数 m", _fmt(p["m"]), "mm"), ("小齿轮齿数 z1", p["z1"], ""),
        ("插齿刀齿数 zs", p["zs"], ""), ("面齿轮齿数 z2", p["z2"], ""),
        ("压力角 α", _fmt(p["alpha_deg"], 1), "°"),
        ("轴交角 γ", _fmt(p["gamma_deg"], 1), "°"),
        ("齿顶高系数 ha*", _fmt(p["ha_star"], 2), ""),
        ("顶隙系数 c*", _fmt(p["c_star"], 2), ""),
        ("齿宽 b", _fmt(p["b"]), "mm"), ("传动比 u", _fmt(p["u"], 3), ""),
    ]:
        A(row(k, v, u))
    A("</table>")

    A("<h2>2. 几何与载荷</h2><table>")
    pin, fg, msh = g["pinion"], g["face_gear"], g["mesh"]
    for k, v, u in [
        ("小齿轮分度圆 d1", _fmt(pin["d1_mm"]), "mm"),
        ("小齿轮基圆 db1", _fmt(pin["db1_mm"]), "mm"),
        ("小齿轮齿顶圆 da1", _fmt(pin["da1_mm"]), "mm"),
        ("面齿轮内半径", _fmt(fg["r_inner_mm"]), "mm"),
        ("面齿轮外半径", _fmt(fg["r_outer_mm"]), "mm"),
        ("端面重合度 εα", _fmt(msh["eps_alpha"]), ""),
        ("输入扭矩 T1", _fmt(ld["T1_Nmm"] / 1000.0, 2), "N·m"),
        ("转速 n1", _fmt(ld["speed_rpm"], 1), "r/min"),
        ("节线速度 v", _fmt(ld["v_pitch_m_s"]), "m/s"),
        ("切向力 Ft", _fmt(ld["Ft_N"], 1), "N"),
        ("法向力 Fn", _fmt(ld["Fn_N"], 1), "N"),
    ]:
        A(row(k, v, u))
    A("</table>")

    A("<h2>3. 应力计算（多引擎对照）</h2><table>")
    A("<tr><th>项目</th><th>数值</th><th>方法</th><th>说明</th></tr>")
    A(f"<tr><td><b>接触应力 σH</b></td><td><b>{_fmt(ci['sigma_H'], 1)} MPa</b></td>"
      f"<td>ISO 6336-2</td><td>推荐值（当量齿轮法）</td></tr>")
    if st.get("contact_hertz"):
        ch = st["contact_hertz"]
        A(f"<tr><td>接触应力 p0</td><td>{_fmt(ch['p0'], 1)} MPa</td>"
          f"<td>Hertz</td><td>单齿全载上限参考</td></tr>")
    if st.get("contact_hefei"):
        hf = st["contact_hefei"]
        A(f"<tr><td>接触应力 σc</td><td>{_fmt(hf['sigma_c'], 1)} MPa</td>"
          f"<td>何飞2023</td><td>文献简化公式</td></tr>")
    A(f"<tr><td><b>弯曲应力 σF</b></td><td><b>{_fmt(bi['sigma_F'], 1)} MPa</b></td>"
      f"<td>ISO 6336-3</td><td>推荐值（当量齿轮法）</td></tr>")
    if st.get("contact_hefei"):
        A(f"<tr><td>弯曲应力 σb</td>"
          f"<td>{_fmt(st['contact_hefei']['sigma_b'], 1)} MPa</td>"
          f"<td>何飞2023</td><td>文献简化公式</td></tr>")
    A("</table>")
    A(f"<p style='font-size:.9em;color:#4b5563'>系数：ZH={_fmt(ci['ZH'], 3)}，"
      f"ZE={_fmt(ci['ZE'], 1)}，Zε={_fmt(ci['Zeps'], 3)}，"
      f"YF={_fmt(bi['YF'], 3)}，YS={_fmt(bi['YS'], 3)}，Yε={_fmt(bi['Yeps'], 3)}"
      f"（YF/YS 来源: {st['YF_YS']['source']}）</p>")

    A("<h2>4. 强度校核</h2><table>")
    A("<tr><th>项目</th><th>计算值</th><th>许用值</th><th>安全系数</th><th>判定</th></tr>")
    al = st["allowable"]
    A(f"<tr><td>接触强度</td><td>{_fmt(ci['sigma_H'], 1)} MPa</td>"
      f"<td>{_fmt(al['sigma_H_allow'], 1)} MPa</td>"
      f"<td>{_fmt(sf['S_H'], 3)}</td><td>{'通过' if sf['pass_H'] else '不通过'}</td></tr>")
    A(f"<tr><td>弯曲强度</td><td>{_fmt(bi['sigma_F'], 1)} MPa</td>"
      f"<td>{_fmt(al['sigma_F_allow'], 1)} MPa</td>"
      f"<td>{_fmt(sf['S_F'], 3)}</td><td>{'通过' if sf['pass_F'] else '不通过'}</td></tr>")
    A("</table>")

    if d.get("warnings"):
        A("<h2>5. 提示与警告</h2>")
        for w in d["warnings"]:
            A(f"<div class='warn'>{html.escape(str(w))}</div>")

    A("<h2>6. 计算依据与免责声明</h2><table>")
    for k, v in _FORMULA_SOURCES.items():
        A(row(k, v))
    A("</table>")
    A("<div class='foot'>本软件为工程辅助计算工具，结果不替代试验验证与有限元"
      "校核。面齿轮尚无专用强度标准，采用当量齿轮法，存在固有误差。"
      "面齿轮内外半径的极限值为估算，精确值须由齿面展成/TCA 或有限元确定。"
      "</div></body></html>")
    return "".join(parts)
