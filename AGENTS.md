# laRkdown

独立科研工具项目：豆包工作 + 飞书原生文档 + Python。维护四个上游适配技能及两个 laRkdown 原生扩展，共六个技能。上游版本与逐文件来源记录在 `.agents/config/upstream.json`，不修改 maRkdown 或其原科研项目。

创建或移动文件前读取 `.agents/instructions/project-layout.md`，按 `.agents/config/project-layout.json` 执行。正式本地产物唯一根目录为 `outputs/`；飞书文档是科研记录和用户交付的默认载体，本地 XML/JSON 是工作稿、读取快照与校验记录。

## 科研事实与范围

用户的只读问答不写科研记录。先按稳定 ID、标题和关键词定位，再读取直接相关条目；纯工具维护不读取科研状态。OBS 只记直接观察，CON 链接 OBS 并标注证据等级，HYP 保持未验证解释。保留阴性、矛盾、不显著与缺失信息，不猜测关键参数。

CURRENT_STATE 对应的飞书文档是事实权威；RESEARCH_QUESTIONS 管问题与优先级；PROJECT_STORY 管目标叙事；指定 RQ 的 SOL 管候选路线。稳定研究 ID 不改号、不复用。可靠新结果先更新 CURRENT_STATE，后续文档仅在受影响时更新。路线变化只在明确授权时执行。

## 六个技能

- 学术正文起草、改写、翻译、润色、审阅：`.agents/skills/academic-writing-editor/SKILL.md`。审阅只报告问题；其他流程先处理事实与结构再编辑。
- 空白科研初始化和研究条目结构维护：`.agents/skills/maintain-research-state/SKILL.md`。已有科研状态不重新初始化。
- 指定实验 PPTX 导入：`.agents/skills/pptx-to-research-state/SKILL.md`。结构与视觉两条路径均完成后才录入事实。
- 外部学术文献：`.agents/skills/literature-source-gate/SKILL.md`。指定文献与自主检索分别执行来源政策；工具官方文档不触发学术指标门槛。
- 三篇飞书科研文档构建/同步多维表格：`.agents/skills/research-docs-to-base/SKILL.md`。六表是派生协作视图，源文档仍为事实权威；保护 AI/人工字段，缺失条目归档不删，不回写源文档。
- 已初始化项目的版本升级：`.agents/skills/upgrade-larkdown/SKILL.md`。从新版完整发行包运行 `upgrade_larkdown.py`，先预览冲突；保留科研资料、本机配置、飞书文档和多维表格同步基线。

## 飞书操作

默认使用官方 `lark-cli`，优先 `docs +fetch/+create/+update`，默认 `--as user`。先读 `.agents/instructions/feishu-workflow.md`，再查当前 CLI 内嵌的官方技能或 `--help`；不凭旧教程猜参数。文档采用飞书 DocxXML 原生块，交付实际返回的飞书 URL。原生 Markdown 云盘文件不是默认交付。

飞书记录每次修改前读取最新正文、版本及当前 block ID。保护人类编辑、评论、图片和附件；优先局部补丁，不自动整篇覆盖。`ok=true`、warnings 检查和写后回读共同构成完成条件。创建结果不确定时停止重复创建并查证已创建的文档。

飞书文档是唯一正式科研记录，本地快照不作为独立事实层。研究 ID 与飞书 block ID 分开：前者永久，后者在结构修改后重新查询。关联条目使用真实飞书文档/块链接；不使用双括号链接、行尾锚点、专有笔记属性或自动反向链接。

缺失 CLI、权限、渲染器或视觉入口只阻塞相关部分。不得宣称豆包已经看过未实际加载的图片；不得用标题或 OCR 代替图形证据。当前环境的能力检查优先于产品宣传。

## 工具项目开发

只改用户指定范围。保留第三方 LICENSE。修改可执行脚本后做对应行为检查；没有科研条目变更时不运行真实科研状态审计。文档中引用官方来源并记录核验日期，推断与未实测能力分开。

## 每个发行版本的升级合同

未来每个公开 Release 必须携带 `upgrade_larkdown.py`、`upgrade-larkdown` 技能、`.agents/config/release-manifest.json`、旧版基线和 [UPGRADING.md](UPGRADING.md)。发布前运行 `tools/build_release.py --check` 与项目测试；打包只使用该脚本的 `--build`。推送版本 tag 后，由 `.github/workflows/release-contract.yml` 在全部检查通过后自动创建 Release 并上传 ZIP 与同名 `.sha256` 附件；不要绕过该流程手工创建 Release。不能为方便发布删除升级器或跳过冲突/恢复检查。科研项目结构版本变化时先实现并验证迁移，否则发布检查必须失败。发行版本与 maRkdown 的引用版本分别记录。
