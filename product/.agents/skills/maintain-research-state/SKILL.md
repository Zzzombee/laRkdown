---
name: maintain-research-state
description: 初始化科研框架、即时记录实验或维护 OBS/CON/HYP/RQ/SOL。已有记录增量更新；只读问答不写入。
---

# 科研状态维护

以登记的飞书文档为事实源。飞书操作遵循 `.agents/instructions/feishu-workflow.md`；文件创建/移动才读目录合同。复用本次已确认的稳定规则，写前仍读最新相关内容。

## 选择分支

- 用户明确建立空白框架：读 [initialization](references/initialization.md)。已有记录绑定/更新，不重建。
- 用户口述刚完成的实验：从已有事实、数值、对照、阴性和不确定信息整理，先写 CURRENT_STATE；无需 PPTX。缺关键条件只阻塞相关判断，可靠部分先记，不补造结果。
- 新增/改变研究条目、关系或路线结构：读 [state-schema](references/state-schema.md)，按完整 ID 索引及保留号分配新号，不能从局部猜号。只读、拼写、日期、普通正文不触发结构审计。

OBS 只记观察；CON 链接 OBS 并分级；HYP 明确未验证。保留人工编辑及阴性/矛盾。先改现状，其余仅在受影响时更新；core_route 仅明确授权才改，一个 SOL 一个主 RQ，真实回链在同批维护。

## 执行与完成

统一入口 `python run.py feishu <参数>` 提供 preflight/create/bind/fetch/patch；`python run.py initialize <参数>` 准备/发布框架。Windows 可用 run.ps1 替代 `python run.py`。

相关结构修改合并后 fetch 必要完整快照，再执行 `python run.py validate-state --snapshot 当前快照 --snapshot 相关快照 --changed CURRENT_STATE`。changed 决定检查范围；关联 SOL 提供相应快照。跨文档迁移或用户全局审计才用 --full，需覆盖全部登记记录，不自行扫全库。校验不代替科学证据判断。

写前核对 revision，写后回读；创建结果不明保留 pending、查证并恢复同一资源。交付实际 URL、改变的研究 ID 和必要未解决项；初始化后的简短引导按项目 AGENTS。
