# 01 · GitHub 同类仓库调研：面齿轮 / 齿轮强度计算 / 齿轮几何建模

> 调研任务：task-1（GitHub 同类仓库调研）
> 调研时间：2026-11-16
> 检索环境：`gh` 2.95（已登录账号 `zhangpengyu1123`，token 认证）、Python 3.12、Windows PowerShell 5.1
> 全部原始响应与命令记录见 `work/github/`（文件清单见文末附录）

---

## 0. 摘要（先看结论）

1. **GitHub 上不存在开源的「面齿轮应力/强度计算」实现。** 面齿轮（face gear）相关的公开仓库只有 3 类：几何建模、在机测量、空仓库。唯一具备真实面齿轮算法实现能力的是 **`NoOneExceptEnderk/RatioLab`**（★7，GPL-3.0，Python+Rust），它按 Litvin 的 NASA 报告实现了**正交/偏置面齿轮齿面的共轭包络生成**（含区间算术/Krawczyk 数值认证），但其文档明确声明**不包含强度、磨损、寿命与许用载荷计算**。
2. **齿轮强度计算的开源实现很成熟，但全部限定在「圆柱齿轮」或「锥齿轮」。** 最佳参考是 **`efirvida/python-gearbox`**（★39，MIT，ISO 6336:2019 全部 3 个部分 + AGMA 2001-D04，同时给出 σH 与 σF 的完整因子链，并有 CalculiX 有限元对拍）。
3. **面齿轮强度计算正好落在这两个成熟领域之间的空白地带**：几何侧（RatioLab）不做强度，强度侧（python-gearbox / GEARpie / Bevel-Gear-Design）不做面齿轮。本项目把「面齿轮当量齿轮法（HB/Z 84）+ Hertz 接触 + 悬臂梁抛物线法」做成可计算的软件，正好填补该空白。
4. 三条**必须纠正的先验信息**（见 §6）：`pygears` 是 FPGA 硬件设计框架、与齿轮无关；`gearpy` 的 v0.4.0 已是历史版本、最新为 **1.3.1**；`vanillawang22-code/Inverse-calculation-of-meshing-equation` 是**空仓库**（GitHub 返回 `Git Repository is empty`）。

---

## 1. 检索策略与关键词

### 1.1 工具与额度控制

| 项 | 说明 |
|---|---|
| 主工具 | `gh api -X GET search/repositories`、`gh api -X GET search/code`、`gh api repos/{owner}/{repo}` |
| 认证 | token 认证（账号 `zhangpengyu1123`），避免匿名 60 req/hr 限制 |
| 实际用量 | 仓库检索 37 次（search 限额 30 req/min，脚本间隔 2.2 s）；代码检索 9 次（限额 10 req/min，间隔 7 s）；仓库复核 20 组 × 4 次 |
| 速率受限情况 | **未触发任何 429/限流**，全部 46 次 search 请求成功返回 |
| 踩坑记录 | `gh api` 只要带 `-f` 参数而不显式 `-X GET` 就会**按 POST 发送**（表现为 `HTTP 422 tag_name wasn't supplied` 或 `HTTP 404`），脚本里已全部改为显式 `-X GET` |

> 说明：网络检索受限的情况**不存在**；但「检索不到」本身是重要结论（见 §4）。

### 1.2 仓库检索（37 个 query）

覆盖任务要求的 5 个方向。命令模板：

```bash
gh api -X GET search/repositories \
  -f q='<query>' -f sort=stars -f order=desc -f per_page=50
```

| # | 方向 | query | 命中总数 | 说明 |
|---:|---|---|---:|---|
| 1 | 面齿轮 | `facegear` | 4 | 全部为无关/空壳项目 |
| 2 | 面齿轮 | `"face gear"` | 6 | 3 个 3D 打印玩具、2 个无描述、1 个 RatioLab 以外的空壳 |
| 3 | 面齿轮 | `"face gear drive"` | 0 | **零命中** |
| 4 | 面齿轮 | `"spur face gear"` | 0 | **零命中** |
| 5 | 面齿轮 | `"face gear" stress` | 0 | **零命中** |
| 6 | 面齿轮 | `"face gear" generation` | 0 | **零命中** |
| 7 | 面齿轮（中文） | `面齿轮` | 28 | 仅 2 个相关：在机测量、空仓库 |
| 8 | 面齿轮（中文） | `面齿轮传动` | 6 | 同上，多为词库/文档命中 |
| 9 | 面齿轮（中文） | `面齿轮 强度` | 0 | **零命中** |
| 10 | 强度标准 | `ISO 6336` | 8 | 部分为本科课程设计仓库 |
| 11 | 强度标准 | `"gear rating"` | 6 | 多为游戏数值评分，噪声 |
| 12 | 强度标准 | `AGMA gear` | 18 | 课程设计/单文件计算器为主 |
| 13 | 强度标准 | `DIN 3990` | 3 | 含 GEARpie、hanslhansl/din3990 |
| 14 | 强度标准 | `"gear strength" calculation` | 0 | **零命中** |
| 15 | 强度标准 | `"load capacity" gear` | 1 | hanslhansl/din3990 |
| 16 | 强度标准 | `GB/T 3480` | 2 | 公式速查手册，无代码实现 |
| 17 | 强度标准 | `齿轮 承载能力` | 0 | **零命中** |
| 18 | 几何/TCA | `"tooth contact analysis"` | 1 | 1 个仓库名含 TCA |
| 19 | 几何/TCA | `Litvin gear` | 0 | **零命中**（GitHub 仓库搜索弱于代码搜索） |
| 20 | 几何/TCA | `"involute gear" python` | 11 | 几何生成器为主 |
| 21 | 几何/TCA | `gear generation profile` | 6 | CAD 插件为主 |
| 22 | 几何/TCA | `"bevel gear"` | 88（取前 50） | 锥齿轮 CAD 生成居多 |
| 23 | 几何/TCA | `齿面接触分析` | 1 | 词库类噪声 |
| 24 | 几何/TCA | `"gear tooth profile"` | 9 | 齿廓生成 |
| 25 | Python 生态 | `gearpy` | 2 | AndreaBlengino/gearpy + 一个同名无关项目 |
| 26 | Python 生态 | `pygears` | 22 | **全部是 FPGA 硬件设计框架**，非齿轮 |
| 27 | Python 生态 | `gear python involute` | 15 | 几何生成 |
| 28 | Python 生态 | `"gear design" python` | 15 | 课程设计项目 |
| 29 | Python 生态 | `"gear calculator"` | 254（取前 50） | 大量游戏/自行车齿比计算器 |
| 30 | 中文 | `齿轮` | 226（取前 50） | 故障诊断、游戏、CAD 均在内 |
| 31 | 中文 | `齿轮 强度` | 4 | 其中 2 个为课程设计求解器 |
| 32 | 中文 | `渐开线齿轮` | 4 | Lilililiyyy 两个项目 + 课程题库 |
| 33 | 中文 | `齿轮 设计 计算` | 12 | 单文件计算器为主 |
| 34 | 应力 | `"contact stress" gear hertz` | 0 | **零命中** |
| 35 | 应力 | `gear finite element stress python` | 0 | **零命中** |
| 36 | 应力 | `"bending stress" gear` | 2 | 课程项目 |
| 37 | 面齿轮+展成（中文） | `面齿轮 展成` | 0 | **零命中** |

