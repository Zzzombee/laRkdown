# laRkdown

面向 **豆包工作 + 飞书原生文档 + Python** 的科研进度管理工具。当前初版仅包含四个技能：学术写作编辑、研究状态维护、实验 PPTX 提取和外部文献门槛。

以飞书文档保存正式科研记录；Python 负责 PPTX 结构与图片提取、校验和 CLI 调用。本地 Markdown 用于技能指令，XML/JSON 用于工作稿与读取快照。研究条目使用稳定编号和真实飞书文档/块链接。

## 使用

1. 将本项目的 AGENTS.md 与 `.agents/` 复制到一个独立研究工作目录，保留层级。不要复制 `.work/`、本机文档登记、凭证或已有研究资料。
2. 在豆包工作的自定义技能导入入口分别导入 `.agents/skills/` 下四个技能目录。任务开始时明确研究工作目录，并要求读取该目录的 AGENTS.md；不假设客户端自动识别 `.agents/` 或自动执行 AGENTS.md。导入后的托管技能路径不作为项目根目录。
3. 安装 Python 3.11+，在工具项目目录运行 `python -m pip install -r requirements.txt`。飞书默认使用官方 `lark-cli`，按 [官方安装说明](https://github.com/larksuite/cli) 配置当前用户身份；已有登录不重复配置。PPTX 整页渲染默认需要 Windows、PowerShell 和桌面 PowerPoint。

可向豆包发送：

> 研究工作目录是“我的项目路径”。请先读取 AGENTS.md，然后初始化空白飞书科研记录。使用官方 lark-cli，以我的用户身份创建原生文档；已有记录时改为增量维护，完成后返回飞书链接。

初始化助手先准备 XML，再发布 CURRENT_STATE、RESEARCH_QUESTIONS、PROJECT_STORY 三篇空白原生文档。已有科研记录时不重复初始化。日期由用户时区当天日期确定，不写死；项目范围只使用用户给出的信息。

## 四个技能

- `academic-writing-editor`：中英文学术正文起草、改写、翻译与审阅，保护数字、引用和证据强度；默认交付飞书原生文档。
- `maintain-research-state`：维护 OBS／CON／HYP／RQ／SOL 的稳定编号、证据关系及原生文档结构。
- `pptx-to-research-state`：提取文字、备注、表格、原生图表及原图，渲染整页并实际逐图读取后更新科研记录。
- `literature-source-gate`：区分用户指定文献与自主检索，核验来源、主张匹配、指标、例外与受限来源警示。

## 图片提取的完成条件

PPTX 的结构提取、原图保留、整页渲染和实际视觉核验分开记录。PNG/JPEG/TIFF 等可解码图片生成查看代理，多帧与显示映射保留；精确像素仍来自原图。小字、多 panel 和密集曲线须读局部图，不能从标题或 OCR 自动推定图形结果。

脚本验收包含源 hash、页覆盖、原图完整性与视觉台账。台账通过不证明实际识图正确。当前版本不承诺豆包客户端自动逐页读图；初次部署须用代表性实验 PPTX 实测其图片入口和识别准确率。云环境缺少 PowerPoint 时不宣称完整提取已完成。

## 正式记录与协作

飞书为正式事实源，修改前读最新正文与版本，局部修改后回读。稳定研究 ID 与飞书 block ID 分开；结构修改后更新块定位。保护同事编辑、评论和图片资源，不自动整篇覆盖。

`.agents/config/feishu.example.json` 是配置示例；实际本机配置为 feishu.json，文档登记为 feishu-documents.json，均不进入版本控制。工作稿和快照进入 `.work/`，正式文档链接和验收记录进入 `outputs/reports/`。

## 来源与验证

改写自 [maRkdown v0.1.0](https://github.com/Zzzombee/maRkdown/releases/tag/v0.1.0)，精确 commit 为 `a189bd0755a2d1a097b0a1c6f5f5c5712135d616`。内部版本与逐文件来源 hash 在 `.agents/config/upstream.json`；官方资料、核验日期和能力边界在 official-sources.json。

CLI 用法按本机 1.0.97 的官方内嵌技能核验，运行时以当前 `lark-cli --help` 与 `lark-cli skills read` 为准。学术编辑技能保留其第三方 MIT LICENSE；不将该许可推定为其他文件的统一许可。

开发检查：`python -m unittest discover -s tests -v`。检查实际行为与关键失败分支，不能替代豆包客户端验收。
