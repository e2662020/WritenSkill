---
name: screenplay-engine
description: "系统性剧本创作与诊断引擎：融合麦基《故事》(AAA)、菲尔德《电影剧本写作基础》(AA)、斯奈德《救猫咪》(A)、HBO大师课等理论，内置SPL剧本标记语言（可渲染标准格式剧本PDF）、剧本医生双重检查（格式校验+十维诊断）与21部经典电影剧本的逐拍拆解范例（嚼碎的电影剧本）。用于创作/续写/改写电影长片、短片、剧集、短剧剧本，一句话故事Logline、三幕结构、15节拍表、五诫命、人物设计与弧光、对白打磨、场景拆解、类型套路、世界规则、剧本诊断与返工。用户提到写剧本、剧本、故事大纲、分场、人物小传、对白、节拍表、三幕、类型片、剧本医生、诊断剧本、Logline、一句话故事、渲染剧本PDF时使用。"
license: MIT
metadata:
  author: doubao
  version: "1.1.0"
---

# 剧本引擎 Screenplay Engine

系统性剧本创作与诊断引擎。以「概念 → 结构 → 人物 → 场景 → 对白 → 正文 → 诊断」七级流水线组织创作；正文强制使用 **SPL 剧本标记语言**（可渲染为行业标准格式的剧本 PDF）；交付前由**剧本医生**执行双重检查（格式校验 + 十维内容诊断）；以**嚼碎的电影剧本**为写作参照系。

## 原则优先级（书籍等级）

方法论发生冲突时按以下等级裁决：

- **AAA**：麦基《故事：材质、结构、风格和银幕剧作的原理》——因果与价值逻辑为最高准则
- **AA**：菲尔德《电影剧本写作基础》、《写作兵器库：故事创意指南》——结构框架与推演法次之
- **A**：斯奈德《救猫咪》、HBO《如何写出好故事》、《剧本：影视写作的艺术》——实操技巧（节拍位置等）可调整

**方法优先于技术**：大师的方法（结构/人物/对白/情感/观众）决定故事质量；SPL 语法、渲染器、校验器只是执行工具，绝不让格式反过来束缚创作。

## When to Use

### Must Use（必须使用）

- 创作、续写、改写、扩写任何影视剧本（电影长片 / 短片 / 剧集 / 短剧）
- 产出故事大纲、三幕结构、15节拍表、分场大纲、序列大纲
- 设计人物（小传、弧光、欲望、角色关系网、反派）
- 打磨对白（潜台词、语言行动、人物声音）
- 拆解或重构某一场景的价值转折
- 诊断已有剧本、找出结构/人物/对白问题并返工
- 需要类型套路参考或一句话故事（Logline）设计
- 把剧本渲染为行业标准格式 PDF

### Recommended（建议使用）

- 用户只有模糊灵感，需要被引导出完整故事
- 用户反馈"剧情平淡 / 人物扁平 / 对白尴尬 / 节奏拖沓"，原因不明
- 需要参照某部经典影片的结构来组织自己的故事

### Skip（无需使用）

- 小说、网文正文写作（但三幕/人物方法可借鉴）
- 纯文案、新媒体内容
- 非虚构报道 / 纪实写作

**判断准则**：只要产出物是「拍出来能看的戏」——有场、有动作、有对白、有冲突——就使用本技能。

## 核心规则（不可违反）

### 用户与 Agent 分工

- 用户提供想法、偏好、已有材料和不可修改的设定；Agent 负责全部专业推导，不要求用户填理论表格。
- 信息不足时，只问「当前步骤无法合理推断且会改变故事方向」的问题，一次最多问 3 个。
- 逐步推进：每步先生成可修改方案，再让用户选择 `[通过 / 修改 / 自检]`。当前步骤未通过，不进入下一步。

### 主角与主线

- 整体梗概必须以主角为主语，用主角行动组成因果链。
- 主线定义：主角因激励事件产生目标，持续行动、承受递进对抗，最终作出危机选择并完成高潮行动。
- 支线不得成为独立故事；删掉后主线完全不受影响的支线，删除或合并。
- 配角可以主动，但不能替主角发现核心真相、完成决定性选择或解决高潮。