37 个 query 去重后共 **289 个仓库**，按「名字/描述/topics 命中关键词 + star 加权」打分后人工筛选。打分脚本：`work/github/aggregate.py`。

### 1.3 代码检索（9 个 query）— 判断「有没有人真的写过面齿轮应力代码」

仓库搜索只看 name/description/readme，容易漏掉「README 不提但代码里有」的实现，因此补做代码搜索：

```bash
gh api -X GET search/code -f q='<query>' -f per_page=100
```

| query | total_count | 返回 | 结论 |
|---|---:|---:|---|
| `"face gear"` | 8528 | 100 | 绝大多数是英文散文/无关变量名命中，噪声极大 |
| `"face gear" stress` | 407 | 100 | 无一为齿轮工程实现 |
| `"face gear" language:Python` | 64 | 64 | 命中 `NoOneExceptEnderk/RatioLab` 的 `src/face_geometry.py` |
| `facegear` | 4520 | 100 | 主要命中游戏/无关项目（如 `merc-forge`） |
| `面齿轮` | 619 | 100 | 命中词库、教材、题库、KISSsoft 汉化帮助文档 |
| `面齿轮 强度` | 192 | 100 | 同上，全部为文档/词库，**无代码实现** |
| `"face gear" fillet` | 141 | 100 | 命中 RatioLab 的 `docs/technical/face-gears.md` |
| `HB/Z 84` | 86784 | 100 | **该 query 无效**：GitHub 代码搜索丢弃标点与斜杠，实际退化为宽泛匹配，此数字无意义 |
| `"face gear" hertz` | 46 | 46 | 噪声（专利文本、论文缓存、i18n 文件） |

**关键筛查结果**：`面齿轮 强度`（192 命中）逐条归仓后，命中的仓库全部是拼音词库、机械设计题库、KISSsoft 帮助文档汉化、专利文本缓存 —— **没有任何一个仓库包含面齿轮应力计算代码**。聚合脚本：`work/github/aggregate_code.py`，逐仓明细：`work/github/logs/code_aggregate.txt`。

#### 子串误命中排查（必须记录）

中文「面齿轮」会被「双曲**面齿轮**」「端**面齿轮**廓」等词包含，是本次检索最主要的假阳性来源。对聚合结果里三个"看起来像计算工具"的命中逐个开箱核实：

| 命中仓库 | 假象 | 实际内容 | 判定 |
|---|---|---|---|
| `gxuqpp/final_drive_load_tool_v2` | 名称像"主减速器载荷工具"，且命中 `面齿轮 强度` | 仅 `README.md` + `index.html`（52 KB），内容为**弧齿锥/双曲面齿轮主减速器**的传动比、效率 η_G（式 5-8）、扭矩计算；`index.html` 中**无「应力」「弯曲」字样** | 非面齿轮强度工具，0 star，无许可证，不入选 |
| `fyjgtddco/DSH-SW-and-CAD` | ★59、MIT、1228 文件，含 `rules/gb_transmission_rules.json`、`gb_standards_registry.json`（91 条国标），命中 `面齿轮 强度` | 实为 **SolidWorks + AI 的工程图交付校验项目**；两个 rules JSON 是**标准元数据登记表**（`standard_id/title/scope/severity/validation_method`），仅 1 条标准正文含「面齿轮」，且来自 `GB/T 11365-2019 锥齿轮 精度制` 的「双曲面齿轮」表述；无 σH/σF 计算 | 非面齿轮强度实现；但其 **GB 标准登记表**（含 `GB/T 3480.1-2019` 条目）可作为标准清单类参考（标准体系本身由 task-2 负责） |
| `oubetat/SECP-Fondation-` 的 `GearEngineeringWorkspace.tsx` | 命中 `"face gear" hertz` | 前端工作区 UI 组件，无计算内核 | 排除 |

### 1.4 GitLab 补充检索（7 个 query）

```text
GET https://gitlab.com/api/v4/projects?search=<q>&per_page=20&order_by=last_activity_at
```

`face gear` 命中 12 个（相机包、表盘、Netgear 路由器、面部脱敏工具等，与齿轮无关）；`facegear`、`面齿轮`、`齿轮`、`ISO 6336`、`involute gear` 均 **0 命中**；`gear strength` 命中 4 个职业发展课程文案。
**结论：GitLab 无相关项目。** 原始记录：`work/github/raw_gitlab/`、`work/github/logs/gitlab_commands.log`。

### 1.5 落脚仓库的复核方法（防编造）

对筛出的 20 个仓库，逐个用**单仓库端点**复核，而不是只信搜索结果：

