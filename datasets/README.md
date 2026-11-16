# 面齿轮应力计算软件 · 论文算例基准数据集（work/benchmarks）

本目录把 6 篇中文论文里**可复现的算例与系数**抽成结构化数据，供软件实现后做「对拍验证（golden test）」。
**所有数值来自论文原文 PDF**，每条都带 PDF 页码 / 表号 / 式号；由论文两个表反算得到的量显式标注 `derived: true`。

- `cases.json` —— 50 个算例（几何 + 工况 + 论文给出的应力值）
- `coefficients.json` —— 10 组系数表 / 公式链（YF、YS、Yε、YX、载荷系数、赫兹系数、齿宽系数修正等）
- `pages/` —— 关键页/表格的高清渲染 PNG（复核用，含 GUI 截图与公式原貌）
- `tools/` —— 生成与复核脚本（`build_cases.py`、`pagedump.py`、`render.py`）
- 测试设计（分级、容差）见 [`docs/05-test-cases.md`](../../docs/05-test-cases.md)

---

## 1. 单位约定

| 物理量 | 单位 | 说明 |
|---|---|---|
| 长度 / 半径 / 齿宽 / 模数 | **mm** | 与论文一致，不做 m 换算 |
| 力 | **N** | 含"法向载荷"、"压头静载"、"施加的载荷" |
| 力矩 / 转矩 | **N·m** | JSON 字段名统一 `_Nm`；正文公式内若需 N·mm 会注明 |
| 应力（接触/弯曲/许用） | **MPa** | |
| 弹性模量 | **MPa** | 论文常用 GPa 或 N/mm²，此处统一折算到 MPa |
| 功率 | **kW** | |
| 转速 | **r/min** | |
| 角度 | **°（度）** | 公式内三角函数按弧度计算 |
| 齿宽系数 | 无量纲 | `phi_b = b/m` |
| 啮合刚度 | N/(mm·µm) | 沿用论文单位 |

论文里出现的 `lb-in`、`ksi` 保留原值并在该字段注明换算（如何飞算例 1：7200 lb-in ≈ 813 N·m，275 ksi ≈ 1896.1 MPa）。

---

## 2. ★ 半径约定（最容易踩的坑）

**6 篇论文都把面齿轮的内/外半径写成"内径 / 外径"，但数值上必然是半径。**
本数据集一律按**半径（mm）**存储。三条独立证据（均可复核）：

| 论文 | 内外"径" | 齿宽 | 校验 | 位置 |
|---|---|---|---|---|
| 刘新胜 2016 | 93.9681 / 112.779 | 18.8112 | 差 = 18.8109 ✓ | 图6.3，PDF p69 |
| 任雅丽 2009 | 471 / 559 | 88 | 差 = 88 ✓ | 表2-1，PDF p27 |
| 何飞 2023 | 480 / 560 | 80（未给，反推） | 差 = 80，且 ρ₂ = m·z₂/2 = 508 ∈ (480,560) ✓ | 表1，PDF p5 |

配套规律：**面齿轮分度圆半径 `r_p2 = m·z2/2`，工作齿宽 `b = 外半径 − 内半径`**（刘新胜图6.3 中 `r_p2 = 100 = 4×50/2` 直接给出，可视为定标点）。

> 软件若把 480/560 当直径使用，会得到完全错误的量级。建议在解析输入时显式命名 `face_gear_inner_radius` 并在文档里写明来源论文的措辞是"内径"。

---

## 3. `cases.json` 字段字典

```
{
  "schema_version": "1.0",
  "unit_system": {...},          // 见第 1 节
  "radius_convention": "...",    // 见第 2 节
  "case_count": 50,
  "cases": [ Case, ... ]
}
```

