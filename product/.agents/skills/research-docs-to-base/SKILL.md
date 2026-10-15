---
name: research-docs-to-base
description: 将项目现状、研究问题、项目故事构建或同步为六张知识库多维表格；支持只读预览、关联与归档。
---

# 知识库六表

文档是事实源，Base 仅为派生视图，不回写原文，不新搜/评价文献。涉及飞书时遵循飞书工作流，默认官方 CLI 和用户身份。首次使用按 README 准备 base 功能，后续不重复检查环境。

## 输入与分支

读 [mapping](references/mapping.md)，复用三文档登记或绑定用户提供的三个不同链接；来源必须完整可读，不把操作手册当事实。配置存 `.agents/config/research-base.local.json`，由 [示例](assets/research-base.example.json) 复制结构，不存凭证；非标准条目用真实 block ID 的 selectors 指定。

统一用 `python run.py base --root . <操作>`，Windows 可用 run.ps1 替代 `python run.py`：

| 请求 | 操作 |
| --- | --- |
| 提取/预览 | extract / preview，只读双方与输出差异 |
| 构建 | init --name 名称，再 sync；init 只补结构，不导记录 |
| 绑定已有 Base | init --base-url 实际链接，不自动迁移 |
| 复制空白母版 | init --template-url 实际链接 --name 新名称，不能写原母版 |
| 同步 | sync，已授权对应写入；内部重读、检查差异/冲突后执行并回读 |
| 中断恢复 | 读 [operations](references/operations.md)，查证后 recover，再继续缺失部分 |

新建 Base 放入已登记科研知识空间，与三文档同级；用户绑定的已有 Base 不搬动。未知创建/移动结果保留 pending，查证同一资源，不重复创建或移动。

## 约束与交付

按永久研究编号/独立同步键识别记录，使用真实 record ID；只归档本技能管理的缺失条目，不删除未知行。六表映射、可读正文/引用、目标叙事标签、资源定位、视图与字段所有权按 mapping；保留人工备注、AI 扩展和原视图，不删同步字段、不自动配置 AI 用量。

来源不完整、重复 ID、字段不兼容、分页不全、源版本变化或管理字段被人工修改时停止写入，不用新建另一份避开冲突。接口与恢复细节按需读 operations；不改变共享权限或发送消息。

交付真实 Base 链接、知识空间归属、六表新增/更新/归档/未变数量和缺口。精简结果放 outputs/reports/，快照/计划/日志放 .work/research-base/；图片文本不代表完成视觉核验。