```bash
gh api repos/{owner}/{repo}                       # star / license / pushed_at / topics / size
gh api -X GET repos/{owner}/{repo}/git/trees/{branch} -f recursive=1   # 真实文件树
gh api -X GET repos/{owner}/{repo}/releases -f per_page=100            # 真实 tag
gh api repos/{owner}/{repo}/contents/<path> -H 'Accept: application/vnd.github.raw'  # 原文
```

复核脚本：`work/github/verify_repos.py`、`check_releases.py`、`fetch_files.py`；复核结果汇总：`work/github/verified_repos.json`。**本文表格中的 star / 许可证 / 最后推送时间全部来自上述端点返回，未使用记忆值。**

---

## 2. 候选仓库总表

> 「契合度」定义：**高** = 直接可用于/直接借鉴本项目的应力计算链路；**中** = 方法论或架构可借鉴，但对象不是面齿轮；**低** = 仅几何/周边，参考价值有限。
> 所有 star / 最后推送均为 2026-11-16 通过 `gh api repos/{owner}/{repo}` 实测值。

| 仓库 | URL | star | 语言 | 许可证 | 最后推送 | 功能概述 | 契合度 |
|---|---|---:|---|---|---|---|---|
| `efirvida/python-gearbox` | <https://github.com/efirvida/python-gearbox> | 39 | Python | MIT | 2026-11-14 | ISO 6336:2019（Part 1/2/3）+ AGMA 2001-D04 的接触/弯曲强度评级，含几何导出与 CalculiX 有限元 | **高** |
| `heartworm/py_gear_gen` | <https://github.com/heartworm/py_gear_gen> | 39 | Python | **未声明** | 2020-07-30 | 渐开线直齿轮几何生成，输出 SVG/DXF | 低 |
| `e-dub/pygear` | <https://github.com/e-dub/pygear> | 24 | Python | GPL-3.0 | 2017-10-07 | 基于 pythonOCC 的渐开线齿轮 CAE/CAD 预处理几何生成 | 低 |
| `cfernandesFEUP/GEARpie` | <https://github.com/cfernandesFEUP/GEARpie> | 22 | Python | MIT | 2025-01-10 | 圆柱齿轮几何 + gmsh 有限元网格 + 接触压力/应力场（含摩擦）+ DIN 3990 B / VDI 2736 承载能力 | **高** |
| `NoOneExceptEnderk/RatioLab` | <https://github.com/NoOneExceptEnderk/RatioLab> | 7 | Python | GPL-3.0 | 2026-11-15 | 参数化齿轮/减速器设计工作台，含**正交/偏置面齿轮共轭齿面生成**（Litvin 方法）+ 3D 预览 + STEP/STL 导出 + MCP 接口 | **高** |
| `AndreaBlengino/gearpy` | <https://github.com/AndreaBlengino/gearpy> | 5 | Python | GPL-3.0 | 2026-10-19 | 传动系统动力学分析库（电机/齿轮/轴/轴承），**不做强度评级** | 低 |
| `KoongWeiJian/omm_software` | <https://github.com/KoongWeiJian/omm_software> | 1 | C# | 未声明 | 2025-03-03 | 面齿轮**在机测量**软件（几何测量，非应力） | 低 |
| `JimmyGreenbeans/sn_curve_iso_6336` | <https://github.com/JimmyGreenbeans/sn_curve_iso_6336> | 1 | Python | 未声明 | 2021-12-03 | ISO 6336 的 S-N 曲线计算类（仅 4 个文件） | 低 |
| `JRaposo-m/AxisForge-...-Platform` | <https://github.com/JRaposo-m/AxisForge-Shaft-Bearing-Gear-System-Analysis-Platform> | 1 | Python | 未声明 | 2026-11-10 | 轴/轴承/平行轴齿轮的确定性 CAE 引擎（ISO 21771/6336、ISO 281/16281），PySide6 桌面端 | 中 |
| `Lilililiyyy/gear-transmission-skills` | <https://github.com/Lilililiyyy/gear-transmission-skills> | 1 | Python | AGPL-3.0 | 2026-11-15 | 把下两个内核封装成 Agent Skills（自然语言调用计算内核 + 结果复算），v0.7.0 | 中 |
| `ToumaTouko/gear-calc` | <https://github.com/ToumaTouko/gear-calc> | 1 | HTML | MIT | 2026-10-03 | 单文件纯前端：按《机械设计》(第11版) 教材公式做直齿轮几何 + **σH / σF 校核**，公式并排展示、可导出计算书 | **高** |
| `vanillawang22-code/Inverse-calculation-of-meshing-equation` | <https://github.com/vanillawang22-code/Inverse-calculation-of-meshing-equation> | 0 | — | 未声明 | 2026-10-27 | 描述为「逆向求解啮合方程，求解修形面齿轮用加工刀具齿廓」，但**仓库为空**（GitHub: `Git Repository is empty`） | 无（空仓） |
| `SebWith/gearforge` | <https://github.com/SebWith/gearforge> | 0 | Kotlin | MIT | 2026-10-07 | Android 端 3D 齿轮生成器，14 种齿轮含 `face gear`，导出 STL/3MF/STEP；内购解锁（3D 网格，非强度） | 低 |
| `hanslhansl/din3990` | <https://github.com/hanslhansl/din3990> | 0 | Python | MIT | 2026-05-21 | DIN 3990-5 / -11 承载能力计算实现（11 个文件，作者自述不保证完整性） | 中 |
| `shirudepratik24-stack/mech-tool-api` | <https://github.com/shirudepratik24-stack/mech-tool-api> | 0 | Python | 未声明 | 2026-09-04 | 齿轮/弹簧设计计算 API（AGMA 2001-D04 & IS 7907），FastAPI 部署 | 中 |
| `serdevir91/gearbox-web` | <https://github.com/serdevir91/gearbox-web> | 0 | HTML | 未声明 | 2026-09-09 | 二级减速器竞赛项目（DIN 3990 接触/弯曲 + DIN 743 轴 + ISO 281 轴承），`src/math/din3990GearMath.ts` 为可读实现 | 中 |
| `Lilililiyyy/Bevel-Gear-Design` | <https://github.com/Lilililiyyy/Bevel-Gear-Design> | 0 | Python | AGPL-3.0 | 2026-11-02 | 零偏置直齿/弧齿锥齿轮：几何、啮合力、齿面/整轮建模、ISO 10300 B1/B2 + AGMA 2003 强度、TCA、LTCA（0.10.0） | **高** |
| `Lilililiyyy/Cylindrical-Gear-LTCA` | <https://github.com/Lilililiyyy/Cylindrical-Gear-LTCA> | 0 | Python | AGPL-3.0 | 2026-11-13 | 圆柱齿轮几何 + ISO 6336:2006 接触/齿根强度 + 半解析 LTCA（接触压力、TE、啮合刚度），与 MASTA 对标（0.4.0） | **高** |
| `git-akai/gearcalc` | <https://github.com/git-akai/gearcalc> | 0 | Rust | 未声明 | 2026-10-07 | 齿轮/轮系设计工具：Rust 核心编译到 WASM + Svelte UI，参数计算 + 2D 齿廓 + DXF | 低 |
| `kaziwafeeq-afk/bevel-gear-design-automation` | <https://github.com/kaziwafeeq-afk/bevel-gear-design-automation> | 0 | Python | 未声明 | 2026-10-05 | 锥齿轮自动设计 / 应力分析 / 安全校核（仅 3 个文件，体量极小） | 低 |

