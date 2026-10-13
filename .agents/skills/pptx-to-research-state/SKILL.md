---
name: pptx-to-research-state
description: 从用户指定的实验 PPTX 提取结构与图片证据，初始化或增量更新飞书科研记录；普通 PPT 制作与只读讨论不触发。
---

# PPTX 提取与飞书科研记录

指定研究工作目录和输入 PPTX，读取 AGENTS.md、目录合同与共享飞书工作流。保留输入、用户编辑、稳定研究编号及阴性/矛盾结果。正式产物为飞书原生文档。

- 从指定 PPTX 新建科研记录：[references/initialization.md](references/initialization.md)。已有状态改走增量分支。
- 导入现有项目：[references/incremental-update.md](references/incremental-update.md)。
- 实际提取与看图：完整读 [references/pptx-evidence.md](references/pptx-evidence.md)。脚本路径相对本技能目录，数据路径相对指定研究工作目录。
- 用户明确要求故事或指定 RQ 方案时，分别读 [references/story-workflow.md](references/story-workflow.md)、[references/solution-workflow.md](references/solution-workflow.md)；普通导入不自动扩展到这些分支。

Python 提取文字/备注/表格/原生图表数值，并保留原图；渲染整页恢复实际呈现关系；豆包实际加载逐页图片及必要局部图进行视觉判断。三者缺一不能将图片相关内容作为已核验观察写入飞书。

产品支持文件或模型支持识图不代表当前任务已经看过图片。使用当前豆包可用的图片读取/视觉工具，记录实际打开的文件及 panel；工具缺失时停止相关图片证据录入，保留已经完成的结构与图片产物。API 接入只在用户明确选择后配置。

标题和汇报总结是作者主张，须对照图形；不能复制为直接观察。区分原生精确数值、图上明确标注和视觉估读，不从图片估造样本量、统计或关键参数。完成来源核对后按维护技能做适度结构校验，科学正文用学术编辑器；只有引入外部文献时使用文献门槛。

最后通过官方 lark-cli 写入并回读飞书记录，交付真实飞书 URL 和必要缺口。原图、整页渲染、临时证据台账与机器校验留在 `.work/pptx/`。
