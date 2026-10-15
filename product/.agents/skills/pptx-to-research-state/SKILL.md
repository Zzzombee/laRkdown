---
name: pptx-to-research-state
description: 从实验 PPTX 提取文字与图片证据并更新科研知识库文档；也可根据已有记录生成或修订“项目故事”，无需 PPTX。普通 PPT 制作不触发。
---

# PPTX 提取与飞书科研记录

在研究工作目录读取 AGENTS.md、目录合同与飞书工作流。PPTX 导入需指定文件；故事任务直接读取相关知识库文档。保留已有编辑、研究编号及阴性/矛盾结果。

- 从指定 PPTX 新建科研记录：[references/initialization.md](references/initialization.md)。已有状态改走增量分支。
- 导入现有项目：[references/incremental-update.md](references/incremental-update.md)。
- 实际提取与看图：完整读 [references/pptx-evidence.md](references/pptx-evidence.md)。脚本路径相对本技能目录，数据路径相对指定研究工作目录。
- 用户明确要求生成或修订“项目故事”时，读 [references/story-workflow.md](references/story-workflow.md)，可独立于 PPTX 导入执行；指定 RQ 方案时读 [references/solution-workflow.md](references/solution-workflow.md)。普通导入不自动扩展到这些分支。

在 PPTX 导入分支，Python 提取文字/备注/表格/原生图表数值，并保留原图；渲染整页恢复实际呈现关系；豆包实际加载逐页图片及必要局部图进行视觉判断。三者缺一不能将图片相关内容作为已核验观察写入飞书。

PPTX 导入时，实际打开逐页图片和必要的局部图，记录已查看的 panel；视觉工具不可用时仅处理可核实的文字和结构证据。

PPTX 标题和汇报总结是作者主张，须对照图形；不能复制为直接观察。区分原生精确数值、图上明确标注和视觉估读，不从图片估造样本量、统计或关键参数。两个分支完成来源核对后都按维护技能做适度结构校验，科学正文用学术编辑器；只有引入外部文献时使用文献门槛。

最后通过官方 lark-cli 写入并回读飞书记录，交付真实飞书 URL 和必要缺口。PPTX 分支的原图、整页渲染、临时证据台账与机器校验留在 `.work/pptx/`。