### Case 对象

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | str | 全局唯一。命名规则 `论文代码-算例代码[-序号]`，如 `HE2023-FIVE-TEETH`、`JIN2012-FACE-07` |
| `source.paper` | str | 论文短名（与 `work/pdf_text/<name>.txt` 同名） |
| `source.authors` / `year` / `venue` | | 文献出处 |
| `source.pdf` | str | 原始 PDF 相对路径 |
| `source.pdf_pages` | int[] | **PDF 文件页码（1-based）**，不是论文印刷页码 |
| `source.section` | str | 章节 / 表号 / 图号 |
| `case_name` | str | 中文说明 |
| `method` | str | 论文用的方法（Hertz 解析 / HB/Z84 当量齿轮 / 30°切线法 / 有限元 / 简化系数表） |
| `inputs` | obj | 几何 + 材料。字段名固定：`module_m_mm`、`z_pinion`、`z_face_gear`、`z_shaper`、`pressure_angle_deg`、`shaft_angle_deg`、`helix_angle_deg`、`addendum_coef_ha_star`、`clearance_coef_c_star`、`face_gear_inner_radius_mm`、`face_gear_outer_radius_mm`、`tooth_width_b_mm`、`elastic_modulus_E_MPa`、`poisson_ratio_nu`、`transmission_ratio` |
| `inputs_derived` | obj | 由论文数据推出的输入量（含 `formula` 与 `derived_by`） |
| `operating` | obj | 工况：`torque_T1_Nm`、`speed_rpm`、`power_kW`、`normal_load_Fn_N`、`head_load_N`、`life_h` 等 |
| `load_factors` | obj | 载荷/精度系数（仅刘新胜 GUI 算例有实测值） |
| `outputs_expected` | obj | **论文给出的结果**。标量值为 `{"value": x, "page": n, "table|section": "...", "confidence": "high"}`；成组数据放 `points` / `sections` / `contact_points` 数组 |
| `confidence` | "high"/"medium"/"low" | 见第 5 节 |
| `reproducible` | true / "partial" / false | `true` = 论文输入齐全可直接算；`partial` = 需补边界条件（如压头加载模型）；`false` = 几何或工况缺失，只能做量级参考 |
| `data_conflict` | bool | 论文内部自相矛盾（见第 6 节） |
| `caveats` | str[] | 复现时必读的坑 |

### 算例清单（50 个）

| 组 | id 前缀 | 个数 | 内容 | confidence | reproducible |
|---|---|---|---|---|---|
| 何飞 2023 | `HE2023-*` | 3 | 五齿模型全参数算例（解析+FEM+简化三种结果）；算例1/算例2（参数引自他文献） | high / medium | true / false |
| 刘新胜 2016 | `LIU2016-HBZ84-DEMO` | 1 | HB/Z84 当量齿轮法 MATLAB GUI 全链算例（输入→边界条件→重合度→载荷系数→σF、SF） | high | true |
| 刘新胜 2016 | `LIU2016-TEST-G1..G7` | 7 | 7 组试验件 × 3 种压头载荷：试验值 + 有限元值 + 误差表 + 反算理论值 | high | partial |
| 靳广虎 2012 | `JIN2012-CYL-01..16` | 16 | 圆柱齿轮齿根弯曲（参数表 + FEM + 误差 + 反算计算值） | high | partial |
| 靳广虎 2012 | `JIN2012-FACE-01..16` | 16 | 面齿轮齿根弯曲（同上，走 (4-12) 公式） | high（1 组 medium，数据冲突） | partial |
| 靳广虎 2012 | `JIN2012-EXP-CYL` | 1 | 圆柱齿轮静载试验 4000/5000/6000 N，含跨齿宽 5 点分布 | high | partial |
| 李占平 2018 | `LI2018-HERTZ-150Nm` | 1 | 150 N·m 工况 14 个接触点的赫兹 σHmax（1523.98 MPa 峰值） | high | true |
| 李占平 2018 | `LI2018-BENDING-1000N` | 1 | Wn=1000 N 沿齿宽 8 截面的弯曲应力（187→534 MPa） | high | true |
| 任雅丽 2009 | `REN2009-HERTZ` | 1 | 当量齿条法 σH=317.4 MPa | low | false |
| 刘慧茹 2022 | `HUIRU2022-OPT-A/B/C` | 3 | 修形优化 3 个 Pareto 方案的 σHmax（676.08 / 692.3 / 727.8 MPa） | high | partial |

---

## 4. `coefficients.json` 字段字典

