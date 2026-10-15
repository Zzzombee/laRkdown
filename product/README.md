# 个人科研项目

在豆包工作打开直接包含 AGENTS.md 与 `.agents/skills/` 的本目录。五个技能用于学术编辑、科研记录、PPTX/故事、文献核验和知识库六表。

## 首次准备

用下载包中与本目录并列的独立环境入口准备软件：Windows 执行 `powershell -NoProfile -ExecutionPolicy Bypass -File ../maintenance/bootstrap.ps1`；macOS/Linux 执行 `sh ../maintenance/bootstrap.sh`。当前目录与入口不在相邻位置时指定实际科研目录。首次准备、环境变化或相关失败时才运行；日常直接做科研。

入口检查实际 Python 和官方 CLI，复用兼容组件，缺失时自动补齐，不假设豆包预装。当前 Python 复用范围为 3.11～3.14。基础准备不安装 PPTX 依赖、不改系统 PATH 或已有包；本机路径保存在 `.agents/config/runtime.local.json`，不含凭证，不复制到其他项目。

软件准备后，读当前官方 `lark-shared`，检查已有用户身份；有效就复用。确需配置/授权时提供实际官方链接和二维码，由用户本人完成，不为检查环境创建科研文档。CLI 技能与命令帮助按任务读取，不一次加载所有域。

科研目录下统一运行：Windows `powershell -NoProfile -File ./run.ps1 <命令> [参数]`；其他入口用已选 Python 执行 `python run.py <命令> [参数]`。Windows run.ps1 会读取已选解释器，不依赖激活虚拟环境。常用命令：cli（官方 CLI）、feishu、initialize、validate-state、base、pptx-check/extract/media/sheets/validate；具体参数见对应技能。

首次六表任务以 base 功能重跑环境入口：Windows 加 `-Feature base`；sh 为 `sh ../maintenance/bootstrap.sh . base`。首次 PPTX 同理选择 pptx；依赖装入独立环境。缺少 PowerPoint/其他已核验渲染器或图片入口时，只处理可核实部分，不把结构提取当完整视觉验收。

## 常用请求

- 初始化：“研究体系是……，范围是……。请建立同名知识空间和项目现状、项目故事、研究问题。”已有记录提供链接绑定，不重复初始化。
- 即时记录：“刚做了……实验，观察到……。请整理进项目现状，区分观察与解释，缺信息标待补。”
- PPTX：“从这个 PPTX 提取并核验证据，更新项目现状：文件路径。”
- 故事：“根据项目现状与研究问题，生成/修订项目故事。”无需 PPTX。
- 六表：“把三篇知识库文档构建为知识库多维表格”；之后说“同步知识库多维表格”。
- 学术编辑：“润色这篇知识库文档，保留数据、引用和证据强度。”
- 文献：“为这个研究问题检索并核验文献。”

只问用法或问题时不改记录。正式事实以飞书文档为准；修改前读取最新内容和版本，局部编辑后回读，保护人工编辑与资源。工作稿放 .work/，明确要求的本地导出与精简完成记录放 outputs/。
