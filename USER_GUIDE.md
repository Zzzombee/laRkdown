# laRkdown 使用指南（v0.3.0）

laRkdown 是面向豆包工作、飞书知识库的个人科研预设，源于 [maRkdown](https://github.com/Zzzombee/maRkdown)。用自然语言记录实验、维护研究问题和项目故事，无需自己编写文档格式。

## 第一次使用

在能处理本地文件与运行命令的豆包工作任务中说：

> 请读取 https://raw.githubusercontent.com/Zzzombee/laRkdown/main/README.md，下载最新已发布的 laRkdown 统一 ZIP 到我指定的目录。运行随包环境入口，复用已有兼容工具，缺失时自动补齐；先准备基础科研，PPTX 按需启用。只打开 laRkdown/ 科研目录，确认五技能并带我完成实际需要的飞书用户授权。

自动下载失败时，从 [v0.3.0 发布页](https://github.com/Zzzombee/laRkdown/releases/tag/v0.3.0)下载 [laRkdown-v0.3.0.zip](https://github.com/Zzzombee/laRkdown/releases/download/v0.3.0/laRkdown-v0.3.0.zip)，解压得到并列的 laRkdown/ 和 maintenance/。

Windows 执行 `powershell -NoProfile -ExecutionPolicy Bypass -File <解压目录>/maintenance/bootstrap.ps1`；macOS/Linux 执行 `sh <解压目录>/maintenance/bootstrap.sh`。可让豆包代为执行。无需提前装 Python 或 Node；入口检测用户机实际环境，缺失才下载。macOS/Linux 需具备 curl、tar 和 SHA-256 工具，支持 Intel/ARM64 的 macOS 与 glibc Linux。

基础准备不装 PPTX 包。工具与研究脚本固定使用实际选中的路径，不改系统默认 Python、PATH 或已有包。软件准备不等于飞书已授权；按提示亲自完成必要授权，有效身份复用。环境检查不创建科研记录。

在豆包只打开直接包含 AGENTS.md、README.md、run.py 和 .agents/skills/ 的 laRkdown/。技能未识别时按当前客户端“导入技能”入口导入五技能，不假设所有入口自动加载。

随后说：“研究体系是……，范围是……。请初始化同名知识空间及项目现状、项目故事、研究问题。”已有记录则提供链接绑定，不重建。故事开始为空框架。

## 日常请求

- 刚做完实验：“我做了……，观察到……。请整理到项目现状，区分观察、结论和假设，关键参数缺失标待补。”
- 项目问答：“根据项目现状和研究问题，哪些问题仍未解决，各有什么观察依据？”需要修改时明确要求写回。
- PPTX：“从本地 PPTX（路径）提取并核验图表证据，更新项目现状。”首次按需准备隔离依赖；看图/渲染缺口须说明，不能猜参数。
- 故事：“根据已有记录生成/修订项目故事。”无需 PPTX，真实支持与目标叙事分开。
- 六表：“把三篇文档构建为知识库多维表格”；之后说“同步知识库多维表格”。文档仍为事实源，人工备注受保护。
- 学术编辑与文献：“润色正文并保留数据/引用/证据强度”；“为研究问题检索并核验文献”。

正常任务只读相关资料，成功给简短回执和实际链接；保留证据核验、写前读取、写后回读。环境只在首次、变化或相关失败时检查。

## 已有项目

下载同一新 ZIP，在旧目录外解压；让豆包一次执行 `python <新目录>/maintenance/upgrade_larkdown.py --project <原科研目录> --apply`。脚本核验、备份、保护人工修改与私人登记；冲突时才需处理。然后对原科研目录运行新包的环境入口（Windows -Project，sh 第一个参数），更新本机路径，继续使用，无需重新初始化。缺 Python 可先用环境入口为新解压科研目录准备软件，再用其选中解释器执行升级。

项目源自 maRkdown v0.1.0，来源版本与 laRkdown 版本独立。后续版本以对应说明为准；豆包的入口、身份与权限以实际会话为准，不承诺所有用户预装 Python/CLI。
