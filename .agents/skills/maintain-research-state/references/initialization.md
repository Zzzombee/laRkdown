# 空白飞书科研项目初始化

仅在用户明确要求建立新科研框架且目标没有科研状态时执行。确定用户指定工作目录、项目名、研究范围和当前用户时区日期。先读目录合同，再检查 `.agents/config/feishu-documents.json`、用户提供的飞书链接及已知同项目记录。登记已有 CURRENT_STATE、RQ、Story 或 SOL 时不重新初始化；登记不存在并不证明远端没有已有记录，已有线索须先定位。

保留已有 AGENTS.md 与用户文档；四个技能和共享规则须在研究工作目录可用。新研究工作目录可由本工具目录复制规则/技能建立，不能复制本机登记、sources、outputs、.work 或凭证。

执行：
```text
python .agents/skills/maintain-research-state/scripts/initialize_project.py --root . --date YYYY-MM-DD --project-name 项目名 --scope 一句话范围
```
这一步只生成 `.work/initialization/` 中三份空白 DocxXML 和 manifest，不录入科研发现、ID 或 SOL。核对模板后用同一命令加 `--publish`，通过官方 CLI 创建 CURRENT_STATE、RESEARCH_QUESTIONS 和 PROJECT_STORY 三篇原生文档并登记真实 URL。该阶段不创建额外研究路线。

部分创建成功后继续使用登记的文档，不能另建一套。创建失败且结果不确定时，先查证 pending；用 bridge bind 绑定查到的原文档后再恢复。用户提供既有文档时直接绑定并走增量更新，不把内容改成空框架。

按当前官方 CLI 校验 XML、检查 warnings、写后回读。空框架的目标是建立容器，不包含被误认为已完成的科研条目。最终给三篇飞书链接及工作目录，未配置 CLI 或未授权时保留已准备的工作稿并准确报告阻塞。
