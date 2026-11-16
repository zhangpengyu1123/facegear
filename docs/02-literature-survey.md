# 02 面齿轮强度计算：网络文献与标准调研

> **文档定位**：本文件是「面齿轮应力计算软件」的外部知识基线，与本地 6 篇中文论文（`work/pdf_text/`）互补，提供**标准化与国际化视角**。
> **调研执行**：teammate `lit-scout`，2026-11-16。
> **证据链**：全部检索词、URL、抓取失败记录见 [`work/literature/retrieval-log.md`](../work/literature/retrieval-log.md)；逐字原文片段见 [`work/literature/quotes.md`](../work/literature/quotes.md)；结构化题录（含核实等级 A/B/C）见 [`work/literature/sources-verified.json`](../work/literature/sources-verified.json)。

## 可获取性总声明（先读这一节）

本次调研的硬约束：**几乎所有标准的正文都在付费墙后面**。因此本文严格区分两类陈述：

| 标记 | 含义 |
|---|---|
| ✅ **已核实** | 我实际抓到了页面/API 原始输出，公式图已逐张目视核验 |
| ⚠️ **仅题录** | 只核实到标准号/作者/年份/期刊/DOI，全文 403 或付费，**不对正文公式细节作任何声称** |
| ❌ **未检索到** | 明确说明检索不到，不以推测填补 |

不满足上述任一条的文献，一律不写入本文。

**具体到本文涉及的核心对象：**

- GB/T 3480-1997（≡ ISO 6336 体系）的公式链：✅ **已核实**（嘉立创FA机械设计手册复刻全条款 + 5 张公式图目视核验）
- 2024 MMT 面齿轮接触应力论文：⚠️ **仅题录 + 关键词**（ScienceDirect 403，TUM mediatum 导出 BibTeX 核实卷期页）
- Litvin 2002 CMAME 面齿轮经典：⚠️ **仅题录**（NASA NTRS PDF 403，作者/期刊/DOI/被引三方一致）
- ISO 6336-1:2019、ISO 10300-1:2023、AGMA 2101-D04、DIN 3990-3、HB/Z 84.1/84.3：⚠️ **仅题录**（全部 403 或不可解析）
- **AGMA 2101-D04 的标准全称我没能核实到**，故本文只登记标准号与版本状态，不写其公式——这是纪律要求，不是遗漏。

---

## 1. 标准体系对照表

面齿轮**没有专门的承载能力标准**（见 1.3），工程上只能借道三类标准：圆柱齿轮（当量齿轮法）、锥齿轮（角度传动类比）、航空行业标准（HB/Z 84）。

### 1.1 主表