**刻意排除**（避免表格被噪声污染，但保留判断依据）：

| 对象 | 排除原因 |
|---|---|
| `bogdanvuk/pygears`（★146） | **不是齿轮库**：FPGA/ASIC 函数式硬件设计框架。任务书把 `pygears` 列入「Python 齿轮生态」是命名误判 |
| `clydejallorina/OverseerVersion1` 等 | `facegear` 命中实为游戏/网页域名，与机械无关 |
| `bakedlays-glitch/merc-forge` | `facegear.py` 是游戏内道具模块 |
| `Sfedfcv/redesigned-pancake`（★280） | 描述被 GitHub 页面文本污染，与齿轮无关 |
| `excellent-max/KISSsoft-2025-Help-ZH` | **有价值但非代码**：1608 页 KISSsoft 2025 官方帮助汉化，是面齿轮设计流程的权威文档参考（含面齿轮章节），不计入开源实现 |
| 各类 `wxFaultDiagnosis` / `YOLOv11-gear-defect-*` | 齿轮故障诊断/缺陷检测，与强度计算无关 |

---

## 3. 重点仓库详评

### 3.1 `NoOneExceptEnderk/RatioLab` — 唯一的真实面齿轮实现（但只做几何）

| 项 | 值 |
|---|---|
| URL | <https://github.com/NoOneExceptEnderk/RatioLab> |
| star / fork | 7 / 0 |
| 语言 / 许可证 | Python（+ Rust 几何内核）/ **GPL-3.0-only** |
| 活跃度 | 创建 2026-10-28，最后推送 2026-11-15，最新 release **v0.2.5** |
| 规模 | 921 个文件，仓库约 61 MB（API `size=62035` KB）；`src/` 应用、`rust/` 内核、`tests/`、`docs/technical/` |

**面齿轮能力（重点）**

- 支持 **15 种机构族**，其中「相交/偏置轴」族明确包含 `face-gear pairs`；面齿轮支持 *直齿 / 斜齿 / 双斜齿* 小齿轮，轴交角 **90°**，带**有符号轴偏置**（0 偏置 = 相交轴，非零 = 交错轴）。
- 齿面由**小齿轮运动的共轭包络**生成（不是把圆柱齿复制到盘面上），实现依据是 Litvin 的两份 NASA 报告，代码里直接标注了公式号：
  - `NASA/CR-2000-209909`：Part 1 §1.4–1.7（方程 19–20 渐开线、21–22 变换与啮合方程、24 传动比、奇异性/尖点条件）；Part 2 §2.1（方程 63–69 偏置直齿面齿轮）、§2.2–2.3（啮合轴与非对称尖点极限）
  - `NASA/CR-2005-213443`：§2–3（方程 1–4、15–18 面齿轮展成、19–23 奇异性与尖点规避）
- 源码位置：`src/face_geometry.py`（Python 包装层）、`rust/geometry-kernel/src/face.rs`、`face_joined.rs`、`surfaces.rs`；测试 `tests/test_face_gears.py`、`test_face_herringbone.py`、`test_face_offset.py`；文档 `docs/technical/face-gears.md`。

**可直接借鉴的算法/工程做法**

1. **啮合方程 + 包络的显式求解链**：文档给出了完整的可复算公式（齿厚半角 `Hhalf(r)`、世界点 `P = Op + Rx(φ)(X, r·cos a0, r·sin a0)`、啮合条件 `n·(ec × (P−Op) − g·ez × P) = 0`，以及化为 `F = k·S·(Y+E) + σ·X·q·Y/rb + X·h − S/g = 0` 的一元求根形式并给出 `FY` 用于分支选择）。这套「啮合条件 → 一元方程 → 分支选择 → 包络装配」的结构，与本项目用当量齿轮法推 σH/σF 的输入几何同源。
2. **区间算术 + Krawczyk 数值认证**：用参数化 Krawczyk 单元在 `(X, h)` 矩形上包住标量根，再用隐函数导数验证根分离、径向顺序单调、齿根/齿顶宽度。这是「数值几何结论要有可验证界」的工程范式，值得本项目在「危急截面位置/接触点位置」求解时借鉴。
3. **一份 JSON 工程文件 + MCP 本地服务**：桌面端与浏览器共用同一 JSON 项目格式，另有本地 MCP server 供 agent 调用（`docs/mcp.md`）。对本项目「计算内核与 UI 解耦」的架构选型很有参考价值。
4. **明确的能力边界写法**：README 用「Current limits」一节声明「不认证强度、寿命、可制造性」；`docs/technical/face-gears.md` 结尾亦写「No strength, wear, durability, allowable load … is implied」。这种边界声明值得本项目在自己的文档里照抄——本软件只做强度校核，不宣称寿命/胶合/制造可行性。

