# 仓库发布规范

## 单一发行 ZIP，两个隔离目录

只发布 laRkdown-v<版本>.zip 和同名 .sha256。ZIP 内：

- laRkdown/：从 product/ 映射的个人科研 AGENTS.md、README.md、依赖和五个科研技能。无开发、维护或版本管理指引。
- maintenance/：升级器、UPGRADING.md、release/ 中的来源、清单、历史基线与版本说明。无 AGENTS.md 或 .agents 技能入口。

科研目录与维护目录分别校验，统一封装。禁止直接使用 git archive 构建产品。哈希及历史 AGENTS 基线取实际科研文件；维护文件另列哈希，不进入科研项目托管范围。保留已发布 Windows 字节基线。

## 高优先级：节省用户 token

开发侧完成完整测试与发行检查。用户侧一次下载、一次 --apply，不要求先预览或反复让模型读取清单。确定性检查、备份与恢复由脚本完成，成功短回执，明细本地按需读。普通科研任务不触发发行校验；环境检查按需执行。科研证据与写后回读保留。

## 指南与版本

版本来源为 tools/release/upstream.json，独立于 maRkdown 引用版本。每次发布前根据实际功能更新 README.md、USER_GUIDE.md、产品用法和 tools/release/version-notes.md，核对版本、发布页与唯一 ZIP 下载链接。版本说明作为 Release 正文，不复制进科研目录。

## 检查与构建

```text
python tools/build_release.py --prepare
python -m unittest discover -s tests -v
python tools/build_release.py --check
python tools/build_release.py --preview-build outputs/releases/laRkdown-v<版本>.zip
```

prepare/check 使用工作树中可提交的源文件，按 .gitattributes 规范化文本。预览构建供未提交改动审核。检查通过后提交所有公开变更，从干净提交运行 --build。变更科研 schema 时先实现并验证迁移；私人登记、凭证、科研资料和缓存不得进入发行物。

推送版本 tag 前完成全部测试和发布检查。CI 核对 tag 与版本，发布唯一 ZIP 和校验附件，使用维护版本说明创建 Release。不手工绕过流程，不改写已发布 tag。