| 标准号 | 名称 | 适用对象 | 对面齿轮的适用性 | 关键公式形式 | 核实 |
|---|---|---|---|---|---|
| **HB/Z 84.1-1984** | 航空渐开线圆柱齿轮承载能力一般系数计算 | 航空渐开线圆柱齿轮 | **高**：面齿轮当量齿轮法的系数来源（本地刘新胜论文即用 84.1+84.3） | 一般影响系数体系 $K_A$、$K_V$、$K_\beta$、$K_\alpha$ | ⚠️ 仅题录（万方索引标题 + 本地论文双源确认名称） |
| **HB/Z 84.3-1984** | 航空渐开线圆柱齿轮轮齿弯曲疲劳强度计算 | 航空渐开线圆柱齿轮轮齿 | **高**：面齿轮弯曲强度直接沿用其 $\sigma_F$ 体系 | $\sigma_F$ 计算 + 许用弯曲应力 + 安全系数 | ⚠️ 仅题录（本地论文逐字引用） |
| **GB/T 3480-1997** | 渐开线圆柱齿轮承载能力计算 | 渐开线圆柱齿轮 | **高**：与 ISO 6336 同构，是国内落地首选公式载体 | $\sigma_{H0}=Z_H Z_E Z_\varepsilon Z_\beta\sqrt{\frac{F_t}{d_1 b}\cdot\frac{u\pm1}{u}}$；$\sigma_F=\sigma_{F0}K_AK_VK_{F\beta}K_{F\alpha}$ | ✅ **已核实**（条款 + 公式图） |
| **GB/T 3480.2-2021** | 直齿轮和斜齿轮承载能力计算 第2部分：齿面接触强度(点蚀)计算 | 同上（新版分部） | **高**：新版分部结构，便于声明标准版本 | 同 ISO 6336-2 | ⚠️ 仅题录 |
| ISO 6336-1:2019 | Calculation of load capacity of spur and helical gears — Part 1: Basic principles, introduction and general influence factors | 圆柱齿轮 | **高**（系数定义层） | 定义 $K_A,K_V,K_{H\beta},K_{H\alpha},K_{F\beta},K_{F\alpha}$ 与安全系数体系 | ⚠️ 仅题录（BSI 页 URL slug 即标题，页面 403） |
| ISO 6336-2 | …— Part 2: Calculation of surface durability (pitting) | 圆柱齿轮齿面 | **高**：$\sigma_H$ 公式母本 | 同 GB/T 3480 接触强度部分 | ⚠️ 仅题录（经 GB/T 3480 间接获得公式结构） |
| ISO 6336-3 | …— Part 3: Calculation of tooth bending strength | 圆柱齿轮轮齿 | **高**：$\sigma_F$ 公式母本 | 同 GB/T 3480 弯曲强度部分 | ⚠️ 仅题录 |
| ISO 10300-1:2023 | Calculation of load capacity of bevel gears — Part 1: Introduction and general influence factors | 锥齿轮（角度传动） | **中**：面齿轮是角度传动，几何上更接近锥齿轮；但标准本身不含面齿轮条款 | 锥齿轮 $\sigma_H$/$\sigma_F$ 体系；符号体系与圆柱齿轮不同，**具体形式未核实** | ⚠️ 仅题录（AFNOR 页 URL slug 即标题） |
| DIN 3990-3:1987-12 | Tragfähigkeitsberechnung von Stirnrädern; Berechnung der Zahnfußtragfähigkeit（齿根承载能力计算） | 圆柱齿轮齿根 | **中**：ISO 6336 之前的德国标准体系 | 齿根承载能力计算（**与 ISO 6336 的逐项异同未核实**） | ⚠️ 仅题录（Crossref 官方 DOI `10.31030/2069801`） |
| ANSI/AGMA 2101-D04 (R2016) | **全称未核实**（见下） | 公制齿轮承载能力评定 | **低**：AGMA 体系与 ISO/B 法系数不通用，且无面齿轮条款 | **不作声称** | ⚠️ 仅标准号（ANSI Webstore 索引 + 版本状态 "Historical"；站点 Cloudflare 403） |
| — | **AGMA 面齿轮专用标准** | — | — | — | ❌ **未检索到** |

### 1.2 三套体系的定位判断

```
                ┌── 当量齿轮法（工程主流）─────────────┐
面齿轮 ─────────┤                                      ├── σ_H、σ_F
                └── 角度传动类比（ISO 10300 / 锥齿轮）──┘

系数来源：HB/Z 84（航空行业指导性技术文件，中国）  ≈  GB/T 3480（国家推荐性标准，中国）  ≈  ISO 6336（国际）  ≈  DIN 3990（德国，ISO 6336 之前的标准体系）
公式母本：ISO 6336-2 / -3  ←  数值上 GB/T 3480 与其同构，可整体移植
```

**关键判断（供实现决策）**：HB/Z 84 与 ISO 6336/GB/T 3480 在**公式结构上同源**——都是「赫兹接触 + 齿根危险截面悬臂梁（30°切线/抛物线）」两条主线，差异集中在**系数取值的标定基准**（航空材料、航空工况 vs 通用工业）。⚠️ 该差异的具体系数表需以 HB/Z 84 正文核实，本次未获取全文，故本文不给出任何 HB/Z 84 的具体系数数值。

### 1.3 一个对项目定位有意义的发现

**AGMA 与 ISO 均无面齿轮（face gear）专用承载能力标准。** 检索 AGMA 标准体系时未发现面齿轮承载能力条目（⚠️ 因 AGMA 站点全面 403，此项为"未检索到"而非"确认不存在"，但结合 ISO 10300 与 ISO 6336 的目录范围，面齿轮标准缺位是高置信度判断）。

→ 这正是本软件的价值点：**把"当量齿轮法 + 现代曲率/LTCA 修正"固化成可复现的计算工具，填补标准空白**。

---

## 2. 面齿轮强度计算理论谱系

四条技术路线，按"实现成本 vs 精度"排列：

### 路线 A：当量齿轮法（Equivalent Gear Method）——HB/Z 84 体系

**核心思想**：把面齿轮副在某瞬时啮合点映射为一对**当量直齿圆柱齿轮**（当量齿数 $z_v$、当量模数、当量中心距），然后**整套套用 ISO 6336 / GB/T 3480 / HB/Z 84 的 $\sigma_H$、$\sigma_F$ 公式**。

