---
name: maintain-research-state
description: 初始化飞书科研记录，或维护 OBS、CON、HYP、RQ、SOL 的编号、关系和结构；已有记录不重新初始化，正文编辑与只读问答不做结构审计。
---

# 飞书研究状态维护

运行前定位用户指定研究工作目录，读取其 AGENTS.md、目录合同与 `.agents/instructions/feishu-workflow.md`。技能安装目录不代表研究目录。正式事实源是登记的飞书文档，本地 XML/JSON 是最新读取快照或待发布工作稿。

- 空白初始化：读 [references/initialization.md](references/initialization.md)。先查登记与现有飞书记录，已有状态时停止初始化；不得用空白框架替代 PPTX 证据导入。
- 研究条目、关系或路线结构改变：完整读 [references/state-schema.md](references/state-schema.md)，用官方 CLI 定位并获取最新相关块。
- 只读、拼写、日期和普通正文修改：不调用结构校验。

稳定研究 ID 不改号、不复用；飞书 block ID 是平台定位信息，结构修改后重新获取。分配新号前核对完整 ID 索引及保留/废弃记录，不从局部读取猜下一个编号。CON 链接支持 OBS 并保留等级、限制和替代解释；HYP 保持未验证；RQ 管优先级；一个 SOL 关联一个主 RQ 且有明确回链，core_route 只有在用户明确要求时改变。

新结果先写 CURRENT_STATE；只有受影响时再写 RESEARCH_QUESTIONS、相关 SOL 和 PROJECT_STORY。日期是可见文档字段。人类编辑、阴性、矛盾和未解决问题保留。原生链接使用真实飞书文档 URL 与当前块 ID，不能构造不存在的链接。

## 校验与交付

合并相关结构修改后定向检查一次。用 `scripts/feishu_bridge.py fetch` 获取当前完整快照，再运行 `scripts/validate_state.py --snapshot 当前状态.fetch.json --snapshot 研究问题.fetch.json --changed CURRENT_STATE`；直接关联的 SOL 也传入。校验范围由 changed 决定，其他快照用于解析引用。跨文档搬动或明确全局审计时才传 `--full`，必须提供覆盖全部登记记录的快照；脚本不会自行拉取全库。

`scripts/feishu_bridge.py` 提供 preflight/create/bind/fetch/patch，并保存完整返回及资源 sidecar；不自动登录、发送消息、改权限或整篇覆盖。修改前的基线 revision 必须与回读一致；pending 创建必须查证，不能重复新建。

交付实际飞书 URL、修改的研究 ID 与必要未解决项。脚本通过不能替代对证据的判断或图片视觉核验。
