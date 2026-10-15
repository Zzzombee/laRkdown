---
name: maintain-research-state
description: 初始化科研知识库文档，或将刚完成的实验和结果写入“项目现状”，维护 OBS、CON、HYP、RQ、SOL 的编号与关系。已有记录不重新初始化；只读问答不触发写入。
---

# 飞书研究状态维护

在研究工作目录读取 AGENTS.md、目录合同和 `.agents/instructions/feishu-workflow.md`。登记的知识库文档是事实源；本地 XML/JSON 是工作稿或快照。

- 空白初始化：读 [references/initialization.md](references/initialization.md)。已有科研记录时改用增量维护。
- 即时实验记录：用户直接叙述做了什么、观察到什么，或说“刚做完实验，立刻整理到飞书”时，读最新“项目现状”及必要的相关 RQ，不要求用户先提交 PPTX 或按条目格式写稿。提取已有事实、数字、对照、阴性结果与不确定处；OBS 仅收直接观察，解释单列 CON/HYP 并限定证据，缺失关键参数只阻塞相关判断。能可靠记录的部分先写入知识库文档，回读后给实际链接；没有足够事实时明确追问，不补造结果。
- 研究条目、关系或路线结构改变：完整读 [references/state-schema.md](references/state-schema.md)，用官方 CLI 定位并获取最新相关块。
- 只读、拼写、日期和普通正文修改：不调用结构校验。

稳定研究 ID 不改号、不复用；飞书 block ID 是平台定位信息，结构修改后重新获取。分配新号前核对完整 ID 索引及保留/废弃记录，不从局部读取猜下一个编号。CON 链接支持 OBS 并保留等级、限制和替代解释；HYP 保持未验证；RQ 管优先级；一个 SOL 关联一个主 RQ 且有明确回链，core_route 只有在用户明确要求时改变。

新结果先写 CURRENT_STATE；只有受影响时再写 RESEARCH_QUESTIONS、相关 SOL 和 PROJECT_STORY。日期是可见文档字段。人类编辑、阴性、矛盾和未解决问题保留。原生链接使用真实飞书文档 URL 与当前块 ID，不能构造不存在的链接。

## 校验与交付

合并相关结构修改后定向检查一次。用 `scripts/feishu_bridge.py fetch` 获取当前完整快照，再运行 `scripts/validate_state.py --snapshot 当前状态.fetch.json --snapshot 研究问题.fetch.json --changed CURRENT_STATE`；直接关联的 SOL 也传入。校验范围由 changed 决定，其他快照用于解析引用。跨文档搬动或明确全局审计时才传 `--full`，必须提供覆盖全部登记记录的快照；脚本不会自行拉取全库。

`scripts/feishu_bridge.py` 提供 preflight/create/bind/fetch/patch，并保存返回及资源 sidecar。修改前核对 revision；创建结果不明时先查证，再继续。

交付实际飞书 URL、修改的研究 ID 与必要未解决项。初始化后按根目录 AGENTS.md 的引导示例，把即时实验记录放在首位，并说明“项目故事”仍是待生成的空白框架。脚本通过不能替代对证据的判断或图片视觉核验。
