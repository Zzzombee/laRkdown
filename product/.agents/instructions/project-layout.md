# 个人科研项目目录

创建和移动文件前读取本合同；目录清单由 `.agents/config/project-layout.json` 管理。

- 根目录：AGENTS.md、README.md、Python 依赖说明及 run.py/run.ps1 科研调用入口。豆包打开此目录；未自动识别技能时按客户端入口导入。
- `.agents/instructions/`：科研事实、飞书操作和故事规则；`.agents/config/`：科研目录、工具来源及本机飞书文档登记；`.agents/skills/`：五个科研技能及资源。
- `sources/presentations/`：输入 PPTX；`sources/literature/`：指定论文与补充材料。原始数据可留在项目外，不为目录整理搬动唯一副本。
- `.work/`：DocxXML 工作稿、飞书快照、提取图片、整页渲染、证据台账及临时依赖。
- `.planning/`：科研任务计划和恢复检查点。
- `outputs/reports/`：正式飞书交付的 URL、文档 ID、版本和精简完成记录；明确要求的本地导出也进入 outputs。

飞书原生文档是默认正式产物。`outputs/` 是唯一正式本地输出根目录，不建立顶层 output、out、result、results、figures、reports、tmp、staging 等同义目录。不在本地维护第二套科研状态正文；规则和技能不放在 outputs。

飞书文档登记、快照和私人资料只服务当前科研项目。凭证留在 CLI 认证存储，不复制到技能或交付文件。不递归搬动或清理目录链接的目标。