**局限**

- **完全没有 σH / σF**：`docs/technical/calculations.md` 只覆盖几何、运动学与**载荷（切向/径向/轴向力）**，无应力；全仓库文件名中无 `stress` / `strength` / `rating`。
- 采用「理想等齿数插齿刀」假设，不重现工业齿面局部化（不同插齿刀齿数/修形），也不是加载接触模型（无 LTCA）。
- 许可证 **GPL-3.0-only**：若本项目分发闭源软件，**不能链接或复制其代码**，只能读其算法与文档。

---

### 3.2 `efirvida/python-gearbox` — 强度计算的「标准实现」范本（圆柱齿轮）

| 项 | 值 |
|---|---|
| URL | <https://github.com/efirvida/python-gearbox> |
| star / fork | 39 / 16 |
| 语言 / 许可证 | Python（3.11–3.13）/ **MIT** |
| 活跃度 | 创建 2015，最后推送 2026-11-14，release `v0.2.0` |
| 学术标识 | Zenodo DOI `10.5281/zenodo.3660526`，文档站 `efirvida.github.io/python-gearbox` |

**能力**

- **ISO 6336:2019 Part 1/2/3 + AGMA 2001-D04** 双标准，同时算 **点蚀（σH）** 与 **齿根断裂（σF）**，覆盖直齿/斜齿/双斜齿/内齿、插齿刀切齿、静载与有限寿命。
- 目录结构清晰：`src/gearbox/standards/iso6336/{_load_factors,_materials,bending,pitting}.py`、`src/gearbox/standards/agma2101/{_factors,_geometry,_strength,bending,pitting}.py`，并有 `tests/test_*_golden.py` 黄金值测试。
- **每个中间因子都可单独取出**（`result.dynamic_factor`、`life_factor_pinion` 等，docstring 标注标准符号）——这一点对本项目至关重要：需要能和论文的系数表逐项对拍。
- 附带 `gearbox.fem`：对**真实齿形**（含滚刀切出的齿根圆角）建 2D/3D 网格，用 **CalculiX** 求解，可与标准法结果互相对拍。
- 文档把公式写全（`docs/theory/iso6336-2.md`、`iso6336-3.md`、`agma-strength.md`），可直接引用：

**可复用的公式骨架（摘自其 theory 文档，ISO 6336 符号体系）**

```text
接触应力（ISO 6336-2）：
  σH0 = Z_H · Z_E · Z_ε · Z_β · sqrt( (F_t / (b·d1)) · (u+1)/u )
  σH1 = Z_B · σH0 · sqrt( K_A·K_γ·K_v·K_Hβ·K_Hα )
  σH2 = Z_D · σH0 · sqrt( K_A·K_γ·K_v·K_Hβ·K_Hα )
  其中 u = z2/z1，双斜齿 b = 2·b_B
  Z_H = sqrt( 2·cosβ_b·cosα_wt / (cos²α_t·sinα_wt) )
  Z_E = sqrt( 1 / (π·[(1−ν1²)/E1 + (1−ν2²)/E2]) )
  Z_ε = 分段式（依 ε_α、ε_β），Z_β = 1/sqrt(cosβ)

齿根应力（ISO 6336-3，其式(3)）：
  σF = σF0 · K_A · K_γ · K_v · K_Fβ · K_Fα
  安全系数 S_F = σ_FG / σ_F ≥ S_Fmin

许用/安全：
  σH ≤ σ_HP  等价于  S_H ≥ S_Hmin（不要重复施加最小安全系数）
```

> 对本项目的直接价值：HB/Z 84 的当量齿轮法本质上是 ISO/AGMA 体系在航空标准里的简化分支。`python-gearbox` 的**因子链组织方式**（每个 K 因子独立可查、可替换）正是我们要做的「简化系数表法」的工程化模板；其 σH0 的 Hertz 内核可以和论文的 Hertz 接触应力公式逐项映射。

**局限**：只支持**平行轴圆柱齿轮**，无锥齿轮、无面齿轮；本软件的面齿轮当量齿轮法需要自己做「面齿轮 → 当量直齿轮」的参数映射后才能复用其因子命名体系。

---

### 3.3 `cfernandesFEUP/GEARpie` — 接触应力场 + DIN 3990，方法论最接近「Hertz + 有限元对拍」

| 项 | 值 |
|---|---|
| URL | <https://github.com/cfernandesFEUP/GEARpie> |
| star / fork | 22 / 8 |
| 语言 / 许可证 | Python / **MIT** |
| 活跃度 | 最后推送 2025-01-10（本项目调研中较「静」但完整） |

**能力**：圆柱齿轮几何（MAAG 方法）+ 沿啮合线的**接触压力与应力场（含摩擦）**、油膜厚度、功率损失与发热、gmsh 结构化有限元网格（1/2 阶单元）、**DIN 3990 B 法**（钢齿轮）与 **VDI 2736 Part 2**（塑料齿轮）承载能力、VDI 2736 齿根应力（C 法，可选 B 法）、磨损/变形/峰值载荷校核。

**借鉴点**

- `CLASSES/DIN3990.py` 是单文件、可读的 DIN 3990 实现，适合作为「欧标与航标对照」的参考。
- 其「**沿接触路径离散（A/B/C/D/E 五点或任意点）+ 沿齿宽离散**」的数据组织方式，正是本项目做「齿宽方向载荷分配」和 σH 沿齿宽分布时的自然数据结构。
- 明确给出了「刚性载荷分配模型 + 若外部提供 k=f(啮合位置) 则改用该刚度」的接口设计——本项目若要做「简化系数表法 ↔ 有限元」双轨，可以直接采用这种「外部刚度表注入」的设计。

**局限**：无面齿轮；DIN 3990 与 HB/Z 84 的系数表不同（前者更细，后者是航空简化），需要做系数映射与差异说明。