### 可拍摄写作（电影剧本硬标准）

禁止：

- 摄影机拍不到的心理说明（"她意识到""他感到命运改变"）
- 用括号解释台词真实意图
- 人物用台词讲解双方都知道的设定（信息倾倒）
- 说教、强行煽情、空泛独白、书面化套话
- 靠临时出现的能力、密码、证据或援军解决高潮（deus ex machina）

必须：

- 用可见动作、声音、物件、空间和人物反应表达内心
- 台词口语化，但每句话执行一个「语言行动」（请求/威胁/试探/拒绝…）
- 重要信息通过冲突、交换、威胁、调查或选择进入剧情
- 高潮由主角依据「已建立的能力、信息和规则」完成；硬规则（世界观限制）不得临时突破

### 引用嚼碎剧本

- 进入任何创作阶段前，先查 `references/chewed-scripts/` 中与本次类型/结构最接近的拆解，将其节拍骨架与写作技法作为参照系，再落笔。
- 参照的是结构与方法，不是情节（禁止抄袭人物关系与事件设计）。

## SPL 快速语法（正文强制格式，完整规范见 references/spl-spec.md）

```markdown
---
title: 剧本标题          # frontmatter：title 必填
author: 作者
type: feature            # feature/short/series/short-drama
genre: 剧情
runtime: 120分钟
logline: 一句话故事
---

> FADE IN:               # 转场：> 命令，渲染右对齐

# INT. 咖啡馆 - 夜 [1]   # 场景标题：# + INT./EXT. + 地点 - 时间（可带场号）

动作段落。只写摄影机拍得到的内容。   # 普通段落=动作

**安迪**                # 独占一行 **姓名** = 角色提示（居中大写）
（低声）                # 对白内的（ ）独立行 = 括号提示（斜体）
台词内容。               # 角色提示后的段落 = 对白（居中缩进块）

## 特写 门把手          # ## = 镜头/字幕/蒙太奇标题
> CUT TO:               # 转场
---                     # 强制分页
%% 注释不渲染           # 内部备忘/伏笔登记
> FADE OUT.
```

## 标准工作流（七级流水线）

每级对应一个产出物。长片、短片、剧集按各自体量缩放（见 `references/story-structure.md`）。

| 级 | 产出 | 核心问题 | 读取文件 |
|---|---|---|---|
| 0 | 项目任务卡 | 形式/类型/受众/时长/硬约束是什么？ | — |
| 1 | 一句话故事 Logline | 它讲的是什么？想法成立吗？ | `references/logline-and-concept.md` + `references/hbo-seven-elements.md` + `references/story-framework.md` |
| 2 | 概念与类型确认 | 属于哪种类型？套路与反套路？ | `references/genre-matrix.md` |
| 3 | 人物系统 | 主角想要什么/需要什么？谁会对抗？ | `references/character-engine.md` |
| 4 | 世界观与规则 | 世界如何运转？限制什么？ | `references/story-structure.md` |
| 5 | 结构骨架 | 三幕/五诫命/15节拍如何分布？ | `references/story-structure.md` |
| 6 | 场景大纲 | 每场价值如何转折？ | `references/scene-craft.md` |
| 7 | 对白设计 | 每句台词在做什么？ | `references/dialogue-engine.md` |
| 8 | 正文写作（SPL） | 用 SPL 书写，情感与语言是否过关？ | `references/spl-spec.md` + `references/screenplay-format.md` + `references/craft-of-script.md` |
| 9 | 剧本医生 | 格式+十维诊断是否过关？ | `references/doctor.md` + `scripts/validate-spl.py` |

### 第8步补充：正文写作

1. 用 SPL 语法写正文（见上表语法与 `spl-spec.md`）。
2. 写完后立即运行格式校验：`python scripts/validate-spl.py 剧本.md`，有错就改。
3. 用户确认正文后，渲染 PDF：`python scripts/render_pdf.py 剧本.md`（输出同目录同名 .pdf）。

### 第9步补充：剧本医生双重检查

