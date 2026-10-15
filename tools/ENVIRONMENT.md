# 环境准备

从同一 ZIP 解压得到并列的 laRkdown/ 与 maintenance/。安装器仅准备软件，不创建飞书资源、不读取科研正文、不检查或重做授权。只把 laRkdown/ 作为科研项目打开。

## 一次入口

Windows 无需先装 Python 或 Node。在终端或豆包任务中执行：

```text
powershell -NoProfile -ExecutionPolicy Bypass -File <解压目录>/maintenance/bootstrap.ps1
```

macOS/Linux（x86_64/ARM64，Linux 为 glibc 环境；需已有 curl、tar 和 SHA-256 工具）：

```text
sh <解压目录>/maintenance/bootstrap.sh
```

默认目标是同包相邻 laRkdown/。已有科研目录用 Windows `-Project <目录>`；sh 用第一个参数。不会复制、覆盖或清理科研内容。开发 checkout 和 product/ 源码被拒绝。已有安装需要先按 UPGRADING.md 更新科研文件，再准备环境。

已有合适 Python 也可直接执行 `python maintenance/setup_larkdown.py --project <科研目录>`。当前复用范围为 Python 3.11～3.14，并检查 SSL、标准库和实际解释器；PPTX 分支才额外检查 venv/ensurepip，缺失时准备完整受管运行时。不把命令名存在或更高版本当成兼容证据。Windows 还查本机登记与 Python 注册表。缺失时通过固定版本 uv 准备独立的 CPython 3.13.15；不修改系统 PATH、默认 Python、注册表或用户已有包。

## 复用与按需补齐

- 基础准备复用能通过所需本地帮助检查的官方 CLI；不因版本号不同强制升级。npm shim 优先定位其原生二进制，必要时明确使用 Node runner。缺失或不兼容时下载已核验的官方 CLI 1.0.97；不要求安装 Node/npm。
- CLI 检查只调用版本及命令帮助，不访问飞书。软件就绪不代表用户身份或权限就绪；之后按当前官方 lark-shared 完成实际所需授权，复用有效身份。
- 首次使用六表同步：Windows 添加 `-Feature base`；sh 第二参数为 `base`；Python 添加 `--feature base`。只核对额外 CLI 接口，不安装 PPTX 包。NDJSON 返回合同仍由同步脚本在实际读取时严格检查。
- 首次使用 PPTX：同理选择 `pptx`。在项目 .work/setup/environments/ 建立独立环境，使用锁定版本、传递依赖及 wheel 哈希；保留中断状态，重跑同一入口续装。不自动安装 PowerPoint，不将结构提取成功视为完整视觉验收。
- 基础路径不运行 pip、不连接 PyPI、不检测渲染器。重复准备复用未变的 CLI 检查结果；日常科研不运行安装器。

`--python`/`-Python` 可指定解释器；Python 入口的 `--cache`、Windows 的 `-Cache` 可指定缓存。缓存默认位于 Windows LOCALAPPDATA/laRkdown 或 macOS/Linux 的 XDG_CACHE_HOME/laRkdown（未设置时 ~/.cache/laRkdown）。归档按固定 SHA-256 校验，已修改缓存保留并停止；不以强制删除解决问题。

成功只返回 features、配置与报告位置。本机配置 `.agents/config/runtime.local.json` 保存实际解释器/CLI 路径，不含凭证；`.work/setup/` 保存状态和报告，不纳入发行或迁入另一个项目。进程锁自动释放；失败后重跑同一入口。依赖环境不会在创建后移动。

## 科研脚本入口

科研目录下使用 `powershell -NoProfile -File ./run.ps1 <命令> [参数]`，或用已选解释器执行 `python run.py <命令> [参数]`。run.py 再使用登记的实际解释器和 CLI，不依赖 shell 激活或旧 PATH。入口只允许已声明科研脚本；不能拿它运行任意外部路径。

命令：feishu、initialize、validate-state、base、pptx-check、pptx-extract、pptx-media、pptx-sheets、pptx-validate。具体参数由各技能说明。配置路径变化或调用失败时重做相关环境准备。

## 来源、固定组件与许可

runtime-assets.tsv 是组件来源、平台、固定版本与归档 SHA-256；Python 版本由其 python 行指定，uv 自带固定构建目录及校验信息。安装用 HTTPS 和有限超时，不使用 latest 或关闭 TLS 验证。PPTX 包锁在 pptx-requirements.lock，包含 python-pptx、Pillow、lxml、XlsxWriter、typing_extensions。

- uv 0.12.20：[官方发行](https://github.com/astral-sh/uv/releases/tag/0.12.20)，MIT/Apache-2.0 原文在 third-party/uv-LICENSE-*。
- CPython：[项目及许可](https://www.python.org/about/legal/)，由 uv 使用 [python-build-standalone](https://github.com/astral-sh/python-build-standalone) 分发；保留下载运行时中的许可文件。
- lark-cli 1.0.97：[官方发行](https://github.com/larksuite/cli/releases/tag/v1.0.97)，MIT 原文在 third-party/lark-cli-LICENSE；提取时同时保留归档 LICENSE。
- PPTX 依赖来自各自 [PyPI](https://pypi.org/) 固定版本；wheel 中的 dist-info、LICENSE、版权与来源记录由包管理器完整保留。科研技能原有 LICENSE 不修改。

复用用户已有工具只作能力检查，无法据此证明组件由豆包预装。CLI 本地帮助通过不能认证远端冲突、实际权限或完整科研流程；真实客户端验收必须在开发仓库之外进行。
