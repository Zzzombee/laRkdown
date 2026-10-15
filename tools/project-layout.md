# 开发目录合同

- 仓库根目录：开发 AGENTS.md、README.md、USER_GUIDE.md 和 Git 配置。
- `product/`：科研包唯一源码根目录。此处 AGENTS.md、README.md、requirements.txt 和 `.agents/` 映射到用户科研项目同名路径；禁止加入维护内容。
- `tools/`：构建及独立升级工具、发布规范、隔离设计；`tools/release/`：版本来源、发行清单、历史基线和发行说明。发行时映射为 ZIP 内与 laRkdown/ 并列的 maintenance/，不放入科研目录。
- `tools/bootstrap.ps1`、`bootstrap.sh`、`setup_larkdown.py`：独立环境准备入口；固定组件来源、PPTX wheel 锁和第三方许可同属维护目录。`product/run.py`、`run.ps1` 仅运行科研工具，不安装或管理发行内容；本机路径配置和依赖环境不进发行包。
- `tests/`：离线测试，不执行真实科研任务。
- `.planning/`、`.work/`：计划和临时校验；正式本地产物统一在 `outputs/`，构建包放在 `outputs/releases/`。

旧路径上的私人配置原地保留，不读取科研事实、不复制到 product/ 或发行物。用户运行产生的 sources、outputs、.work、.planning、凭证和本机登记均不纳入 Git 和发行包。
