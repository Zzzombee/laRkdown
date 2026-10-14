# 目录合同

创建和移动文件前读取本合同；目录清单由 `.agents/config/project-layout.json` 管理。

- 产品根目录：AGENTS.md、README.md、UPGRADING.md、upgrade_larkdown.py 和依赖清单。源码仓库另有 USER_GUIDE.md，为纳入 Git 并随版本更新的正式使用指南，不进入产品 ZIP 或升级托管清单。不在此维护第二套科研状态正文。
- `.agents/instructions/`：共享规则及供豆包解释当前版本变化的 version-notes.md；`.agents/config/`：版本来源、发行/升级清单、长期配置与本机飞书文档登记；`.agents/skills/`：六个科研技能及资源。
- 豆包实际打开的项目根目录须直接包含上述 `.agents/skills/`；把整个仓库放在已打开项目的 `laRkdown/` 子目录时，须改为打开该子目录或安全地将发行包内容放到根目录。
- `sources/presentations/`：输入 PPTX；`sources/literature/`：指定论文与补充材料。原始数据可留在项目外，不为目录整理搬动唯一副本。
- `.work/`：DocxXML 工作稿、最新飞书快照、提取图片、整页渲染、证据台账、校验结果及临时依赖。
- `.planning/`：任务计划和恢复检查点。
- `outputs/reports/`：正式飞书交付的 URL、文档 ID、版本和精简完成记录；明确要求的本地导出也进入 outputs。

飞书原生文档是默认正式产物。`outputs/` 是唯一正式本地输出根目录，不建立顶层 output、out、result、results、figures、reports、tmp、staging 等同义目录。规则和技能不放在 outputs；测试和缓存不作为正式交付。

飞书文档登记文件和快照包含用户实际资源标识，默认不纳入版本控制。运行时依赖、凭证和第三方缓存不打包；不递归搬动或清理目录链接的目标。