```
{ "schema_version", "unit_system", "chart_digitization_policy",
  "tables": [ { "id", "name", "source", "entries"|"values"|"digitized", "confidence", "notes" } ] }
```

| id | 内容 | confidence |
|---|---|---|
| `HE2023-FORMULA-CHAIN` | 何飞 (1)~(33) 全套解析/简化公式（曲率→载荷分配→赫兹→30°切线→Ysa/YFa→重合度→简化式） | medium |
| `HE2023-FIG4-YFA-YSA` | 图4 的 YFa / Ysa 曲线数字化（α=20/25/30°，横轴 N2/Ns=4~20，10 条 Ns 曲线） | **low** |
| `HE2023-YFA-YSA-CROSSCHECK` | 由 σb=76.3 MPa 反算 `YFa·Ysa = 2.989`（与读图 2.99 吻合） | medium |
| `LIU2016-HBZ84-FORMULA-CHAIN` | HB/Z84 (3-20)~(3-59)：啮合刚度、q、ZH、ZE、YF、SFn/hFe、**YS 式(3-43)**、Yε、Yβ、YX、σF0、σFP、SF | high |
| `LIU2016-LOAD-FACTORS-DEMO` | 软件算例实测 KA / KV / KHβ / KFβ / KHα / KFα / 施加载荷 / 精度等级 | high |
| `JIN2012-WIDTH-FACTOR-CORRECTION` | 齿宽系数修正：圆柱 0.1441φ+0.2069，面齿轮 0.0831φ+0.422（最易实现） | high |
| `LI2018-BENDING-COEFFICIENTS` | 齿形系数 x = −6.2018(X/b)+8.0689；逐截面 x / YS / σt；赫兹式(2.43) | high |
| `REN2009-CONTACT-COEFFICIENTS` | ZH=2.285、Zε=0.9、Zβ=1.0、K=1.119、σH=317.434 | low |
| `HUIRU2022-MODIFICATION-VARIABLES` | 修形变量范围（u0, ar, ae）、ULH/NSGA-II 参数 | medium |
| `SHARED-CONSTANTS` | E、ν、ZE=189.8、ha*、c*、`r_p2 = m·z2/2`、`b = R2−R1` | high |

### 两个必须知道的系数冲突

1. **YS 的指数律**：刘新胜式 (3-43) 与 ISO 6336-3 为
   `YS = (1.2+0.13L) · qs^(1/(1.21+2.3/L))`，
   而何飞式 (22) 印刷为 `q^(La/(1.12La+2.3))`。二者等价形式下常数应为 **1.21**，1.12 疑为印刷错位。
   **建议实现取 1.21**，并在单元测试里保留 1.12 作为 diff 记录。
2. **何飞式 (15)/(32) 的下标/指数在 PDF 中散乱**：已按量纲一致性复原（见 `HE2023-FORMULA-CHAIN` 的 `note`），属推测，`confidence=medium`。数值验证只能靠 σb 那条（见下）。

---

## 5. confidence 与 derived 的含义

| 值 | 含义 |
|---|---|
| `high` | 论文**表格或正文明确写出数值**，且出处可定位到具体页/表 |
| `medium` | 数值来自正文但存在单位/量级疑点，或由两个表反算，或由截图读取 |
| `low` | 只能读图（曲线/云图图例），精度受限；或论文内部不自洽 |

`derived: true` 的字段 = **不是论文直接给出的数**，由本数据集用注明公式反算。现有两类：

1. **理论值反算**（刘新胜）：论文只给"理论值−试验值"相对误差，未给理论值本身
   → `sigma_theory = sigma_test × (1 + err%/100)`；精度受百分比取整限制，约 ±0.03 MPa。
2. **计算值反算**（靳广虎）：表 4.3/4.6 只有一列应力值（判为有限元值）+ 一列相对误差
   → `sigma_calc = sigma_fem × (1 + err%/100)`。

派生量**可以**用于测试，但断言容差应放宽（见 `docs/05-test-cases.md`）。

---

## 6. 已知数据缺陷（复现前必读）