1. **第一道（格式）**：运行 `validate-spl.py`——脚本报错则返回第8步，通过才继续。
2. **第二道（内容）**：按 `references/doctor.md` 十维诊断（概念/类型/主线/结构/场景/规则/人物/对白/可拍摄性/伏笔回收），输出报告。
3. 返工路由见 doctor.md；改完重跑格式校验 + 受影响维度。

## Scripts（确定性工具）

| 脚本 | 用途 | 用法 |
|---|---|---|
| `scripts/search.py` | 检索 data/ 知识库（节拍/类型/原型/对白行动/常见坑） | `python scripts/search.py "<关键词>" --domain beats` |
| `scripts/validate-spl.py` | SPL 格式校验（剧本医生第一道） | `python scripts/validate-spl.py 剧本.md` |
| `scripts/render_pdf.py` | SPL → 标准格式剧本 PDF（封面/页眉/场景行/对白/转场） | `python scripts/render_pdf.py 剧本.md [-o 输出.pdf]` |
| `scripts/spl_to_epub.py` | SPL → EPUB 3 电子书（不嵌入字体，由阅读器选择） | `python scripts/spl_to_epub.py 剧本.md [-o 输出.epub]` |

**依赖**：`render_pdf.py` 需要 fpdf2 + fonttools（`pip install fpdf2 fonttools`）；中文字体已内置在 `assets/fonts/`（Noto Sans SC SemiBold 600 + ExtraBold 800，静态字体，fvar 已删除、所有 nameID 已修正）。`spl_to_epub.py` 无第三方依赖。

**输出目录**：未指定 `-o` 时，PDF/EPUB 默认输出到技能内 `output/` 目录。

## Data（可检索知识库）

| 文件 | 内容 |
|---|---|
| `data/beats.csv` | 15节拍 × 位置 × 功能 × 正例/反例 |
| `data/genres.csv` | 12种类型 × 价值轴 × 结构套路 × 范例 × 反类型手段 |
| `data/archetypes.csv` | 角色原型 × 需求 × 缺陷 × 弧光 |
| `data/dialogue-moves.csv` | 20种语言行动 × 定义 × 示例 |
| `data/pitfalls.csv` | 剧本常见病 × 症状 × 修法 × 严重度 |

## References（按需加载）

| 主题 | 文件 | 何时读取 |
|---|---|---|
| SPL 标记语言规范 | `references/spl-spec.md` | 第8步写正文、校验、渲染时 |
| 行业格式速查 | `references/screenplay-format.md` | 理解渲染版面、估算页数时 |
| 结构与节奏 | `references/story-structure.md` | 建结构骨架、分幕分场、处理解说与布局时 |
| 故事框架推演 | `references/story-framework.md` | 第1步从灵感推演主题-人物-世界；卡壳时 |
| 人物引擎 | `references/character-engine.md` | 人物设计、弧光、反派、关系网时 |
| 对白引擎 | `references/dialogue-engine.md` | 写对白、改对白、诊断对白时 |
| 场景引擎 | `references/scene-craft.md` | 拆解场景、设计转折时 |
| 概念与Logline | `references/logline-and-concept.md` | 第1步构思、改一句话故事时 |
| HBO 七要素 | `references/hbo-seven-elements.md` | 开工前检验想法、诊断"故事为什么不成立"时 |
| 编剧手艺 | `references/craft-of-script.md` | 写正文前校正语言观/情感观/观众观 |
| 类型矩阵 | `references/genre-matrix.md` | 定类型、查套路/反套路时 |
| 剧本医生 | `references/doctor.md` | 第9步诊断与返工时 |
| 嚼碎的电影剧本 | `references/chewed-scripts/` | 写任何一稿前，按类型就近参照片段与结构 |

## Integration

- **创作短剧/短视频脚本**：沿用本工作流，体量缩放见 story-structure 的体量表；正文仍用 SPL，渲染 PDF 即可交付分镜依据。
- **跨媒介**：小说改编影视时，先按 `references/logline-and-concept.md` 重构核心冲突，再走流水线。
- **与可视化配合**：结构骨架、人物关系网、类型分布可用图表呈现给用户。
