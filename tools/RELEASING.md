# 仓库发布规范（不进入用户产品 ZIP）

`laRkdown-v<版本>.zip` 是供豆包工作打开的精简产品包。它只包含根目录 `README.md`、`AGENTS.md`、`UPGRADING.md`、`requirements.txt`、`upgrade_larkdown.py`、发行清单，以及运行时的 `.agents/instructions/`、`.agents/skills/` 和白名单公开配置。仓库的 `.github/`、`.gitignore`、`tests/`、`tools/`、计划与构建资料均不打包。运行时目录合同 `.agents/instructions/project-layout.md` 和 `.agents/config/project-layout.json` 必须保留。

只改用户指定范围。保留第三方 LICENSE。修改可执行脚本后做对应行为检查；没有科研条目变更时不运行真实科研状态审计。文档中引用官方来源并记录核验日期，推断与未实测能力分开。

每个公开 Release 必须携带 `upgrade_larkdown.py`、`upgrade-larkdown` 技能、`.agents/config/release-manifest.json`、旧版基线和 `UPGRADING.md`。发行版本与 maRkdown 引用版本分别记录。科研项目结构版本变化时先实现并验证迁移，否则发布检查必须失败。不能为方便发布删除升级器或跳过冲突与恢复检查。

发布前暂存所有发行文件，运行 `python tools/build_release.py --prepare` 并暂存生成的清单；再运行 `python -m unittest discover -s tests -v`、`python tools/build_release.py --check`，提交后用 `python tools/build_release.py --build <ZIP路径>` 构建并核对成员清单。打包只使用该脚本的 `--build`。推送版本 tag 后，由 `.github/workflows/release-contract.yml` 在检查通过时自动创建 Release 并上传 ZIP 与同名 `.sha256` 附件；不要绕过流程手工创建 Release，也不可修改已发布 tag 的内容。
