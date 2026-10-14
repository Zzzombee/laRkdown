# 仓库发布规范（不进入用户产品 ZIP）

`laRkdown-v<版本>.zip` 是供豆包工作打开的精简产品包。它只包含根目录 `README.md`、`AGENTS.md`、`UPGRADING.md`、`requirements.txt`、`upgrade_larkdown.py`、发行清单，以及运行时的 `.agents/instructions/`、`.agents/skills/` 和白名单公开配置。仓库的 `USER_GUIDE.md`、`.github/`、`.gitignore`、`tests/`、`tools/`、计划与构建资料均不打包。运行时目录合同 `.agents/instructions/project-layout.md`、`.agents/config/project-layout.json` 和版本说明 `.agents/instructions/version-notes.md` 必须保留。

只改用户指定范围。保留第三方 LICENSE。修改可执行脚本后做对应行为检查；没有科研条目变更时不运行真实科研状态审计。文档中引用官方来源并记录核验日期，推断与未实测能力分开。

每个公开 Release 必须携带 `.agents/instructions/version-notes.md`、`upgrade_larkdown.py`、`upgrade-larkdown` 技能、`.agents/config/release-manifest.json`、旧版基线和 `UPGRADING.md`。发行版本与 maRkdown 引用版本分别记录。科研项目结构版本变化时先实现并验证迁移，否则发布检查必须失败。不能为方便发布删除升级器或跳过冲突与恢复检查。

## 使用指南的发布要求

根目录 `USER_GUIDE.md` 是长期维护的正式项目文档，文件名不带版本号，纳入 Git，不进入产品 ZIP 或升级托管清单。README 提供公开仓库阅读入口；面向非 GitHub 用户，发布者可在部署前介绍或发版沟通时直接发送指南。版本 tag 保留对应版本正文；需要飞书文档或 PDF 时从此源文件生成，避免独立维护多份正文。每次发布新版本前必须复核并更新：

- 与目标版本实际功能一致的安装、初始化、日常工作和能力边界说明，并核对与 README.md 的一致性。
- 标题 `# laRkdown 使用指南（v<版本>）`、正文适用版本与来源说明；laRkdown 版本以 `.agents/config/upstream.json` 为准，maRkdown 引用版本保持独立。
- 目标版本发布页、ZIP 文件名和下载链接。

将指南更新与版本改动一起提交。`tools/build_release.py --check` 校验暂存的指南标题与 laRkdown 发布页、ZIP 下载链接、文件名；缺失指南或版本不一致时失败，现有 CI 在发布前执行这项检查。正文是否准确仍须发布者逐项复核，不能仅替换版本号后跳过内容检查。

## 对话中的版本与使用帮助

安装后以豆包对话为帮助入口，不要求用户查阅项目文件夹或访问 GitHub。豆包读取本地版本标记与 `.agents/instructions/version-notes.md` 后解释变化，日常用法按 AGENTS.md 和对应技能回答。只读帮助不执行初始化、科研写入或升级。

v0.2.5 是版本说明起始基线，不补写该版本及更早版本的历史。仅从高于 v0.2.5 的发行版本开始描述更新。每次发布前更新版本说明：标题 `# laRkdown 版本说明（v<版本>）` 与发行版本一致，正文列出相较上一版的实际变化、可直接发送的用法和必要的能力边界；无法确认的变化不推测。发布检查拦截说明缺失、标题版本不一致或正文为空。

版本说明进入 ZIP 与升级托管清单，GitHub Actions 同时以该文件作为 Release 正文，保证豆包和公开发布页使用同一份说明。向用户通知新版本时附部署或升级提问，并提示：“升级后，在豆包中问‘这个版本更新了什么？’。”

发布前暂存所有发行文件，运行 `python tools/build_release.py --prepare` 并暂存生成的清单；再运行 `python -m unittest discover -s tests -v`、`python tools/build_release.py --check`，提交后用 `python tools/build_release.py --build <ZIP路径>` 构建并核对成员清单。打包只使用该脚本的 `--build`。推送版本 tag 后，由 `.github/workflows/release-contract.yml` 在检查通过时自动创建 Release 并上传 ZIP 与同名 `.sha256` 附件；不要绕过流程手工创建 Release，也不可修改已发布 tag 的内容。