---

### 3.4 `Lilililiyyy/Bevel-Gear-Design` — 与本项目形态最像的「同类软件」（锥齿轮版）

| 项 | 值 |
|---|---|
| URL | <https://github.com/Lilililiyyy/Bevel-Gear-Design> |
| star / fork | 0 / 0 |
| 语言 / 许可证 | Python 3.10+ / **AGPL-3.0-only** |
| 版本 | README 标注 0.10.0（**无 GitHub release**） |
| 规模 | 256 个文件 |

**能力（模块表，直接来自 README）**：几何与载荷（节锥、外端/中点/内端尺寸、齿厚齿高、重合度、切向/径向/轴向啮合力）→ 齿面与 CAD（直齿球面渐开线 + 工程根连接、弧齿刀盘展成、整轮 STEP/BREP）→ **标准强度**（ISO 10300 B1/B2、AGMA 2003 分支、独立 2014 名义应力链）→ **无载 TCA**（接触轨迹、无载传递误差）→ **整轮 FE-LTCA**（三维线弹性、齿体/轮体柔度、多齿耦合、非负接触压力、扭矩平衡）→ 局部半解析接触 → 结果后处理（TE、切线刚度、齿对分载、瞬时/周期最大压力）。

**架构对照（可直接映射到本项目）**

| Bevel-Gear-Design 模块 | 文件 | 本项目对应 |
|---|---|---|
| 几何 | `bevel_gear/*geometry*` | 面齿轮齿面/当量齿轮参数 |
| 名义强度 | `bevel_gear/strength_assessment.py`、`iso2014_nominal.py`、`agma_rating.py` | HB/Z 84 当量齿轮法 σH/σF |
| 无载接触 | `straight_tca.py`、`generated_tca.py` | （可扩展）接触椭圆/接触点 |
| 承载接触 | `*_ltca.py`、`generated_ltca*.py` | （可扩展）Hertz 接触压 |
| 对比 | `contact_comparison.py` | 与论文算例对拍 |

**借鉴点**

- 它已经把「**几何 → 啮合力 → 标准强度 → TCA/LTCA → 与商业软件(MASTA)对标**」这条链完整工程化，并用 `examples/*.json` 保存可复现算例（如 17/47 弧齿锥齿轮，me=4 mm、de2=188 mm、b=29.988 mm、Σ=90°）。本项目要做的就是**把「锥齿轮」换成「面齿轮」，把标准换成 HB/Z 84**。
- README 全中文 + 英文双语、单位统一为 SI（长度 m、角度 rad、压力 Pa），结果可导出 JSON/NPZ/CSV/PNG/SVG —— 这是**面向工程交付而非论文 demo** 的写法，值得作为本项目文档与输出格式的模板。
- 同一作者的 `gear-transmission-skills`（v0.7.0）把上述内核封装成 **Agent Skills**（自然语言调用计算内核 + 独立复算 + 来源哈希校验），是「计算内核 + agent 前端」的现成架构参考。

**局限**：AGPL-3.0（强传染性，闭源分发不可用其代码）；仅锥齿轮；体量小、单作者、无社区验证。

---

### 3.5 `Lilililiyyy/Cylindrical-Gear-LTCA` + `hanslhansl/din3990` — 「接触压」与「标准实现」的两个补充

- **`Lilililiyyy/Cylindrical-Gear-LTCA`**（0 star，AGPL-3.0，Python，最后推送 2026-11-13，132 文件）：`gear_contact/{surfaces,iso_contact,strength}.py` 三件套 = 齿面离散 + ISO 6336:2006 接触/齿根强度 + 半解析 LTCA。其 `examples/results/validation/masta_comparison.json` 提供了**与商业软件 MASTA 的逐项对标**思路，可作为本项目「与论文算例/有限元对拍」的流程范本。README 明确「评级因子由用户提供」——即它把 K 因子表留在外部，这与本项目「简化系数表法」需要用户/论文给系数的定位一致。
- **`hanslhansl/din3990`**（0 star，MIT，Python）：**DIN 3990-5 / -11** 实现，11 个文件、结构极简（`din3990/din3990_1.py`、`din3990_5.py`、`din3990_11.py`）。MIT 许可证 + 代码量小 = **最适合直接读通透并借用的「欧标承载能力」参考实现**，用于和 HB/Z 84 的简化系数做对照。

### 3.6 次重点：中文/教学向实现

- **`ToumaTouko/gear-calc`**（1 star，MIT，单文件 HTML，最后推送 2026-10-03）：按《机械设计》(第 11 版) 教材逐条实现 `Y_Fa`/`Y_Sa`（表 10-5 查表+线性插值）、`Z_E`（表 10-6）、`Z_H`/`Z_ε`、`Y_ε`、**σH（式 10-10）**、**σF（式 10-6）**，并反算最小模数/最小分度圆。它的价值在于：**「系数表 + 插值 + 公式链 + 计算书导出」的产品形态，与本项目「简化系数表法」几乎同构**，且 MIT 许可可自由借鉴；同时它证明了「把公式溯源写在界面上」是这类工具的核心卖点。
- **`serdevir91/gearbox-web`**（0 star，最后推送 2026-09-09）：`src/math/din3990GearMath.ts` 是一份**可读的 TypeScript DIN 3990 实现**，配 `StressComparisonChart.tsx`；适合做 Web 前端型计算器的参考（本项目若走 Web UI）。
- **`AndreaBlengino/gearpy`**（5 star，GPL-3.0，最新 release **1.3.1**）：**传动系统动力学**（电机、齿轮、轴、轴承的功率流/惯量/效率），**不含强度评级**。可作为本项目后续「动力学特性分析」扩展（对应靳广虎论文的动力学部分）的候选依赖。

---

## 4. 结论

### 4.1 是否存在现成的「面齿轮应力计算」开源实现？

**没有。** 证据链如下（三层交叉验证）：

