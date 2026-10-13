---
name: research-docs-to-base
description: 用户要求把“项目现状”“研究问题”“项目故事”构建或同步为六张知识库多维表格时使用；支持差异预览、关联与归档。
---

# 知识库文档转知识库多维表格

触发示例：“用 laRkdown 把这三篇知识库文档构建为知识库多维表格”“同步知识库多维表格”“预览知识库文档到多维表格的变化”。默认官方飞书 CLI、用户身份。知识库文档继续作为事实源，Base 是派生协作视图，不回写原文。

## 输入与执行

1. 在研究工作目录读取 AGENTS.md、目录合同和 `.agents/instructions/feishu-workflow.md`。
2. 读取 [references/mapping.md](references/mapping.md)。复用 `.agents/config/feishu-documents.json` 的三篇登记，或让用户提供三个链接并绑定。示例仅用于复制结构，实际配置存 `.agents/config/research-base.local.json`，不保存凭证。三个来源必须不同、完整可读，不把操作手册当科研事实源。
3. 按任务读取本机官方 `lark-base` 说明，运行 [scripts/research_base.py](scripts/research_base.py) 提取和预览。非标准条目用 `selectors` 指定真实 block ID；来源不清时先定位。
4. 用户要求“构建”时可创建新 Base，或复制用户提供的空白母版；项目已登记研究知识空间时，将新建 Base 放入该空间，与三篇文档同级。用户指定已有 Base 时只绑定该 Base，不自动迁移它。用户要求“同步”已授权对应写入，完成差异检查后执行；“预览/检查”只读。不得为了完成导入改共享权限、发送消息或写原母版。
5. 执行增量同步，交付实际返回的 Base 链接、知识空间归属、六表新增/更新/归档/未变数量及缺口。保存精简验收到 `outputs/reports/`；快照、差异和日志进入 `.work/research-base/`。写入失败按 [references/operations.md](references/operations.md) 查证后恢复，不能再次盲目创建。

## 同步约束

- OBS/CON/HYP/RQ 按永久编号；文献按 DOI 或规范化链接。其他条目使用独立同步键，展示序号不作身份。源条目消失时只归档本技能已管理的记录，不删除。
- 六表均给出“概要”“原文”“引用”：概要默认使用去编号的来源标题或任务首句，优先采用已有中文标题；非标准来源可用经过人工核对的 selector 标题。原文仅放条目内容，剔除重复编号、来源/同步元数据及独立引文行；引文另入“引用”。不由脚本生成科学结论或提高证据等级。PROJECT_STORY 的成功叙事标为“目标论文叙事”；真实支持条件保留原文。SOL 只保留原文中的引用，不据此生成方案。
- 同步键、来源版本和哈希等字段仍用于增量同步与冲突检查；新建 Base 的阅读视图隐藏它们，接入已有 Base 时另建“科研阅读”视图，保留原视图设置。不要手动删除同步字段。
- 图片、附件、公式等保留源块定位和资源标记；多维表格文本不等于完成视觉读取，不从图片补造科学事实。
- 核心发现、层级、类型及所有带 AI 扩展的字段不写；人工备注、评论、附加字段不写。源类型和源证据等级另存可追溯文本。新 Base 不自动配置 AI 列或 AI 用量。
- 任一来源不完整、编号重复、目标字段不兼容、表格读取分页不完整、源版本变化或已管理字段有人修改时停止写入。未知原有记录不自动接管；不能用新增一份避开冲突。
- 本技能不搜索或评价新文献；需要补充外部证据时另走 literature-source-gate。

## 常用命令

在工作根目录运行；Python 用项目实际虚拟环境替换。第一次将 [assets/research-base.example.json](assets/research-base.example.json) 复制到 `.agents/config/research-base.local.json`，填写三个链接（也可留空复用登记）。

```text
python .agents/skills/research-docs-to-base/scripts/research_base.py --root . extract
python .agents/skills/research-docs-to-base/scripts/research_base.py --root . init --name 我的科研知识库多维表格
python .agents/skills/research-docs-to-base/scripts/research_base.py --root . preview
python .agents/skills/research-docs-to-base/scripts/research_base.py --root . sync
```

`extract` 只读取文档并输出六表数据集；`init` 创建/补齐六表结构（不导入记录），新 Base 会迁入已登记的研究知识空间；`preview` 读取双方并生成差异；`sync` 重新读取双方、核对版本再写并回读。创建已有目标时用 `init --base-url 实际链接`，复制空白母版用 `init --template-url 实际链接 --name 新名称`。参考来源和参数见 operations，不把上述占位词原样执行。