| # | 位置 | 问题 | 处置 |
|---|---|---|---|
| 1 | 靳广虎 表4.5 第4行 | 齿宽 19 mm、模数 5 → φ_b = 3.8，但表4.6 给 φ_b = 3.2（疑齿宽应为 16 mm） | 标 `data_conflict: true`、`confidence: medium`；两值都保留 |
| 2 | 刘慧茹 表4-5 | ae 初值 0.04 超出上界 0.01（疑 0.004） | 记录原值并加注 |
| 3 | 任雅丽 第4/5章 | P=1000 kW & n=400 r/min 应得 T≈23873 N·m，正文写 47746 N·m（2 倍）；Fn=331.8 N 实应 ~3.3e5 N（1000 倍，kW 与 mm 混用） | `confidence: low`、`reproducible: false` |
| 4 | 何飞 表1 | 未给 `ha*`、`c*`；σb 简化值 76.3 MPa 依赖 ε，而 ε 依赖 `ha*` | 用 `ha*=1` 假设，ε=1.5545，已在 `HE2023-YFA-YSA-CROSSCHECK` 自洽验证 |
| 5 | 刘新胜 表5.1 | 7 组试验件未给齿宽/`ha*`；载荷是"压头静载"不是传动切向力 | `reproducible: partial` |
| 6 | 何飞 表2/表3 算例1/2 | 几何参数引自文献[15]/[16]，本文未复述 | `reproducible: false` |
| 7 | 李占平 | 表3.1 的截面跨度 34.0 mm 与 R2−R1 = 34.5 mm 差 0.5 mm | 两值都保留，加注 |
| 8 | 靳广虎 表4.3/4.6 | 只有一列应力值，未标明是有限元值还是计算值 | 依正文定为有限元值，计算值用误差反算 |

---

## 7. 复核与再生成

```powershell
# 论文文本按页检索 / 打印（避免 GBK 控制台乱码）
$env:PYTHONIOENCODING="utf-8"
cd work\benchmarks\tools
python pagedump.py find he 表1 算例 MPa          # 列出命中关键词的 PDF 页码
python pagedump.py page he 5                     # 打印第 5 页（压缩空白）
python pagedump.py grep li "模数|齿数"            # 正则检索

# 关键页渲染成 PNG（--clip 用页内 0~1 比例裁剪）
python render.py he 5 he_p5_full --dpi 300
python render.py liu 73 liu_p73 --clip 0.05,0.02,0.95,0.98 --dpi 500

# 重新生成 cases.json
python build_cases.py
```

`tools/build_cases.py` 是 `cases.json` 的**唯一真源**：改数据请改脚本再运行，不要手改 JSON（脚本会做 id 唯一性与 φ_b 一致性检查）。

渲染产物命名约定：`<论文短名>_p<PDF页码>_<内容>.png`，例如 `liu_p73_full.png` = 刘新胜论文 PDF 第 73 页（图6.10 弯曲强度计算模块）。

---

## 8. 引用与致谢

数据来源（详见各 case 的 `source` 字段）：

1. 何飞, 钱卫香, 付学中, 彭先龙. 面齿轮副啮合强度的简化计算[J]. 机械强度, 2023, 45(5): 1192-1198. DOI:10.16579/j.issn.1001.9669.2023.05.024
2. 刘新胜. 基于航标的面齿轮传动弯曲强度计算方法研究[D]. 南京航空航天大学, 2016.
3. 靳广虎. 正交面齿轮传动的强度与动力学特性分析研究[D]. 南京航空航天大学, 2012.
4. 李占平. 非共轭点接触面齿轮传动的强度设计方法研究[D]. 西安工业大学, 2018.
5. 任雅丽. 某正交直齿面齿轮传动系接触分析[D]. 燕山大学, 2009.
6. 刘慧茹. 直齿面齿轮副多目标优化设计计算机辅助优化技术研究[D]. 中南大学, 2022.

> 本数据集仅摘录论文中的参数与结果用于软件验证，不重新发布论文内容。若论文数值本身有误（第 6 节），以标注为准，**不要为了"对上论文"而改软件**——先把偏差解释清楚。
