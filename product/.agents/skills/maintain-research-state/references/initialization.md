# 空白科研框架

仅用户明确要求新框架且目标无科研状态时执行。确定科研目录、体系名称、范围、用户时区日期；体系名同时用作知识空间名。读目录合同并检查本机登记、用户链接和已知同项目线索。无登记不证明远端无记录；已有 CURRENT_STATE/RQ/Story/SOL 则绑定并增量维护，不覆盖空框架。

保留用户 AGENTS/文档，科研目录从干净产品包建立，不能复制开发 AGENTS、私人登记、sources/outputs/.work 或凭证。五技能及共享规则须可用。

```text
python run.py initialize --root . --date YYYY-MM-DD --system-name 体系名称 --scope 一句话范围 --publish
```

用户已要求初始化时可一次 --publish；脚本先准备并校验 `.work/initialization/` 三份空白 XML/manifest，再创建同名空间及其中三篇 Docx 节点，填充并回读。只准备本地草稿时省略 --publish。不能把占位词原样执行。

标题为“项目现状”“项目故事”“研究问题”，登记 CURRENT_STATE、PROJECT_STORY、RESEARCH_QUESTIONS 及实际空间/节点/文档 ID 和 URL。初始化无科研发现、研究 ID、SOL 或额外路线；故事为空框架。同名空间先核实，不盲目占用或新建。

部分成功沿用登记和匹配的 manifest，失败查证 pending、绑定原资源并恢复；不能清闩锁另建一套，不自动移动已有文档。检查实际 warnings、XML/正文及资源回读。缺 CLI/权限/授权则保留草稿并准确报告。交付空间名、三链接、科研目录和 AGENTS 规定的简短用法。
