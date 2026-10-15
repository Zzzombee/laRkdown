# 个人科研项目

在豆包工作打开直接包含 `.agents/skills/` 的本目录。正式科研记录保存在飞书知识库；本地 XML/JSON 仅作工作稿、快照和校验。

## 全局规则

- 按任务加载相关技能和条目，复用已确认规则。环境只在首次、变化或相关失败时检查；软件准备见 README.md，统一用 run.py/run.ps1 调用选定环境。日常不重复检查全项目。
- 只读问答、用法询问不写记录。确定性工作交给脚本；成功给简短结果和实际链接，失败按需读日志。修改前读最新受影响内容，核验科研证据，写后回读。
- OBS 只记直接观察；CON 链接 OBS 并标证据等级；HYP 明确未验证。保留阴性、不显著、矛盾和缺失信息，不猜关键参数，不从标题/OCR 代替图片核验。
- CURRENT_STATE（项目现状）是实验事实源；RESEARCH_QUESTIONS 管问题与优先级；PROJECT_STORY 管目标叙事；SOL 管指定 RQ 的候选路线。先更新现状，其余仅在受影响时更新。研究 ID 永久、不复用；core_route 仅按用户明确要求改变。
- 创建/移动文件前读 `.agents/instructions/project-layout.md`；正式本地产物统一放 outputs/。不复制私人登记或凭证到其他项目。

## 按任务读取

| 请求 | 技能入口 |
| --- | --- |
| 学术起草、改写、翻译、润色、审阅 | `.agents/skills/academic-writing-editor/SKILL.md`；审阅不自动改正文 |
| 空白初始化、刚做完实验的即时记录、结构维护 | `.agents/skills/maintain-research-state/SKILL.md`；已有状态不重建，口述记录无需 PPTX |
| 指定实验 PPTX；生成/修订故事；指定 RQ 方案 | `.agents/skills/pptx-to-research-state/SKILL.md`；按对应分支读取 |
| 外部文献核验/检索 | `.agents/skills/literature-source-gate/SKILL.md`；指定来源与自主检索分开，工具文档不触发学术门槛 |
| 三文档构建/同步六表 | `.agents/skills/research-docs-to-base/SKILL.md`；Base 是派生视图，文档仍为事实源 |

## 飞书与交付

涉及飞书读写时读 `.agents/instructions/feishu-workflow.md`，使用官方 CLI 和用户身份。局部编辑保护人工内容、图片和附件；结构变化后重取 block ID，关系使用真实文档及当前块链接。结果不明先查证同一资源，不能重复创建。

用户说“告诉飞书”且未指定目标时，将实验事实写入“项目现状”；缺信息标待补，只追问影响判断的必要参数。初始化给知识空间名、三篇实际链接，说明故事仍为空框架；先示范即时记录，再按需介绍故事、PPTX 和多维表格。用法示例见 README.md，仅询问用法时不创建资源。缺工具/权限只阻塞相关部分。
