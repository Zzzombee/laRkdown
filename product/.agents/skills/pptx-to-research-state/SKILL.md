---
name: pptx-to-research-state
description: 从指定实验 PPTX 提取并核验科研证据；也用于生成/修订项目故事或指定 RQ 方案。故事无需 PPTX，普通 PPT 制作不触发。
---

# PPTX、故事与研究路线

只读当前分支需要的参考；正式事实仍以飞书文档为准，写入遵循飞书工作流与维护技能。

| 用户请求 | 读取 |
| --- | --- |
| 指定实验 PPTX，新项目 | [initialization](references/initialization.md) 与 [pptx-evidence](references/pptx-evidence.md) |
| PPTX 更新已有记录 | [incremental-update](references/incremental-update.md) 与 [pptx-evidence](references/pptx-evidence.md) |
| 生成/修订项目故事 | [story-workflow](references/story-workflow.md) 与项目 story-policy；不加载提取/渲染步骤 |
| 为指定 RQ 生成方案 | [solution-workflow](references/solution-workflow.md)；普通导入不自动创建 SOL |

PPTX 分支须完成结构提取、原图保留、整页渲染及逐页/必要局部视觉核验，三类验收齐备后才将图片内容录为已核验观察。标题和汇报总结是作者主张，须对照图形；精确数值、图上标注与视觉估读分开，不猜样本量、统计或参数。视觉不可用时只处理可核实部分。

保留人工编辑、稳定编号及阴性/矛盾。新文献才触发来源门槛；科学正文用学术编辑。写后回读，交付真实飞书 URL 和必要缺口；原图、渲染及证据台账留 .work/pptx/。
