# 从指定 PPTX 建立飞书科研记录

先读取目标工作目录 AGENTS.md、目录合同和飞书登记。已有 CURRENT_STATE/RQ/Story 时走 incremental-update.md，不建立重复文档。新项目先用维护技能准备原生 XML 容器，尚未核验的 PPTX 不能直接填为事实。

保留输入来源，执行 pptx-evidence.md 的结构、原图、整页与视觉核验。按真实证据整理 OBS、CON、HYP 和相关 RQ，用维护技能的稳定编号和原生链接。来源台账保存页码、形状、hash 和明确/估读数值身份。

默认建立 CURRENT_STATE、RESEARCH_QUESTIONS、PROJECT_STORY 三篇飞书文档；Story 可仅保留空框架，不因初始化自行补造故事、文献或 SOL。用户明确要求故事时才走 story-workflow.md。

先发布并回读基础记录，取得真实条目块链接，再局部补齐依赖关系。未知链接不当作完成关系写入。已创建部分失败时修复同一文档。相关变更合并后一次适度结构检查，正文再用学术编辑器校订，最后给飞书链接。