- 输入：$m, z_1, z_2, \alpha$、轴交角、内/外半径（齿宽 $B$）
- 关键中间量：当量曲率半径 $\rho_{eq}$、当量齿宽 $b_{eq}$、齿宽方向载荷分配系数
- 输出：$\sigma_H$、$\sigma_F$、安全系数 $S_H$、$S_F$

| 优点 | 缺点 |
|---|---|
| 直接复用成熟标准系数表，**工程可接受性最强**（审图/评审认这个） | 当量映射本身是近似，面齿轮沿齿宽曲率变化剧烈时误差大 |
| 实现成本最低，纯解析、毫秒级 | 无法反映点接触椭圆、边缘接触、安装误差敏感性 |
| 与本地 6 篇论文中的 4 篇方法一致，便于对拍 | 系数表（$Z_{NT}, Y_{NT}, Z_L Z_V Z_R, Y_{\delta relT}$ 等）需逐张数字化 |

**本地支撑**：刘新胜（南航 2016）「基于航空标准 HB/Z84，给出了面齿轮当量齿轮…」；何飞（机械强度 2023）「应用 30°切线法确定轮齿危险截面处齿厚」——30°切线法正是 ISO 6336 方法一的几何基础。

### 路线 B：Hertz 解析法 + 曲率精确计算

**核心思想**：不整体套标准，而是**逐点**算面齿轮齿面主曲率，代入 Hertz 线/点接触公式求局部接触应力，再沿啮合周期积分取峰值。

- Litvin 体系（2002 CMAME）建立了面齿轮齿面方程与展成法，是曲率计算的几何基础
- 2024 MMT 论文（Hochrein/Otto/Stahl）关键词直指 `Curvature calculation` + `Equivalent cylindrical gearing` + `LTCA`——即"精确曲率 + 等效圆柱齿轮 + 加载齿接触分析"

| 优点 | 缺点 |
|---|---|
| 物理意义清晰，能给出接触椭圆、应力分布 | 需要齿面方程/展成参数，几何模块复杂度高一个量级 |
| 可解释"为什么边缘应力高" | 对输入几何精度敏感；实现周期长 |

### 路线 C：LTCA / 加载齿接触分析（含多齿接触）

**核心思想**：在 TCA（空载齿接触分析）得到的接触迹/接触椭圆上，用**齿与轮体的柔度矩阵**做载荷分配，求出沿啮合周期的载荷历程，再算 $\sigma_H$、$\sigma_F$。

- Tang & Liu 2013（J. Cent. South Univ. 20(2):354-362）：加载多齿接触分析与接触应力计算
- Wang et al. 2012（Proc IMechE C）：正交面齿轮 LTCA
- Zhou et al. 2024（Proc IMechE C）：TCA→LTCA 求齿面载荷分布与齿根弯曲应力，与 FEM 及**齿根应力试验**三方对拍；FEM 一个啮合周期约 5 h，本方法约 40 s
- **Berger/Otto/Stahl 2024（AGMA FTM）**：指出面齿轮轮体是**平板圆盘**，现有 LTCA 解析法不覆盖，提出用板/盘公式 + 功积分沿齿宽逐片求轮体刚度

| 优点 | 缺点 |
|---|---|
| 精度最高（接近 FEM），速度远快于 FEM（40 s vs 5 h） | 实现难度最大：需柔度矩阵、轮体刚度、载荷分配迭代 |
| 能给出齿宽方向载荷分布（面齿轮最关心的量） | 标定/验证成本高 |

### 路线 D：简化系数表 / 回归模型

**核心思想**：把 $\sigma_H$、$\sigma_F$ 拟合成几何参数与工况的显式表达式或系数表，查表/插值即可。

- 何飞（机械强度 2023）：基于曲率简化求解 + Hertz，给出"基于齿轮副基本参数表达"的简化公式与系数表
- Jin et al. 2019（Microsystem Technologies）：基于**正交试验**建立接触应力与弯曲应力计算模型（回归路线）

| 优点 | 缺点 |
|---|---|
| 最快、最易用，适合初步选型与参数扫描 | 外推能力差，超出标定域不可信 |
| 代码量极小，便于做"快速估算"模式 | 论文系数表覆盖的参数范围有限，需逐条核对适用条件 |

### 谱系对比总表

