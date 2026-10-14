# laRkdown

面向研究者的入门步骤与日常用法见 [使用指南](USER_GUIDE.md)。该文档随每个发行版本更新并进入产品 ZIP。

## 一句话交给豆包工作

在能够访问本地文件并运行命令的豆包工作任务中，复制发送：

> 请读取 https://raw.githubusercontent.com/Zzzombee/laRkdown/main/README.md 并安装最新版 laRkdown。把包含 `.agents/skills/` 的目录作为当前项目打开，确认六个技能可用，配置 Python 与官方飞书 CLI，并引导我完成飞书授权。

也可在这句话末尾补充目标文件夹路径。用户只需提供必要的目录或项目信息，并亲自完成账户授权；下面的安装与检查由豆包执行。

## 项目概述

laRkdown 是面向 **豆包工作 + 飞书原生文档 + Python** 的科研进度管理工具，由 [maRkdown](https://github.com/Zzzombee/maRkdown) 的科研工作流适配而来。包含四个上游适配技能：学术写作编辑、研究状态维护、实验 PPTX 提取、外部文献门槛；另有“科研文档转多维表格”和“已有项目升级”两个 laRkdown 原生扩展，共六个技能。

飞书文档保存正式科研记录，Python 完成材料提取与结构校验，豆包工作按技能组织任务并调用工具。观察、结论、假设、研究问题和候选路线以稳定编号关联。技能指令使用普通 Markdown，工作稿使用 DocxXML/JSON；项目关联使用真实飞书文档与块链接。

**引用版本：** [maRkdown v0.1.0](https://github.com/Zzzombee/maRkdown/releases/tag/v0.1.0)，源码提交 [a189bd0755a2d1a097b0a1c6f5f5c5712135d616](https://github.com/Zzzombee/maRkdown/commit/a189bd0755a2d1a097b0a1c6f5f5c5712135d616)。这是固定版本适配，不自动跟随上游 main。内部来源及逐文件记录见 [upstream.json](.agents/config/upstream.json)。

## 给豆包工作的安装指引

按顺序执行，复用已有环境。**豆包当前打开的项目根目录须直接包含 `.agents/skills/`。**

### 1. 下载并确定工作目录

- 从 [laRkdown Releases](https://github.com/Zzzombee/laRkdown/releases) 获取最新发行 ZIP 和同名 `.sha256`，核对校验值后解压；GitHub 页面不可读时可用 `gh release download --repo Zzzombee/laRkdown --pattern '*.zip' --pattern '*.sha256'`。在豆包中打开解压所得、直接包含 README.md、AGENTS.md 和 `.agents/skills/` 的目录。
- 若当前项目根目录外还有一层 `laRkdown/`，直接打开内层目录。同名目录已存在时先检查内容，保留其中的科研资料和本机配置。
- 在打开的项目根目录读取 AGENTS.md、目录合同和飞书工作流；后续脚本也在此目录运行。

### 2. 检查六个科研技能

在**豆包当前打开的项目根目录**检查以下六个完整文件夹，保留 SKILL.md 及其 references、scripts 和许可文件：

```text
.agents/skills/academic-writing-editor/
.agents/skills/maintain-research-state/
.agents/skills/pptx-to-research-state/
.agents/skills/literature-source-gate/
.agents/skills/research-docs-to-base/
.agents/skills/upgrade-larkdown/
```

刷新或重开项目，确认六个技能可选或可加载。若未识别，先核对项目根目录，再使用当前豆包客户端提供的本地技能导入入口；不要假定某个用户技能目录在所有设备上通用。保留各技能完整目录及已有同名用户文件。

### 3. 配置 Python 与飞书 CLI

复用已有环境；缺少 Python 3.11+ 或 Node.js/npm 时按官方说明安装。

推荐在项目内创建 `.venv/`，避免与其他项目依赖混用：

```text
python -m venv .venv
```

Windows 使用 `.venv/Scripts/python.exe -m pip install -r requirements.txt`；macOS/Linux 使用 `.venv/bin/python -m pip install -r requirements.txt`。之后科研脚本使用该环境的 Python。

安装并读取官方 CLI 当前帮助：

```text
npx @larksuite/cli@latest install
lark-cli --version
lark-cli skills read lark-shared
lark-cli skills read lark-doc
lark-cli skills read lark-wiki
lark-cli skills read lark-base
```

运行时以当前官方内嵌技能和 `--help` 为准。[官方 CLI 安装与 Agent 指引](https://github.com/larksuite/cli/blob/main/README.zh.md)

### 4. 完成飞书用户授权

- 先 `lark-cli auth status --json`，复用现有有效用户身份。
- 尚未配置应用时，按[官方指引](https://github.com/larksuite/cli/blob/main/README.zh.md)运行 `lark-cli config init --new --brand feishu`。
- 缺少用户授权时，按要使用的功能运行 `lark-cli auth login --domain docs,drive,wiki,base --no-wait --json`，向用户展示实际授权链接或二维码；用户完成后运行 `lark-cli auth login --device-code <本次实际返回值>` 并复查状态。
- 默认 `--as user`。密钥与 token 留在 CLI 认证存储中，不写入项目。

用户本人完成扫码或浏览器授权，豆包执行后续命令。[飞书原生工作流](.agents/instructions/feishu-workflow.md)

### 5. 验收并交付配置结果

- 确认六个技能在豆包中可选，运行 `python upgrade_larkdown.py --help` 和 `python .agents/skills/maintain-research-state/scripts/feishu_bridge.py --root . preflight`。
- 交付项目目录、技能状态、Python/CLI 状态及实际缺口。仅在需要端到端验证飞书写入时创建测试文档；使用 PPTX 功能前再验证本机渲染与图片读取能力。

完整工作流需要能访问本地文件并运行命令的豆包工作任务。[豆包工作官方说明](https://www.feishu.cn/content/article/7677519271848610746)

## 开始科研工作

完成配置后，发送：

> 研究工作目录是“我的项目路径”。使用 laRkdown 初始化空白飞书科研记录。研究体系名称：……；研究范围：……。新建同名飞书知识空间，并在其中创建“项目现状”“项目故事”“研究问题”三篇文档；已有记录时先绑定其飞书链接并进行增量维护，完成后返回文档链接。

初始化先准备 XML，再在与研究体系同名的新知识空间内直接发布 CURRENT_STATE、PROJECT_STORY、RESEARCH_QUESTIONS 三篇空白原生文档，其可见标题依次为“项目现状”“项目故事”“研究问题”。此时“项目故事”只是空白框架，可以在录入初步事实与问题后要求豆包生成初稿。已有记录不重复初始化。日期采用用户时区当天日期，研究范围只使用用户提供的信息。新同事接手时给出已有科研文档链接并绑定，不另建一套记录。

刚做完实验时，可以直接把过程和结果告诉豆包，无需先制作 PPTX 或整理成报告。例如：

> 我刚做完实验：做了……，观察到……，对照/重复情况是……。请立刻把已知事实整理进知识库文档“项目现状”，区分观察、结论和待验证假设；缺失的关键参数标注待补，写后给我文档链接。

没有完整参数也可先用自然语言描述；豆包只追问会影响该项记录或判断的关键信息，已能可靠记录的部分先写入。后续可说“从这个 PPTX 提取证据并更新知识库文档‘项目现状’：文件路径”“根据‘项目现状’和‘研究问题’生成知识库文档‘项目故事’的初稿”或“根据这次新结果修订知识库文档‘项目故事’，保留证据边界”。也可以要求润色指定知识库文档，或为指定研究问题检索并核验文献。

若只问“laRkdown 怎么用”或“初始化后做什么”，豆包应先给上述即时实验记录入口，再按当前状态介绍 PPTX 导入、故事生成/修订和知识库多维表格；不因询问用法而创建或修改文档。

## 六个技能

- `academic-writing-editor`：中英文学术正文起草、改写、翻译与审阅，保护数字、引用和证据强度；默认交付飞书原生文档。
- `maintain-research-state`：将刚完成的实验与结果及时整理进知识库文档“项目现状”，并维护 OBS／CON／HYP／RQ／SOL 的稳定编号、证据关系及原生文档结构。
- `pptx-to-research-state`：提取文字、备注、表格、原生图表及原图，渲染整页并实际逐图读取后更新科研记录；也支持不依赖 PPTX、根据已有记录生成或修订“项目故事”。
- `literature-source-gate`：区分用户指定文献与自主检索，核验来源、主张匹配、指标、例外与受限来源警示。
- `research-docs-to-base`：从三篇知识库文档构建/同步六表知识库多维表格，展示概要、清理后的原文与独立引用列；隐藏同步技术字段，保留稳定编号和提及关联；预览增量差异，缺失条目归档，保护 AI 与人工协作字段。
- `upgrade-larkdown`：对已经初始化的科研项目预览版本差异、处理托管文件冲突并执行可恢复的原位升级。

## 已有项目升级

把新版本完整 ZIP 下载并解压在**已有科研项目目录之外**。从新包运行 `upgrade_larkdown.py`，先预览，再按用户的升级指令应用：

```text
python <新包目录>/upgrade_larkdown.py --project <已有科研项目目录> --package <新包ZIP>
python <新包目录>/upgrade_larkdown.py --project <已有科研项目目录> --package <新包ZIP> --apply
```

已有升级器的项目也可使用 `--latest`，读取 GitHub 最新公开 Release 并校验资产 SHA256；API 限流时使用公开校验附件。v0.1.0/v0.2.0 项目没有升级器，首次从下载的新包执行。升级器更新发行版托管文件，保留项目本机配置、飞书文档登记、科研资料和多维表格同步基线。AGENTS.md 中不重叠的用户增补会合并；重叠编辑及其他被修改的托管文件列为冲突，不自动覆盖。中断时运行 `--recover`。更新后确认豆包实际打开的项目根目录直接包含 `.agents/skills/`，刷新项目并检查六个技能；根目录正确但仍未识别时再按客户端入口导入。详细规则见 [UPGRADING.md](UPGRADING.md)。

## 知识库文档转知识库多维表格

导入新增的 [research-docs-to-base](.agents/skills/research-docs-to-base/SKILL.md) 完整技能目录后，可交给豆包：

> 工作目录是“我的项目路径”。使用 laRkdown 的 research-docs-to-base 技能，把已登记的“项目现状”“研究问题”“项目故事”三篇知识库文档构建为知识库多维表格；把新多维表格放在同一研究知识空间内，每条展示简短概要、清理后的原文与单列引用，隐藏同步技术字段，完成后给我表格链接。

尚未登记时附三个实际文档链接。可追加“使用这个空白母版的新副本：实际链接”或“同步到已有知识库多维表格：实际链接”；没有指定时创建新知识库多维表格。日后发送“同步知识库多维表格”；只查看差异则发送“预览知识库多维表格的变化”。同步指令授权相应写入，预览只读。

六表为项目概览、实验观察OBS、结论与假设、研究问题RQ、关键参考文献、近期优先事项。已登记研究知识空间时，新建的 Base 迁入该空间，与三篇文档同级；用户指定的已有 Base 不自动移动。每张表提供概要、原文、引用，概要默认使用去编号的源标题或任务首句；原文不重复编号、来源和独立引文行。技术同步字段为增量更新所需，保留但在阅读视图隐藏。文档仍是事实源，表格是协作视图，不回写原文。AI 核心发现、层级、类型及人工备注不覆盖；源类型和源证据等级单独保存。文献按 DOI/链接去重，序号只用于展示。全文读取失败或发生人工修改冲突时停止；源条目消失只归档已管理的行。

本机设置保存 `.agents/config/research-base.local.json`，示例在技能 assets；基线、快照和中断日志在 `.work/research-base/`，均不发布。不带同步身份的旧表记录不自动接管，迁移前需明确对应关系。图片/附件保留源定位，表格文字不能替代图片判读。新 Base 不自动配置 AI 字段。

## 图片提取的完成条件

PPTX 的结构提取、原图保留、整页渲染和实际视觉核验分开记录。PNG/JPEG/TIFF 等可解码图片生成查看代理，多帧与显示映射保留；精确像素仍来自原图。小字、多 panel 和密集曲线须读局部图，不能从标题或 OCR 自动推定图形结果。

脚本验收包含源 hash、页覆盖、原图完整性与视觉台账。台账通过不证明实际识图正确。当前版本不承诺豆包客户端自动逐页读图；初次部署须用代表性实验 PPTX 实测其图片入口和识别准确率。云环境缺少 PowerPoint 时不宣称完整提取已完成。

## 正式记录与协作

飞书为正式事实源，修改前读最新正文与版本，局部修改后回读。稳定研究 ID 与飞书 block ID 分开；结构修改后更新块定位。保护同事编辑、评论和图片资源，不自动整篇覆盖。

`.agents/config/feishu.example.json` 是配置示例；实际本机配置为 feishu.json，文档登记为 feishu-documents.json，均不进入版本控制。工作稿和快照进入 `.work/`，正式文档链接和验收记录进入 `outputs/reports/`。

## 来源与验证

本源码版本为 laRkdown v0.2.5，包含知识库文档与多维表格、即时实验记录引导、项目故事入口及已有项目升级器。上游引用版本见“项目概述”；官方资料和核验日期见 [official-sources.json](.agents/config/official-sources.json)。公开发行包不包含实验数据、账户凭证、飞书资源登记和本机快照。

CLI 用法按本机 1.0.97 的官方内嵌技能核验，运行时以当前 `lark-cli --help` 与 `lark-cli skills read` 为准。学术编辑技能保留其第三方 MIT LICENSE；不将该许可推定为其他文件的统一许可。