| 验证层 | 方法 | 结果 |
|---|---|---|
| 仓库元数据 | 37 个 query、289 个去重仓库 | 命中面齿轮关键词的仅 9 个，其中最相关的 3 个分别是：几何建模（RatioLab）、在机测量（omm_software）、**空仓库**（Inverse-calculation-of-meshing-equation）；`"face gear" stress`、`"spur face gear"`、`"face gear drive"`、`面齿轮 强度`、`面齿轮 展成` **均为 0 命中** |
| 代码内容 | 9 个 query、407 个命中仓库逐仓归类 | `面齿轮 强度` 的 192 个命中全部是词库/题库/汉化文档/专利文本，**无任何应力计算代码**；`"face gear" language:Python` 只命中 RatioLab 的纯几何文件 |
| 全平台 | GitLab 7 个 query | 0 个相关项目 |

唯一真实的面齿轮代码实现 **RatioLab** 的能力边界白纸黑字：「**No strength, wear, durability, allowable load, industrial conformity** … is implied」（`docs/technical/face-gears.md`）与「do not certify strength, service life or manufacturing readiness」（README）。

同时，**HB/Z 84（航空齿轮承载能力计算）在 GitHub 上没有任何代码实现**——`GB/T 3480` 只命中文档类仓库，`ISO 6336`/`AGMA`/`DIN 3990` 的实现全部针对圆柱齿轮（见 §3.2–3.5），无一条覆盖面齿轮。

### 4.2 本项目填补什么空白

1. **标准空白**：把 **HB/Z 84 当量齿轮法** 从论文里的公式与系数表，变成**可执行、可复算、可对拍**的软件。GitHub 上没有 HB/Z 84 的实现，也没有任何「面齿轮 + 航标」组合的公开代码。
2. **对象空白**：现有强度实现全部是圆柱/锥齿轮。面齿轮的关键差异——**齿宽方向载荷分配不均、内外端齿高/齿厚变化、当量齿数沿齿宽变化**——没有开源代码处理过。RatioLab 能把面齿轮齿面算出来，但不算受载。
3. **闭环空白**：没有任何开源项目把「面齿轮几何 → 载荷 → σH/σF → 强度校核」连成一条链。RatioLab 有前半段（几何+力），python-gearbox/GEARpie/Bevel-Gear-Design 有后半段（强度+接触），**中间缺一环**，正是本项目的落点。
4. **可直接借力的现成资产**（降低开发成本）：
   - 公式与因子链组织：`python-gearbox`（MIT，可安全借鉴实现思路与 API 设计）
   - 面齿轮啮合几何与数值认证范式：`RatioLab`（GPL，只能读算法/文档，不能复制代码）
   - 同类软件的工程形态（算例 JSON、结果导出、中英双语文档、与商业软件对标流程）：`Bevel-Gear-Design` / `Cylindrical-Gear-LTCA`（AGPL，只能读）
   - 系数表 + 计算书导出的产品形态：`gear-calc`（MIT，可借鉴甚至复用前端思路）

### 4.3 建议的复用策略（按许可证分层）

| 层 | 可用来源 | 许可证约束 | 建议 |
|---|---|---|---|
| 公式/算法思路、文档语义 | 任何仓库 | 著作权不保护「思想/公式」，但**不要复制代码与文字** | 可放心参考；引用时给出处 |
| 直接调用/改写代码 | `python-gearbox`(MIT)、`GEARpie`(MIT)、`gear-calc`(MIT)、`din3990`(MIT) | MIT：保留版权声明即可商用 | 优先在这些项目上做「面齿轮当量齿轮」适配 |
| 仅阅读、不可复制 | `RatioLab`、`Bevel-Gear-Design`、`Cylindrical-Gear-LTCA`、`gear-transmission-skills`（全部 AGPL-3.0） | AGPL：网络分发也触发开源义务；闭源产品**禁止链接/复制** | 只读其算法与文档，用 MIT 项目重写等价实现 |
| 无许可证仓库 | `heartworm/py_gear_gen`、`omm_software`、`AxisForge`、`shirudapratik…`、`serdevir91/…`、`git-akai/gearcalc`、`kaziwafeeq-afk/…` | **无许可证 = 保留所有权利**，默认不可复用 | 只可阅读；如需复用必须联系作者取得授权 |

---

## 5. 依赖 / 许可证注意事项

1. **AGPL-3.0 是最大陷阱**：`RatioLab`、`Bevel-Gear-Design`、`Cylindrical-Gear-LTCA`、`gear-transmission-skills` 恰好是**与本项目最相关**的四个仓库，但全部是 AGPL-3.0-only。若本项目（面齿轮应力计算软件）计划**闭源销售或仅提供二进制**，则：
   - 不可 `import` / 链接其代码；
   - 不可复制其源码片段（即使改了变量名）；
   - 只可阅读其算法描述、公式推导与文档，用自有实现重写，并注明「算法思路参考自 X」。
2. **MIT 项目是安全区**：`python-gearbox`、`GEARpie`、`gear-calc`、`din3990` 全部 MIT，可商用、可修改，只需保留原始版权与许可声明。建议把「ISO/DIN 因子链」的实现参考锚定在 `python-gearbox`（MIT）而非 AGPL 项目上。
3. **无许可证的仓库默认不可用**：GitHub 上「无 LICENSE」不等于「随便用」。表格中 `未声明` 的仓库（含 ★39 的 `heartworm/py_gear_gen`）默认保留所有权利，仅可阅读。
4. **GPL-3.0 与 AGPL-3.0 的区别**：`gearpy`、`e-dub/pygear` 是 GPL-3.0（分发二进制才触发开源义务），`RatioLab` 等是 AGPL-3.0（**提供网络服务即触发**）。若本项目是 Web 服务形态，GPL 项目相对可用、AGPL 项目不可用。
5. **数据/工程依赖**：
   - `python-gearbox` 的 FEM 部分依赖外部 **CalculiX**（`ccx` 需在 PATH，或设 `GEARBOX_CCX`），仅需强度计算时无此依赖。
   - `GEARpie` 依赖 **gmsh** Python API + numpy/scipy/matplotlib。
   - `RatioLab` 桌面端打包了 Python/GTK，Web 端需要 WebAssembly/WebGL2；其几何内核为 Rust（`rust/geometry-kernel`）。
   - 若要复现 `python-gearbox` 的 FEM 对拍，需要额外安装 CalculiX 与 gmsh，建议把这一部分列为**可选依赖**（`pip install "python-gearbox[fem]"` 的同类做法）。
