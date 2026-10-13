# laRkdown

## 一句话交给豆包工作

在能够访问本地文件并运行命令的豆包工作任务中，复制发送：

> 请按照 https://github.com/Zzzombee/laRkdown 的 README，将 laRkdown 安装到当前本地工作目录，导入五个科研技能并配置 Python 和官方飞书 CLI，引导我完成飞书用户授权，验收环境后告诉我如何开始使用。

也可在这句话末尾补充目标文件夹路径。用户只需提供必要的目录或项目信息，并亲自完成账户授权；下面的安装与检查由豆包执行。

## 项目概述

laRkdown 是面向 **豆包工作 + 飞书原生文档 + Python** 的科研进度管理工具，由 [maRkdown](https://github.com/Zzzombee/maRkdown) 的科研工作流适配而来。包含四个上游适配技能：学术写作编辑、研究状态维护、实验 PPTX 提取、外部文献门槛；另有 laRkdown 原生扩展“科研文档转多维表格”，共五个技能。

飞书文档保存正式科研记录，Python 完成材料提取与结构校验，豆包工作按技能组织任务并调用工具。观察、结论、假设、研究问题和候选路线以稳定编号关联。技能指令使用普通 Markdown，工作稿使用 DocxXML/JSON；项目关联使用真实飞书文档与块链接。

**引用版本：** [maRkdown v0.1.0](https://github.com/Zzzombee/maRkdown/releases/tag/v0.1.0)，源码提交 [a189bd0755a2d1a097b0a1c6f5f5c5712135d616](https://github.com/Zzzombee/maRkdown/commit/a189bd0755a2d1a097b0a1c6f5f5c5712135d616)。这是固定版本适配，不自动跟随上游 main。内部来源及逐文件记录见 [upstream.json](.agents/config/upstream.json)。

## 给豆包工作的安装指引

按顺序执行，完成已具备条件的部分。当前客户端的权限和工具可用性决定是否能自动导入技能；不声称尚未完成的安装或图片读取已经成功。

### 1. 下载并确定工作目录

- 使用用户指定的本地文件夹；未指定时，使用当前明确的本地工作目录下 `laRkdown/`。工作目录无法确定时只询问目标路径。
- 优先 `git clone https://github.com/Zzzombee/laRkdown.git`。没有 Git 时，从 [v0.2.0 Release](https://github.com/Zzzombee/laRkdown/releases/tag/v0.2.0) 下载 `laRkdown-v0.2.0.zip`，解压后定位含 README.md、AGENTS.md、requirements.txt 与 `.agents/` 的目录。
- 同名目录已存在时先检查并复用正确版本，不覆盖既有科研资料、文档登记或本机配置。保留 `.agents/` 的名称与层级。
- 在该目录读取 AGENTS.md、目录合同和飞书工作流。该目录是后续脚本与配置的工作根目录，技能平台的托管目录不是项目根目录。

### 2. 导入五个科研技能

通过当前豆包工作提供的自定义技能/本地导入入口，分别导入以下完整文件夹，保留 SKILL.md 及其 references、scripts 和许可文件：

```text
.agents/skills/academic-writing-editor/
.agents/skills/maintain-research-state/
.agents/skills/pptx-to-research-state/
.agents/skills/literature-source-gate/
.agents/skills/research-docs-to-base/
```

若当前工具能操作导入界面，完成导入并核对技能名称；界面必须由用户操作时，给出上述本地完整路径与必要点击步骤。平台将技能复制到托管目录后，仍从研究工作根目录定位共享规则和脚本。不要猜测豆包私有技能目录或注册协议，不把复制文件当作平台导入成功。

确认五个技能可选或可加载。平台要求刷新或重开任务时按实际提示操作；新任务再次明确工作目录并读取 AGENTS.md。在不能导入的环境，可显式读取项目中对应 SKILL.md 试运行，但须标明尚未完成平台注册。

### 3. 配置 Python 与飞书 CLI

复用已有合格环境。缺少 Python 3.11+ 或 Node.js/npm 时按各自官方安装方式补齐；需要用户安装权限时明确指出所需操作。只安装本项目所需依赖。

推荐在项目内创建 `.venv/`，避免与其他项目依赖混用：

```text
python -m venv .venv
```

Windows 使用 `.venv/Scripts/python.exe -m pip install -r requirements.txt`；macOS/Linux 使用 `.venv/bin/python -m pip install -r requirements.txt`。之后科研脚本使用该环境的 Python。不同系统的 Python 启动命令按实际环境解析，记录可用路径即可。

安装并读取官方 CLI 当前帮助：

```text
npx @larksuite/cli@latest install
lark-cli --version
lark-cli skills read lark-shared
lark-cli skills read lark-doc
```

运行时以当前官方内嵌技能和 `--help` 为准。不要将第三方同名工具代替官方 `lark-cli`。[官方 CLI 安装与 Agent 指引](https://github.com/larksuite/cli/blob/main/README.zh.md)

### 4. 完成飞书用户授权

- 先 `lark-cli auth status --json`，复用现有有效用户身份。
- 仅在尚未配置应用时，按当前官方指引执行 `lark-cli config init --new --brand feishu`。该命令需要浏览器配合，后台运行并及时向用户展示实际授权 URL 与二维码；不要在等待期间隐藏链接。已有应用或受管理的 Agent 环境按官方绑定流程处理。
- 用户身份缺少授权时，执行 `lark-cli auth login --domain docs,drive --no-wait --json`，把实际 URL 与二维码交给用户。用户完成后由豆包执行 `lark-cli auth login --device-code <本次实际返回值>`，再检查登录状态。
- 默认 `--as user`，只为本任务申请所需权限。额外目录或功能确实需要其他 scope 时依据实际错误处理。密钥与 token 保留在 CLI 认证存储中，不写入项目或 README；本次授权码不作为长期配置保存。

认证二维码使用当前 CLI 的 `auth qrcode`；链接不改写。用户本人完成扫码/浏览器授权，豆包执行后续命令。[飞书原生工作流](.agents/instructions/feishu-workflow.md)

### 5. 验收并交付配置结果

- 用项目环境运行 `python -m unittest discover -s tests -v`（将 python 替换为实际 `.venv` Python）。
- 运行 `python .agents/skills/maintain-research-state/scripts/feishu_bridge.py --root . preflight`，确认用户身份可用；不要打印认证密钥。
- 创建一篇简短的飞书原生“laRkdown 安装验收”文档并回读，确认正文和真实 URL。保留同一文档，失败时修复它，避免重复创建；不自动改共享权限或发送消息。
- PPTX 功能另检查 Windows、PowerShell、桌面 PowerPoint 与当前豆包视觉工具。缺少条件时标明“PPTX 图片完整导入待配置”，先交付其他功能的配置结果。
- 最后交付本地工作目录、五个技能导入状态、Python/CLI 可用状态、飞书验收链接和具体缺口。不因为环境配置完成就自动建立科研记录。

仅有云端问答且不能读写本地文件或运行命令的入口，无法执行当前完整版本；需使用具备这些工具的工作任务环境。豆包官方描述支持自定义技能与附带资源，但具体入口和开放能力以当前账号为准。[豆包工作官方说明](https://www.feishu.cn/content/article/7677519271848610746)

## 开始科研工作

完成配置后，发送：

> 研究工作目录是“我的项目路径”。使用 laRkdown 初始化空白飞书科研记录。项目名称：……；研究范围：……。已有记录时先绑定其飞书链接并进行增量维护，完成后返回文档链接。

初始化先准备 XML，再发布 CURRENT_STATE、RESEARCH_QUESTIONS、PROJECT_STORY 三篇空白原生文档。已有记录不重复初始化。日期采用用户时区当天日期，研究范围只使用用户提供的信息。新同事接手时给出已有科研文档链接并绑定，不另建一套记录。

日常可以要求“从指定 PPTX 更新研究状态”“将这次结果区分为观察、结论与假设”“润色这篇飞书文档，保留数字和引用”或“为这个问题检索并核验文献”。

## 五个技能

- `academic-writing-editor`：中英文学术正文起草、改写、翻译与审阅，保护数字、引用和证据强度；默认交付飞书原生文档。
- `maintain-research-state`：维护 OBS／CON／HYP／RQ／SOL 的稳定编号、证据关系及原生文档结构。
- `pptx-to-research-state`：提取文字、备注、表格、原生图表及原图，渲染整页并实际逐图读取后更新科研记录。
- `literature-source-gate`：区分用户指定文献与自主检索，核验来源、主张匹配、指标、例外与受限来源警示。
- `research-docs-to-base`：从三篇飞书科研文档构建/同步六表科研工作台，保留来源、稳定编号和提及关联；预览增量差异，缺失条目归档，保护 AI 与人工协作字段。

## 科研文档转多维表格

导入新增的 [research-docs-to-base](.agents/skills/research-docs-to-base/SKILL.md) 完整技能目录后，可交给豆包：

> 工作目录是“我的项目路径”。使用 laRkdown 的 research-docs-to-base 技能，把已登记的 CURRENT_STATE、RESEARCH_QUESTIONS、PROJECT_STORY 三篇飞书文档构建为多维表格科研工作台，保留原文、来源和关联，完成后给我表格链接。

尚未登记时附三个实际文档链接。可追加“使用这个空白母版的新副本：实际链接”或“同步到已有工作台：实际链接”；没有指定时创建新工作台。日后发送“同步科研工作台”；只查看差异则发送“预览科研工作台变化”。同步指令授权相应写入，预览只读。

六表为项目概览、实验观察OBS、结论与假设、研究问题RQ、关键参考文献、近期优先事项。文档仍是事实源，表格是协作视图，不回写原文。AI 核心发现、层级、类型及人工备注不覆盖；源类型和源证据等级单独保存。文献按 DOI/链接去重，序号只用于展示。全文读取失败或发生人工修改冲突时停止；源条目消失只归档已管理的行。

本机设置保存 `.agents/config/research-base.local.json`，示例在技能 assets；基线、快照和中断日志在 `.work/research-base/`，均不发布。不带同步身份的旧表记录不自动接管，迁移前需明确对应关系。图片/附件保留源定位，表格文字不能替代图片判读。新 Base 不自动配置 AI 字段。

## 图片提取的完成条件

PPTX 的结构提取、原图保留、整页渲染和实际视觉核验分开记录。PNG/JPEG/TIFF 等可解码图片生成查看代理，多帧与显示映射保留；精确像素仍来自原图。小字、多 panel 和密集曲线须读局部图，不能从标题或 OCR 自动推定图形结果。

脚本验收包含源 hash、页覆盖、原图完整性与视觉台账。台账通过不证明实际识图正确。当前版本不承诺豆包客户端自动逐页读图；初次部署须用代表性实验 PPTX 实测其图片入口和识别准确率。云环境缺少 PowerPoint 时不宣称完整提取已完成。

## 正式记录与协作

飞书为正式事实源，修改前读最新正文与版本，局部修改后回读。稳定研究 ID 与飞书 block ID 分开；结构修改后更新块定位。保护同事编辑、评论和图片资源，不自动整篇覆盖。

`.agents/config/feishu.example.json` 是配置示例；实际本机配置为 feishu.json，文档登记为 feishu-documents.json，均不进入版本控制。工作稿和快照进入 `.work/`，正式文档链接和验收记录进入 `outputs/reports/`。

## 来源与验证

当前版本为 laRkdown v0.2.0，新增 research-docs-to-base 原生扩展。上游引用版本见“项目概述”；官方资料、核验日期和能力边界见 [official-sources.json](.agents/config/official-sources.json)。公开源码与 Release 不包含实验数据、账户凭证、飞书资源登记和本机快照。

CLI 用法按本机 1.0.97 的官方内嵌技能核验，运行时以当前 `lark-cli --help` 与 `lark-cli skills read` 为准。学术编辑技能保留其第三方 MIT LICENSE；不将该许可推定为其他文件的统一许可。

开发检查：`python -m unittest discover -s tests -v`。检查实际行为与关键失败分支，不能替代豆包客户端验收。