| 维度 | A 当量齿轮法 | B Hertz+曲率 | C LTCA | D 简化系数表 |
|---|---|---|---|---|
| 实现成本 | 低 | 中 | 高 | 极低 |
| 计算速度 | ms | ms~s | s 级 | μs |
| 精度（相对 FEM） | 中（±15~30% 量级，需对拍确认） | 中高 | 高 | 低中 |
| 能否给齿宽载荷分布 | 否（需外加假设） | 部分 | **能** | 否 |
| 工程可接受性 | **最高**（有标准背书） | 高 | 中（需验证报告） | 低 |
| 建议定位 | **首发版本主力** | 二期升级 | 三期/专业版 | 快速估算模式 |

> ⚠️ 表中"精度"列的数量级是**工程经验判断，非文献实测值**，必须由 `docs/05-test-cases.md` 的基准算例对拍后修正。

---

## 3. 权威文献清单

按"对面齿轮强度计算的贡献度"排序。**可获取性**一栏如实反映本次抓取结果。

### 3.1 面齿轮领域最权威的三篇（结论见 §6）

| # | 作者 | 年份 | 标题 | 期刊/会议 | DOI / URL | 核心贡献 | 可获取性 |
|---|---|---|---|---|---|---|---|
| **1** | Litvin, F. L.; Fuentes, A.; Zanzi, C.; Pontiggia, M.; Handschuh, R. F. | **2002** | Face-gear drive with spur involute pinion: geometry, generation by a worm, stress analysis | Computer Methods in Applied Mechanics and Engineering | [10.1016/S0045-7825(02)00215-3](https://doi.org/10.1016/S0045-7825(02)00215-3) | 面齿轮齿面方程、蜗杆展成法、应力分析的**理论奠基**（被引 164~170） | ⚠️ 仅题录；NASA NTRS OA PDF 返回 403 |
| **2** | Hochrein, J.-F.; Otto, M.; Stahl, K. | **2024** | Face gear drives: Nominal contact stress calculation for flank load carrying capacity evaluation | Mechanism and Machine Theory, **195**: 105573 | [10.1016/j.mechmachtheory.2024.105573](https://doi.org/10.1016/j.mechmachtheory.2024.105573) | 面齿轮**名义接触应力**计算：曲率计算 + 等效圆柱齿轮 + LTCA，用于齿面承载能力评定（被引 22） | ⚠️ 仅题录+关键词；全文 403 |
| **3** | Berger, J. F.; Otto, M.; Stahl, K. | **2024** | Analytical Calculation of the Gear Body Stiffness of Face Gears | AGMA Fall Technical Meeting 2024 (FTM 2024), Rosemont, US, 2024-10-07/09 | [TUM Pure 记录](https://portal.fis.tum.de/en/publications/analytical-calculation-of-the-gear-body-stiffness-of-face-gears) | 面齿轮**盘状轮体刚度**解析法，补齐 LTCA 缺口，可推广至锥齿轮 | ⚠️ 仅摘要（TUM 页面完整摘要已抓取） |

> 选这三篇的理由：**1 给几何**（齿面怎么来的）、**2 给接触应力**（工程最需要的 $\sigma_H$）、**3 给弯曲应力的前置条件**（轮体刚度——面齿轮弯曲应力不能直接套圆柱齿轮公式的根本原因）。

### 3.2 面齿轮专项文献（按主题）

**几何/展成与 TCA**

| 作者 | 年份 | 标题 | 期刊 | DOI | 可获取性 |
|---|---|---|---|---|---|
| Litvin, F. L. 等 | 2004 | Design, generation and stress analysis of face-gear drive with helical pinion | CMAME | [10.1016/j.cma.2004.09.006](https://doi.org/10.1016/j.cma.2004.09.006) | ⚠️ 仅题录 |
| Wang, Y. 等 | 2012 | Loaded tooth contact analysis of orthogonal face-gear drives | Proc IMechE Part C | [10.1177/0954406211432976](https://doi.org/10.1177/0954406211432976) | ⚠️ 仅题录 |
| Zschippang, H. A.; Weikert, S.; Wegener, K. | 2022 | Face-gear drive: Meshing efficiency assessment | Mechanism and Machine Theory | [10.1016/j.mechmachtheory.2022.104765](https://doi.org/10.1016/j.mechmachtheory.2022.104765) | ⚠️ 仅题录 |

**接触应力 / 弯曲应力计算**

| 作者 | 年份 | 标题 | 期刊 | DOI | 可获取性 |
|---|---|---|---|---|---|
| Tang, J.-Y.; Liu, Y.-P. | 2013 | Loaded multi-tooth contact analysis and calculation for contact stress of face-gear drive with spur involute pinion | J. Central South Univ. **20**(2): 354-362 | [10.1007/s11771-013-1495-x](https://doi.org/10.1007/s11771-013-1495-x) | ⚠️ 仅题录 |
| Jin, M. 等 | 2019 | Contact stress and bending stress calculation model of spur face gear drive based on orthogonal test | Microsystem Technologies | [10.1007/s00542-019-04630-w](https://doi.org/10.1007/s00542-019-04630-w) | ⚠️ 仅题录 |
| Zhou, W.-G.; Zhu, R.-P. 等 | 2024 | Theoretical and experimental research on tooth root bending stress of face gear | Proc IMechE Part C | [10.1177/09544062241228009](https://doi.org/10.1177/09544062241228009) | ✅ **摘要级**（含试验对拍细节） |

**直升机主减速器应用**

| 作者 | 年份 | 标题 | 期刊 | DOI | 可获取性 |
|---|---|---|---|---|---|
| Litvin, F. L.; Wang, J.-C.; Bossler, R. B.; Chen, Y.-J. D.; Heath, G. F.; Lewicki, D. G. | 1994 | Application of Face-Gear Drives in Helicopter Transmissions | Journal of Mechanical Design (ASME) | [10.1115/1.2919434](https://doi.org/10.1115/1.2919434) | ⚠️ 仅题录（被引 140） |
| Handschuh, R. F.; Lewicki, D. G.; Bossler, R. B. | 1994 | Experimental Testing of Prototype Face Gears for Helicopter Transmissions | Proc IMechE Part G: J. Aerospace Engineering | [10.1243/PIME_PROC_1994_208_262_02](https://doi.org/10.1243/PIME_PROC_1994_208_262_02) | ⚠️ 仅题录 |

### 3.3 本地论文（已提取文本，作为交叉验证与基准数据来源）

| 作者 | 年份 | 题名 | 方法路线 | 与本文关系 |
|---|---|---|---|---|
| 刘新胜 | 2016（南航硕士） | 基于航标的面齿轮传动弯曲强度计算方法研究 | A（HB/Z 84.1 + 84.3 当量齿轮法）+ 试验 | HB/Z 84 分部名称的唯一双源证据之一 |
| 靳广虎 | 2012（南航博士） | 正交面齿轮传动的强度与动力学特性分析研究 | A + 动力学 | 提供 $\sigma_H/\sigma_F$ 对比算例 |
| 任雅丽 | 2009（燕山硕士） | 某正交直齿面齿轮传动系接触分析 | B/C | 接触分析算例 |
| 李占平 | 2018（西安理工硕士） | 非共轭点接触面齿轮传动的强度设计方法研究 | B（Hertz + 悬臂梁抛物线法） | 抛物线法 = ISO 方法一的几何基础 |
| 何飞 | 2023（机械强度 45(5)） | 面齿轮副啮合强度的简化计算 | D + B（Hertz + 30°切线） | 最适合直接实现的简化公式 |
| 刘慧茹 | 2022（中南硕士） | 直齿面齿轮副多目标优化设计 | A + 优化 | 参数区间与优化算例 |

---

## 4. 关键公式摘录

### 4.1 齿面接触应力：ISO 6336-2 / GB/T 3480 形式 ✅ 已核实

来源：GB/T 3480-1997 复刻条款（[`14134-2.htm`](https://www.jlcfa.com/mcbook/14134-2.htm)）+ 公式图 `formula_img/gbt3480_sigmaH0.gif`、`formula_img/gbt3480_sigmaH_pinion.gif` 目视核验。

**节点处接触应力基本值：**

$$
\sigma_{H0} = Z_H \, Z_E \, Z_\varepsilon \, Z_\beta \sqrt{\frac{F_t}{d_1 b}\cdot\frac{u \pm 1}{u}}
$$

- 图中原注：「"+"号用于外啮合，"−"号用于内啮合」
- $F_t$：端面内分度圆上的名义切向力 (N)；$b$：工作齿宽 (mm)，取一对齿轮中较小者；$d_1$：小齿轮分度圆直径 (mm)；$u=z_2/z_1$
- $Z_H$ 节点区域系数；$Z_E$ 弹性系数；$Z_\varepsilon$ 重合度系数；$Z_\beta$ 螺旋角系数

**计算接触应力（小轮）：**

$$
\sigma_{H1} = Z_B \, \sigma_{H0} \sqrt{K_A K_V K_{H\beta} K_{H\alpha}}
$$

大轮用 $Z_D$ 替代 $Z_B$。$Z_B$、$Z_D$ 为小轮/大轮单对齿啮合系数，$Z_B,Z_D \le 1.0$ 时取 1.0。

**强度条件与许用应力：**

$$
\sigma_H \le \sigma_{Hp}, \qquad S_H = \frac{\sigma_{HG}}{\sigma_H} \ge S_{H\min}
$$

**适用范围（原文）**：端面重合度 $\varepsilon_\alpha < 2.5$ 的齿轮副。

### 4.2 齿根弯曲应力：ISO 6336-3 / GB/T 3480 形式 ✅ 已核实

来源：[`14156-4.htm`](https://www.jlcfa.com/mcbook/14156-4.htm) + `formula_img/gbt3480_sigmaF0_method1.gif`、`..._method2.gif` 目视核验。

**齿根应力基本值（两种方法）：**

$$
\text{方法一（载荷作用于单对齿啮合区外界点）:}\quad
\sigma_{F0} = \frac{F_t}{b\, m_n}\, Y_F\, Y_S\, Y_\beta
$$

$$
\text{方法二（载荷作用于齿顶，仅 } \varepsilon_\alpha<2 \text{）:}\quad
\sigma_{F0} = \frac{F_t}{b\, m_n}\, Y_{Fa}\, Y_{Sa}\, Y_\varepsilon\, Y_\beta
$$

**计算齿根应力：**

$$
\sigma_F = \sigma_{F0}\, K_A K_V K_{F\beta} K_{F\alpha}
$$

**许用齿根应力与安全系数：**

$$
\sigma_{FG} = \sigma_{F\lim}\, Y_{ST}\, Y_{NT}\, Y_{\delta relT}\, Y_{RrelT}\, Y_X,
\qquad
S_F = \frac{\sigma_{FG}}{\sigma_F} \ge S_{F\min}
$$

$Y_{ST} = 2.0$（用标准给的 $\sigma_{F\lim}$ 值时）。

**适用前提（原文，对本项目极其关键）：**

> 给出的轮齿弯曲强度计算公式适用于**齿根以内轮缘厚度不小于 $3.5 m_n$** 的圆柱齿轮。对于不符合此条件的薄轮缘齿轮，应作进一步应力分析、实验或根据经验数据确定其齿根应力的增大率。

→ **面齿轮轮体是薄盘，必然不满足该前提**，故弯曲应力必须叠加轮体柔度修正（见 §3.1 文献 3）。

### 4.3 赫兹线接触基本式（面齿轮局部接触应力）⚠️ 通用力学式

面齿轮为点接触/有限接触椭圆，工程上先按赫兹线接触估算峰值，再用椭圆修正：

$$
\sigma_{H,\max} = \sqrt{\frac{F_n\, E'}{\pi\, b\, \rho_{eq}}},
\qquad
\frac{1}{E'} = \frac{1-\nu_1^2}{E_1} + \frac{1-\nu_2^2}{E_2},
\qquad
\frac{1}{\rho_{eq}} = \frac{1}{\rho_1} + \frac{1}{\rho_2}
$$

- $F_n$：法向载荷；$b$：接触线长；$\rho_1,\rho_2$：两齿面在接触点的主曲率半径
- 出处说明：这是赫兹接触力学的通用式，**不是某篇文献的专有公式**；本地论文（李占平「根据赫兹方程计算得出最大接触应力」、何飞「结合赫兹接触理论求解齿面接触应力」）均以此为基础。$\rho_{eq}$ 对面齿轮是**沿齿宽变化的量**，必须逐点计算——这正是 2024 MMT 论文关键词 `Curvature calculation` 的由来。

### 4.4 面齿轮接触应力文献中的复合路线（2024 MMT）⚠️ 仅关键词级

由 TUM mediatum BibTeX 关键词：`Curvature calculation; Equivalent cylindrical gearing; Face gear; LTCA; Contact stress; Carrying capacity`

可确认的**方法骨架**（不含具体公式系数）：

```
面齿轮齿面 → 逐点主曲率 ρ_eq → 映射为等效圆柱齿轮（当量 z_v、当量中心距）
          → LTCA 载荷分配（含多齿、齿宽方向）
          → 名义接触应力 σ_H,nominal → 与许用值比较评定承载能力
```

⚠️ **本文不给出该论文的具体公式与系数**——全文未获取，任何具体表达式都将是编造。

### 4.5 简化计算路线（何飞 2023，本地论文）⚠️ 待 task-3 数字化

路线（原文可辨）：`齿面曲率一般表达式 → 节锥面处赫兹应力 → 30°切线法确定危险截面齿厚 → 弯曲应力`

⚠️ 具体公式与系数表由 task-3（`work/benchmarks/coefficients.json`）从 PDF 逐页数字化，本文不重复摘录，避免与 task-3 冲突或引入转写错误。

---

## 5. 典型设计参数与工况范围

### 5.1 直升机主减速器场景（本地论文实测/引用值）

| 场景 | 模数 $m$ | 传动比 | 输入转速 | 功率 | 出处（本地论文逐字） |
|---|---|---|---|---|---|
| AH-64E 主减速器第一级 | — | — | **21 000 rpm** | — | 刘新胜：「奇直升机AH-64E Guardian 中[8]，作为主减速器中的第一级减速传动，输入转速为21000rpm」 |
| 高速重载 1:2 缩比试验 | — | 1:2 | **19 100 r/min** | **271 kW** | 刘新胜：「面齿轮传动应用于高速（19100r/min）、重载（271Kw）的可行性进行了1:2 缩比试验研究」 |
| 正交直齿面齿轮系 | — | — | **19 000 r/min** | **135 kW（1/8 载荷）/ 270 kW** | 任雅丽：「齿轮转速为19 000 r/min，功率为135 kw(实际使用的1/8)和270」 |
| AH-64D 直升机总体 | — | — | 主轴 **300 rpm**（取 400 rpm 设计） | 最大 **1 409 kW** | 任雅丽：「直升机主轴转速最高的不过400 r/min，阿帕奇的主轴转速为300 r/min，在此取400 r/min，美国阿帕奇AH-64D 直升机最大功率达到1 409」 |
| 正交面齿轮动力学算例 | **5 mm** | **i=5**，$\alpha=20°$ | **3 000 / 4 000 / 5 000 rpm** | **250 kW** | 靳广虎：「输入功率P 为250kW，输入转速分别为3000r/min、4000r/min 和5000r/min」「模数m 为5mm，压力角为20°，转速n 为5000r/min」「传动比i 为5」 |
| 非共轭点接触面齿轮 | — | — | 小轮 **10 500 r/min** | **251 kW** | 李占平：「功率251kw，小轮转速为10500r/min」「样本的转速为10500r/min，运行时间全部为1min」 |

**归纳的工况特征**：

- **高速**：小轮转速 10 000 ~ 21 000 rpm（直升机输入级），远高于通用工业齿轮
- **中大功率**：135 ~ 1 409 kW
- **大传动比**：单级 $i = 5$ 量级（面齿轮的核心优势：一级完成锥齿轮需两级的工作）
- **模数**：算例见 $m = 5$ mm；面齿轮模数通常小于同功率圆柱齿轮

⚠️ **上表全部来自本地论文**，未从国际文献核实（NTRS/Elsevier 全文均 403）。国际侧的典型参数需等全文可获取后补充。

### 5.2 材料与载荷谱（待补）

本次**未检索到**面齿轮专用材料的 $\sigma_{H\lim}$、$\sigma_{F\lim}$ 数据表。工程上按 ISO 6336 / GB/T 3480 的试验齿轮疲劳极限表取值，并按 HB/Z 84 的航空材料系数修正。⚠️ 具体数值需查标准正文，本次未获取。

---

## 6. 对本软件实现的建议

### 6.1 公式优先级

| 优先级 | 模块 | 依据 | 理由 |
|---|---|---|---|
| **P0** | $\sigma_H$ 计算链：Hertz → 当量曲率 $\rho_{eq}$ → $Z_H Z_E Z_\varepsilon Z_\beta$ → $K_H$ 系数 | ISO 6336-2 / GB/T 3480 ✅ | 公式链最短、工程最认、本地论文全可对拍 |
| **P0** | $\sigma_F$ 计算链：30°切线/抛物线危险截面 → $Y_F Y_S$ → $K_F$ 系数 | ISO 6336-3 / GB/T 3480 ✅ | 同上；注意方法一/方法二分支（$\varepsilon_\alpha<2$） |
| **P0** | 强度校核与安全系数：$S_H=\sigma_{HG}/\sigma_H$、$S_F=\sigma_{FG}/\sigma_F$ | GB/T 3480 ✅ | $S_{H\min}/S_{F\min}$ 必须可按航空/民品切换 |
| **P1** | 当量齿轮映射模块（面齿轮 → 当量直齿轮 $z_v$、$\rho_{eq}$、齿宽载荷分配） | HB/Z 84.1 + 84.3（⚠️ 仅题录）+ 刘新胜论文 | 这是「面齿轮」区别于普通齿轮的核心；映射公式须以论文/标准正文为准 |
| **P1** | 系数表数字化 + 插值（$Z_{NT}, Y_{NT}, Z_L Z_V Z_R, Z_W, Z_X, Y_{\delta relT}, Y_{RrelT}$） | GB/T 3480 ✅（条款已定位到各系数子页） | 工作量大但机械，适合脚本化生成 |
| **P1** | 轮体柔度修正开关（薄盘 vs 厚轮缘） | Berger 2024 ⚠️ + 标准 3.5$m_n$ 前提 ✅ | 面齿轮必然不满足 3.5$m_n$，不给修正则 $\sigma_F$ 系统性偏低 |
| **P2** | LTCA 模式（多齿接触、齿宽载荷分布） | Tang 2013 / Wang 2012 / Hochrein 2024 ⚠️ | 专业版卖点，但实现成本高 |
| **P2** | 快速估算模式（简化系数表/回归） | 何飞 2023 / Jin 2019 | 参数扫描、初步选型用 |
| **不做** | AGMA 2101 体系 | — | 无面齿轮条款、无标准全文、与 ISO 系数不通用，投入产出比低 |
| **不做（本期）** | 胶合（scuffing）、微点蚀、磨损 | — | 超出"接触应力+弯曲应力"的验收范围 |

### 6.2 架构建议

```
输入层（几何 + 工况 + 材料）
   ↓
[标准适配层]  ← 关键设计：GB/T 3480 / ISO 6336 / HB/Z 84 三套系数表可切换
   ↓              （公式骨架共用，仅系数表与许用值不同）
[当量齿轮映射层]  ← 面齿轮 → 当量直齿轮（本项目核心算法）
   ↓
[应力计算层] σ_H / σ_F（P0） → [+ 轮体柔度修正]（P1） → [LTCA]（P2）
   ↓
[校核层] S_H / S_F vs 许用值，输出报告
```

**关键建议**：把「标准适配层」设计成可插拔——因为**公式骨架（赫兹 + 悬臂梁）三套标准完全一致，差异只在系数表**。这样一套计算引擎可同时输出 GB/T 3480、ISO 6336、HB/Z 84 三份报告，这对航空客户极具价值。

### 6.3 验证策略建议

| 验证手段 | 依据 | 实施建议 |
|---|---|---|
| **解析法 vs 论文算例对拍** | task-3 的 `cases.json` | 首要手段。何飞（简化公式）、靳广虎（对比算例）最适合做黄金基准 |
| **解析法 vs FEM** | Zhou 2024 ⚠️（FEM 啮合周期 5 h vs 解析 40 s） | 二期做，选 1~2 个算例即可 |
| **应变片电测 / 齿根应力试验** | Zhou 2024 ⚠️（root bending stress tests）；Handschuh 1994 ⚠️（原型面齿轮试验）；刘新胜（夹具设计） | 长期，需外部合作 |
| **台架试验** | Handschuh 1994 ⚠️；李占平（10 500 r/min × 1 min 试验样本） | 长期 |

### 6.4 需要后续补齐的信息缺口

1. **HB/Z 84 全文**（84.1 一般系数表 + 84.3 弯曲强度公式与系数）——本次仅题录，是最大的信息缺口
2. **2024 MMT 论文全文**（Hochrein）——决定"曲率计算 + 等效圆柱齿轮"的具体实现细节
3. **Litvin 2002/2004 全文**——面齿轮齿面方程与展成参数
4. ISO 6336-2/-3 现行版本年份（本次仅确认 -1:2019）
5. 面齿轮材料 $\sigma_{H\lim}$、$\sigma_{F\lim}$ 数据表

获取建议：通过机构 IP（高校/院所）访问 ScienceDirect、ISO 官网、AGMA 商店；HB/Z 84 通过航空工业标准所或万方标准全文库。

---

## 附录：本次调研的方法论说明

1. **网页检索**：26 组查询词，覆盖标准/理论/应用/验证四类（清单见 `retrieval-log.md` §1）
2. **结构化 API**（比网页更可靠的题录来源）：
   - OpenAlex（`api.openalex.org`）：主题检索 5 组 + DOI 定点查询
   - Crossref（`api.crossref.org`）：标准与论文题录，DIN 标准 DOI 即由此获得
   - Semantic Scholar Graph API：摘要获取（2024 Proc IMechE C 摘要即由此获得）
3. **公式核验**：从复刻页面下载公式 GIF，逐张目视核验，未依赖 OCR 或记忆
4. **交叉验证**：HB/Z 84 分部名称用「万方索引标题 + 本地论文逐字引用」双源确认
5. **纪律**：24 个目标抓取失败全部登记（`retrieval-log.md` §3），失败项在正文中标注 ⚠️/❌，不以推测填补
