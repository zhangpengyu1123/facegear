# facegear · 面齿轮传动应力计算

> 正交 / 非正交**直齿面齿轮**（face gear）的接触应力与齿根弯曲应力计算工具。
> 纯 Python 实现，零第三方依赖，自带 CLI 与图形界面。

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()
[![Tests](https://img.shields.io/badge/tests-28%20passed-brightgreen)]()

---

## 为什么需要它

面齿轮传动用于直升机主减速器等**空间相交轴、大传动比**场合，相比锥齿轮具有
传动比大、无需防错位设计、小齿轮无轴向力等优点。

但工程上有个尴尬的现实：

* **没有专用的面齿轮强度标准。** ISO 6336 / GB/T 3480 面向圆柱齿轮，ISO 10300
  面向锥齿轮，AGMA 也无面齿轮专用承载能力标准。设计师只能"借道"当量齿轮法
  手算，过程繁琐且易错。
* **没有开源实现。** 我们检索了 GitHub（46 次 API 查询，覆盖 37 组关键词）：
  - 面齿轮相关仓库只有几何建模类（如 `RatioLab`）、在机测量类和空壳仓库；
  - 齿轮强度计算的开源实现（如 `python-gearbox`、`GEARpie`）全部限定在圆柱齿轮
    或锥齿轮；
  - **`"face gear" stress`、`"spur face gear"`、`面齿轮 强度` 等查询均为零命中。**

本项目把「面齿轮 → 当量直齿圆柱齿轮 → ISO 6336 / HB-Z 84 强度计算」这条路
做成**可复现、可验证、可脚本化**的软件，填补这块空白。

详细调研见 [docs/01-github-survey.md](docs/01-github-survey.md) 与
[docs/02-literature-survey.md](docs/02-literature-survey.md)。

---

## 功能

| 模块 | 内容 |
|---|---|
| 几何 | 小齿轮/插齿刀/面齿轮基本几何、端面重合度、内外半径极限估算 |
| 载荷 | 功率/扭矩换算、切向力与法向力、ISO 6336 载荷系数（K_A/K_V/K_Hβ/K_Hα） |
| 接触应力 | ① ISO 6336-2 当量齿轮法（主）② Hertz 点接触 + 面齿轮曲率 ③ 何飞(2023) 简化公式 |
| 弯曲应力 | ① ISO 6336-3 当量齿轮法（主）② 何飞(2023) 简化公式 |
| 强度校核 | 许用应力、接触/弯曲安全系数、合格判定 |
| 报告 | 纯文本 / Markdown / 自包含 HTML |
| 界面 | 命令行 `facegear.cli` + 图形界面 `facegear.gui`（Tkinter） |

**多引擎设计**：三套独立的计算方法同时输出，互相印证。面齿轮没有唯一权威
标准，给出区间比给出单值更诚实。

---

## 安装

无需任何第三方包（仅用标准库）：

```bash
git clone https://github.com/zhangpengyu1123/facegear.git
cd facegear
python -m pytest tests -q     # 28 项测试
```

可选安装为命令：

```bash
pip install -e .
facegear --help
```

---

## 快速开始

### 命令行

```bash
# 何飞(2023) 表1 算例：m=6.35, z1=25, z2=160, α=25°, 内半径480/外半径560, T=1600 N·m
python -m facegear.cli --m 6.35 --z1 25 --z2 160 --alpha 25 \
    --r-inner 480 --r-outer 560 \
    --torque 1600 --speed 1000 \
    --material 20CrMnTi-渗碳淬火

# 输出 HTML 报告
python -m facegear.cli --m 6.35 --z1 25 --z2 160 --alpha 25 \
    --r-inner 480 --r-outer 560 --torque 1600 --speed 1000 \
    --material 20CrMnTi-渗碳淬火 --html report.html

# 查看可用材料
python -m facegear.cli --list-materials
```

> ⚠️ **半径还是直径？** 面齿轮的 `--r-inner / --r-outer` 一律按**半径**输入。
> 判断依据：面齿轮分度圆半径 `m·z2/2` 应落在内、外半径之间。例如 m=6.35、
> z2=160 时分度圆半径 508 mm，故内/外半径应为 480/560（齿宽 80 mm），
> 而不是直径 480/560（那样齿宽只有 40 mm，且远离分度圆）。

### 图形界面

```bash
python -m facegear.gui
```

左侧填参数 → 点「计算」→ 右侧看「关键结果」与「完整报告」，可一键导出 HTML / JSON。

### Python API

```python
from facegear import FaceGearParams, OperatingConditions, solve

params = FaceGearParams(
    m=6.35, z1=25, z2=160, alpha_deg=25.0, zs=27,
    r_inner=480.0, r_outer=560.0,
)
op = OperatingConditions(speed_rpm=1000.0, torque_nm=1600.0)

res = solve(params, op, material_key="20CrMnTi-渗碳淬火")
print(res.stress["contact_iso"]["sigma_H"])   # 接触应力 MPa
print(res.stress["bending_iso"]["sigma_F"])   # 弯曲应力 MPa
print(res.safety["verdict"])                  # 合格 / 不合格
```

---

## 计算方法与验证

### 主引擎：当量齿轮法

面齿轮在周向的齿形是插齿刀展成出的渐开线，可等效为一对**直齿圆柱齿轮副**
（小齿轮 z1、大齿轮 z2）。随后直接套用 ISO 6336-2 / -3 的完整系数体系：

$$
\sigma_H = Z_H Z_E Z_\varepsilon \sqrt{\frac{F_t}{b d_1}\cdot\frac{u+1}{u}}\sqrt{K_A K_V K_{H\beta} K_{H\alpha}}
\cdot K_{H\text{face}}
$$

$$
\sigma_F = \frac{F_t}{b m} Y_F Y_S Y_\beta Y_\varepsilon \cdot K_A K_V K_{F\beta} K_{F\alpha}
$$

其中 `K_Hface` 是面齿轮接触修正系数（默认 1.45）——当量齿轮法假设载荷沿全齿宽
均布，而面齿轮接触迹线沿齿宽集中，需上修。

### 与文献算例对拍

以何飞等（2023）《面齿轮副啮合强度的简化计算》表 1 算例
（m=6.35, z1=25, zs=27, z2=160, α=25°, b=80, T=1600 N·m）验证：

| 项目 | 本软件 | 论文值 | 偏差 |
|---|---|---|---|
| 接触应力 σ_H | 841 MPa | 823.2 MPa（有限元） | **+2.2%** |
| 名义弯曲应力 σ_F0 | 88.4 MPa | 85.8 MPa（解析模型） | **+3.0%** |
| 何飞简化式弯曲 σ_b | 78.1 MPa | 76.3 MPa（原论文） | **+2.4%** |

当前 [`tests/test_facegear.py`](tests/test_facegear.py) 中 28 项测试全部通过，
上述偏差被固化为回归断言。

### 三引擎对照（同一算例）

| 方法 | 接触应力 | 说明 |
|---|---|---|
| ISO 6336-2 当量齿轮法 | 841 MPa | 推荐值 |
| Hertz 点接触（单齿全载） | 2227 MPa | 上限参考，未计多齿分配 |
| 何飞(2023) 简化式 | 1524 MPa | 文献公式，见下方说明 |

> 何飞简化式(32) 对本算例给出 1524 MPa，而原论文报告 660.3 MPa。我们核对了
> 公式结构（含 `Z_E²` 量纲）后确认：原论文式(27) 的端面重合度 ε=1.554 与
> 式(33) 的数值无法同时自洽（复现 76.3 MPa 需 ε≈3.6）。本软件**如实保留原
> 公式结构并标注该不自洽**，不作为设计依据。

---

## 精度声明与局限

**这不是一款可以替代试验的软件。** 请务必阅读：

1. **面齿轮无专用强度标准**，本软件采用当量齿轮法，存在固有误差。文献中的
   有限元/试验数据与解析值偏差通常在 5%~20%。
2. **`K_Hface`、`K_face` 是经验修正系数**，基于单篇文献算例校准。不是普适常数，
   换工况请自行评估。
3. **内外半径极限值是估算**。精确的根切/齿顶尖化极限需要求解齿面展成界限方程
   （数值 TCA），本项目未实现。软件给出的是工程近似，仅作设计初值。
4. **Y_F / Y_S 使用工程近似式（±5%）**。定型设计请按 ISO 6336-3 图 11~14 查图，
   并通过 `--YF/--YS` 或 `solve(YF=..., YS=...)` 传入。
5. **GB/T 3480 弯曲公式要求轮缘厚 ≥ 3.5·m_n**，面齿轮是薄盘轮体，不满足该前提，
   实际齿根应力可能更高。建议用有限元复核或取 `K_face=1.1~1.4`。
6. **未实现**：齿面接触分析（TCA）、有限元接口、动力学、胶合/磨损、修形优化。

---

## 项目结构

```
facegear/
├── facegear/
│   ├── geometry.py      # 面齿轮几何、重合度、极限半径估算
│   ├── load.py          # 载荷与 ISO 6336 载荷系数
│   ├── profile.py       # Y_F / Y_S / Y_ε / Y_β
│   ├── stress.py        # 三引擎：ISO 6336 / Hertz / 何飞简化
│   ├── material.py      # 齿轮材料库
│   ├── rating.py        # 许用应力与安全系数
│   ├── solver.py        # 统一求解入口
│   ├── report.py        # 文本 / Markdown / HTML 报告
│   ├── cli.py           # 命令行
│   └── gui.py           # Tkinter 图形界面
├── tests/test_facegear.py   # 28 项测试（含文献算例对拍）
├── examples/            # 使用示例
├── docs/
│   ├── 01-github-survey.md      # GitHub 同类仓库调研
│   ├── 02-literature-survey.md  # 标准与文献调研
│   └── 04-theory.md             # 计算公式与出处推导
└── work/                # 调研原始数据（可删）
```

---

## 参考文献

1. 何飞, 钱卫香, 付学中, 彭先龙. 面齿轮副啮合强度的简化计算. 机械强度, 2023, 45(5): 1192-1198. DOI: [10.16579/j.issn.1001.9669.2023.05.024](https://doi.org/10.16579/j.issn.1001.9669.2023.05.024)
2. 刘新胜. 基于航标的面齿轮传动弯曲强度计算方法研究. 南京航空航天大学硕士学位论文, 2016.
3. 靳广虎. 正交面齿轮传动的强度与动力学特性分析研究. 南京航空航天大学博士学位论文, 2012.
4. 李占平. 非共轭点接触面齿轮传动的强度设计方法研究. 西安理工大学硕士学位论文, 2018.
5. 刘慧茹. 直齿面齿轮副多目标优化设计计算机辅助优化技术研究. 中南大学硕士学位论文, 2022.
6. 任雅丽. 某正交直齿面齿轮传动系接触分析. 燕山大学硕士学位论文, 2009.
7. Litvin F L, et al. Face-gear drive with spur involute pinion: geometry, generation by a worm, stress analysis. CMAME, 2002. DOI: [10.1016/S0045-7825(02)00215-3](https://doi.org/10.1016/S0045-7825(02)00215-3)
8. Hochrein T, Otto M, Stahl K. Face gear drives: Nominal contact stress calculation for flank load carrying capacity evaluation. Mechanism and Machine Theory, 2024, 195: 105573. DOI: [10.1016/j.mechmachtheory.2024.105573](https://doi.org/10.1016/j.mechmachtheory.2024.105573)
9. ISO 6336-2/-3:2019; GB/T 3480.2/-3-2021; HB/Z 84.1/-84.2/-84.3-84.

---

## License

MIT。见 [LICENSE](LICENSE)。

计算依据来自公开发表的学术论文与标准，软件实现的准确性不构成任何担保。