6. **引用规范**：`python-gearbox` 有 Zenodo DOI（`10.5281/zenodo.3660526`），若本项目在其基础上做适配并发表论文，应引用该 DOI；`RatioLab` 的算法依据是两份 NASA 报告（NASA/CR-2000-209909、NASA/CR-2005-213443），引用原始报告而非仓库更合适。

---

## 6. 检索局限与对任务书先验信息的更正

### 6.1 先验信息更正（重要）

| 任务书中的说法 | 实测结果 | 证据 |
|---|---|---|
| `AndreaBlengino/gearpy` 的 releases 有 **v0.4.0** | v0.4.0 确实存在，但**已是历史版本**；最新 release 为 **1.3.1**，共 14 个 tag：`1.3.1, 1.3.0, 1.2.0, 1.1.0, v1.0.0, v0.7.2, v0.7.1, v0.7.0, v0.6.0, v0.5.0, v0.4.0, v0.3.0, v0.2.0, v0.1.0` | `work/github/raw_repos/AndreaBlengino__gearpy/releases.json` |
| 「Python 生态：gearpy、**pygears**」 | `pygears`（★146）是 **FPGA/ASIC 硬件设计框架**，与齿轮无关，属同名误判 | `work/github/raw/pygears.json` |
| `vanillawang22-code/Inverse-calculation-of-meshing-equation`（面齿轮刀具齿廓逆向求解） | 仓库**为空**：`gh api .../git/trees/main` 返回 `Git Repository is empty (HTTP 409)`，`size=0`，README 404 | `work/github/raw_repos/vanillawang22-code__Inverse-calculation-of-meshing-equation/meta.json`、`work/github/logs/verify_commands.log` |
| 「学术论文配套代码（南航/西工大/中南大学面齿轮课题组是否有开源）」 | **未检索到**。中文 query（`面齿轮` 28 命中、`面齿轮传动` 6 命中）中没有任何高校课题组的论文配套代码仓库 | `work/github/raw/face_gear_cn.json`、`face_gear_drive_cn.json` |

### 6.2 本次检索的局限（如实说明）

1. **GitHub 代码搜索的短语语义不可靠**：`"face gear"` 返回 8528 个结果，明显超出真实语义范围（GitHub 会做词元级匹配）。因此代码搜索的 **total_count 不能作为「有多少实现」的证据**，本文的结论全部基于**逐仓归类**（`logs/code_aggregate.txt`）。
2. **`HB/Z 84` 代码检索失效**：GitHub 代码搜索丢弃 `/` 与空格，该 query 退化为宽泛匹配（86784 命中），无参考价值。HB/Z 84 的「无实现」结论来自：仓库搜索 `GB/T 3480` 仅 2 个文档仓库、`ISO 6336` 的 8 个命中逐条排查无航标实现、中文 `面齿轮 强度` 逐仓归类无代码。
3. **代码搜索只覆盖默认分支且不含非 ASCII 之外的冷门文件类型**，私有仓库不可见；若存在未公开/未打 tag 的课题组代码，本调研无法发现。
4. **star 数的时效性**：小仓库（0–7 star）star 数波动无意义；本文以「最后推送时间」作为活跃度的主要判据。
5. **未覆盖的平台**：仅补充了 GitLab（0 命中），未检索 Gitee、GitCode、开源中国等国内平台——若需要「国内面齿轮课题组是否有 Gitee 开源」，建议追加一轮 Gitee 检索。

---

## 附录：产物清单（`work/github/`）

| 文件 | 内容 |
|---|---|
| `search_repositories.py` | 37 个仓库检索 query 的执行脚本（可重跑） |
| `raw/*.json` | 37 份 GitHub Search API 原始响应 |
| `logs/search_commands.log` | 每条 query 的实际命令、返回 total_count/items、落盘路径 |
| `code_search.py` / `raw_code/*.json` | 9 个代码检索 query 及原始响应 |
| `logs/code_commands.log` | 代码检索命令记录 |
| `aggregate.py` / `candidates.json` | 289 个去重仓库的字段快照 + 相关性打分 |
| `logs/aggregate_dump.txt` | 全量仓库人读清单 |
| `aggregate_code.py` / `logs/code_aggregate.txt` | 407 个代码命中仓库的逐仓归类 |
| `inspect_candidates.py` / `logs/inspect_filtered.txt` | 按 A–F 六类定向筛选的候选清单 |
| `gear_named_repos.py` / `logs/code_gear_named_repos.txt` | 名称含 gear/face 的代码命中仓库 |
| `verify_repos.py` / `raw_repos/<owner>__<repo>/` | 20 个落脚仓库的 meta / 文件树 / releases / README 原文 |
| `verified_repos.json` | 20 个仓库的核实字段汇总（本文表格数据源） |
| `logs/verify_commands.log` | 复核命令与结果（含失败项原因） |
| `check_releases.py` | release/tag 核实（含 gearpy v0.4.0 澄清） |
| `fetch_files.py` | 关键文档/源码抓取 |
| `gitlab_search.py` / `raw_gitlab/*.json` / `logs/gitlab_commands.log` | GitLab 补充检索记录 |
| `make_table.py` / `logs/table_skeleton.md` | 由核实数据自动生成的表格骨架（保证数字与 API 一致） |

本文写作原则：**表格中的每个 star / 许可证 / 推送时间都可追溯到 `raw_repos/` 下的原始 JSON**；凡是未能证实的（如空仓库、未检索到的课题组代码），一律写明「未检索到 / 仓库为空」，不以推测填充。
