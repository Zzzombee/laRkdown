# laRkdown

laRkdown 使用豆包工作、飞书知识库和 Python 管理科研进度。六个技能及上游来源见 `.agents/config/upstream.json`。

将直接包含 `.agents/skills/` 的目录作为豆包项目打开。

创建或移动文件前读取 `.agents/instructions/project-layout.md`，按 `.agents/config/project-layout.json` 执行。正式本地产物放在 `outputs/`；科研记录以知识库文档为准，本地 XML/JSON 用于工作稿和校验。

## 科研事实与范围

只读问答不写科研记录。按稳定 ID、标题或关键词读取相关条目；工具维护不读科研状态。OBS 记直接观察，CON 链接 OBS 并标注证据等级，HYP 是未验证解释。保留阴性、不显著、矛盾与缺失信息，不猜测关键参数。

“项目现状”是实验事实来源；“研究问题”管问题与优先级；“项目故事”管目标叙事；SOL 管指定 RQ 的候选路线。研究 ID 不改号、不复用。新结果先更新“项目现状”，其他文档仅在受影响时更新；路线变化需用户明确要求。

## 六个技能

- 学术正文起草、改写、翻译、润色、审阅：`.agents/skills/academic-writing-editor/SKILL.md`。审阅只报告问题；其他流程先处理事实与结构再编辑。
- 空白科研初始化、刚完成实验的即时记录和研究条目结构维护：`.agents/skills/maintain-research-state/SKILL.md`。已有科研状态不重新初始化；用户直接口述实验和结果时可写入“项目现状”，不要求先制作 PPTX。
- 指定实验 PPTX 导入：`.agents/skills/pptx-to-research-state/SKILL.md`。结构与视觉两条路径均完成后才录入事实。
- 外部学术文献：`.agents/skills/literature-source-gate/SKILL.md`。指定文献与自主检索分别执行来源政策；工具官方文档不触发学术指标门槛。
- 三篇知识库文档构建/同步知识库多维表格：`.agents/skills/research-docs-to-base/SKILL.md`。项目已登记研究知识空间时，新建 Base 放入同一空间；六表是派生协作视图，源文档仍为事实权威；保护 AI/人工字段，缺失条目归档不删，不回写源文档。
- 已初始化项目的版本升级：`.agents/skills/upgrade-larkdown/SKILL.md`。从新版完整发行包运行 `upgrade_larkdown.py`，先预览冲突；保留科研资料、本机配置、飞书文档和多维表格同步基线。

## 初始化后与无指向用法询问

初始化完成后给出知识空间名称、三篇知识库文档链接和简短用法。用户只问“怎么用”“接下来做什么”时给用法示例，不创建记录。第一条优先引导即时实验记录：用户直接说做了什么、观察到什么，豆包将可核对的事实写入“项目现状”，区分观察与解释，缺失的关键条件仅在相关判断处追问或标注待补。写后回读并给链接。“告诉飞书”且未指定文档时，“项目现状”是实验事实的默认目标。

其他常用入口：PPTX 导入、生成或修订“项目故事”、构建或同步知识库多维表格。初始化时“项目故事”只是空白框架；故事任务走 `.agents/skills/pptx-to-research-state/references/story-workflow.md` 和 `.agents/instructions/story-policy.md`，无需 PPTX。对话中使用“知识库文档”“知识库多维表格”。

可直接给用户的短句示例，按当前状态择要呈现：

- “我刚做了……实验，观察到……；请立刻整理进知识库文档《项目现状》，缺的信息标注待补。”
- “从这个 PPTX 提取证据并更新知识库文档《项目现状》：文件路径。”
- “根据《项目现状》和《研究问题》生成知识库文档《项目故事》的初稿。”
- “根据这次新结果修订知识库文档《项目故事》，保留当前证据边界。”
- “把三篇知识库文档构建为知识库多维表格”；建好后可说“同步知识库多维表格”。

## 版本与使用帮助

豆包工作是用户的产品交互入口。安装后的用法、版本变化和下一步操作直接在对话中说明，不要求用户查阅项目内部文件或访问 GitHub。

用户问“我安装的是哪个版本”“这个版本更新了什么”时，读取当前项目 `.agents/config/upstream.json` 的 laRkdown 版本及 `.agents/instructions/version-notes.md`，有发行清单时核对其版本一致。更新记录从高于 v0.2.5 的发行版本开始，v0.2.5 及更早版本不追溯补写。按说明给出主要变化和可直接使用的提问示例；仅解释本地说明已覆盖的版本差异，不从当前技能反推新增功能，不将仓库 main 或最新 Release 当作已安装版本。说明缺失或版本不一致时明确无法确认相应变化。只读帮助不触发初始化、科研记录写入或升级；用法询问按前述规则优先引导即时实验记录。

## 飞书操作

使用官方 `lark-cli --as user`。空白初始化在同名知识空间创建“项目现状”“项目故事”“研究问题”；日常读写使用 Docs 命令。具体操作读 `.agents/instructions/feishu-workflow.md` 和当前 CLI 帮助，交付真实飞书 URL。

修改前读取最新正文、版本和相关 block ID；局部编辑并保护已有内容与资源。检查 CLI 结果、warnings，写后回读。创建结果不明时先查证，避免重复创建。

研究 ID 永久，飞书 block ID 在结构修改后重新查询。跨条目引用使用真实文档和块链接。

缺少工具或权限只阻塞相关部分。图片证据须实际打开查看，不能仅凭标题或 OCR 判断。

## 发布维护

仓库根目录的 [USER_GUIDE.md](https://github.com/Zzzombee/laRkdown/blob/main/USER_GUIDE.md) 是部署前介绍与发版沟通使用的正式指南，纳入 Git，不进入产品 ZIP 或升级托管清单。每次发布新版本前根据实际功能更新指南正文、适用版本、发布页和下载链接，并与 README.md 保持一致。同时更新随包交付的 `.agents/instructions/version-notes.md`，说明相较上一版的变化、用法和必要的能力边界，供豆包回答并用于 Release 正文。按 [仓库发布规范](https://github.com/Zzzombee/laRkdown/blob/main/tools/RELEASING.md) 完成发行清单准备、测试与发布检查；检查通过后才可推送版本 tag。
