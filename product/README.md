# 个人科研项目

在豆包工作中打开直接包含 AGENTS.md 和 `.agents/skills/` 的本目录。科研记录使用飞书知识库中的“项目现状”“项目故事”“研究问题”；本地文件用于提取材料、工作稿和校验。

## 环境准备

首次准备时读取 AGENTS.md 和 `.agents/instructions/feishu-workflow.md`。确认五个科研技能及其完整资源可用：学术写作编辑、科研状态维护、PPTX 证据提取、学术文献核验、知识库文档转多维表格。

节省用户 token 为高优先级；环境准备仅在首次使用、发生变化或相关调用失败时执行，日常直接处理科研任务。

复用已有 Python 3.11+、Node.js/npm 与官方飞书 CLI。Python 依赖在 requirements.txt；可在本目录建立 `.venv/`，使用该环境安装依赖并运行科研脚本。

```text
python -m venv .venv
```

Windows：`.venv/Scripts/python.exe -m pip install -r requirements.txt`。
macOS/Linux：`.venv/bin/python -m pip install -r requirements.txt`。

缺少官方 CLI 时按其当前官方说明安装，读取本机帮助与内嵌技能，不能凭旧说明猜参数：

```text
npx @larksuite/cli@latest install
lark-cli skills read lark-shared
lark-cli skills read lark-doc
lark-cli skills read lark-wiki
lark-cli skills read lark-base
```

先检查 `lark-cli auth status --json`，复用有效用户身份。尚未配置应用或缺少授权时，按内嵌 lark-shared 指引准备实际授权链接或二维码，由用户本人完成授权。默认 `--as user`，凭证留在 CLI 认证存储。运行下列只读检查后说明工具与权限缺口，不因环境检查创建科研文档：

```text
python .agents/skills/maintain-research-state/scripts/feishu_bridge.py --root . preflight
```

## 开始记录

新项目可发送：“研究体系名称是……，研究范围是……。请在飞书创建同名知识空间和《项目现状》《项目故事》《研究问题》三篇知识库文档，完成后给链接。”已有记录则提供其链接并绑定，不重复初始化。

刚做完实验，直接说：“我刚做了……实验，观察到……；请立刻整理进知识库文档《项目现状》，区分观察、结论与假设，缺的信息标注待补。”不需要先制作 PPTX。

其他入口：

- “从这个 PPTX 提取证据并更新《项目现状》：文件路径。”
- “根据《项目现状》和《研究问题》生成《项目故事》的初稿。”
- “根据这次结果修订《项目故事》，保留当前证据边界。”
- “把三篇知识库文档构建为知识库多维表格。”之后可说“同步知识库多维表格”。
- “润色这篇知识库文档，保留数据、引用和证据强度。”
- “为这个研究问题查找并核验相关学术文献。”

只问用法或科研问题时不修改记录。图片证据须实际打开查看；结构提取或 OCR 不能替代视觉核验。缺少渲染器、图片入口或参数时如实指出缺口。

## 正式记录

“项目现状”是事实源，知识库多维表格是派生协作视图。修改前读取最新正文、版本与 block ID，局部编辑后回读。保留阴性、不显著和矛盾信息，保护人工编辑、图片与附件。

本机登记为 `.agents/config/feishu-documents.json`；配置示例为 `.agents/config/feishu.example.json`。工作稿进入 `.work/`，明确要求的正式本地导出及完成记录进入 `outputs/`。不要复制私人登记或凭证到另一个科研项目。
