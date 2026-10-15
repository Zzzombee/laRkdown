# laRkdown

laRkdown 为豆包工作与飞书原生个人科研管理提供预设。本目录是开发仓库；科研产品源码在 `product/`，开发测试与维护工具在 `tools/`、`tests/`。两份 AGENTS.md 分别服务开发和科研工作，不共用入口。

部署前说明见 [USER_GUIDE.md](USER_GUIDE.md)。当前源码正在准备 v0.2.6；此处链接与指南为待发布版本准备，不表示该版本已公开发布。

## 内容隔离

| 目录 | 职责 | 交付边界 |
| --- | --- | --- |
| 根目录 AGENTS.md | 本地开发、测试、发布 | 只在源码仓库使用 |
| product/AGENTS.md | 个人科研项目管理 | 映射为科研包根目录 AGENTS.md |
| product/.agents/ | 五个科研技能、飞书规则与科研配置 | 只进入发行 ZIP 的 laRkdown/ |
| tools/release/ | 版本来源、清单、历史基线与发行说明 | 只进入发行 ZIP 的 maintenance/ |
| tools/upgrade_larkdown.py | 项目外执行的升级工具 | 只进入发行 ZIP 的 maintenance/ |
| tests/、.github/、tools/build_release.py | 离线校验和构建 | 不进入科研包 |

laRkdown/ 科研目录不含发布、升级或版本管理指令。详细设计与历史迁移规则见 [隔离方案](tools/CONTENT_ISOLATION.md)。

## 给使用者的部署入口

从对应 [Release](https://github.com/Zzzombee/laRkdown/releases) 下载唯一的 `laRkdown-v<版本>.zip`，解压后得到并列的 laRkdown/ 科研目录和 maintenance/ 维护目录。在豆包工作打开直接包含 `.agents/skills/` 的 `laRkdown` 目录，按其 README.md 完成 Python、官方飞书 CLI 和用户授权。科研技能为学术编辑、科研状态维护、PPTX 证据提取、文献核验及知识库文档转多维表格，共五个。

也可交给豆包：“请读取本仓库 README.md，下载已公开发布的科研包并检查五个科研技能及工具环境，带我完成飞书用户授权。只使用科研包作为我的个人科研项目。”

开发源码不作为科研项目部署。若使用源码制作科研目录，应由构建工具导出 product/，不要复制仓库根目录 AGENTS.md 或 tools/。初始化前先检查已有飞书登记与用户文档，不覆盖或重建已有科研记录。

刚做完实验，可直接说：“我刚做了……实验，观察到……；请立刻整理进知识库文档《项目现状》，缺的信息标注待补。”还支持 PPTX 导入、项目故事生成或修订、学术正文编辑、文献核验和知识库多维表格协作。

## 开发与验证

```text
python -m pip install -r product/requirements.txt
python tools/build_release.py --prepare
python -m unittest discover -s tests -v
python tools/build_release.py --check
python tools/build_release.py --preview-build outputs/releases/laRkdown-v0.2.6.zip
```

预览包来自未提交源码，只用于本地审核。公开发布要求提交全部发行变更，使用 `--build` 从干净提交构建，再由 CI 发布。发行流程见 [tools/RELEASING.md](tools/RELEASING.md)。

## 一次升级

下载新版本同一个 ZIP，在旧项目之外解压。使用其中 maintenance/ 的升级器一次执行：

```text
python <新解压目录>/maintenance/upgrade_larkdown.py --project <原科研目录> --apply
```

脚本自动读取相邻的 laRkdown/，完成识别、核验、冲突检查、备份和更新。成功只输出简短结果；冲突时才需要人工或模型介入。完整日志保存在原科研目录 .work/upgrades/last-report.json。无须另下维护包或先执行预览；显式预览和详细输出仍可选。恢复与冲突规则见 [tools/UPGRADING.md](tools/UPGRADING.md)。升级不访问飞书、不重建科研记录。

## 高优先级：节省用户 token

确定性检查交给脚本，日志留本地按需读取。日常科研不触发发行校验；环境仅首次使用、发生变化或相关失败时检查。按任务读取相关技能与科研条目，成功简短回执。证据核验、写后回读、冲突保护和恢复保留。

## 来源与能力边界

上游固定为 maRkdown v0.1.0，逐文件来源位于 `tools/release/upstream.json`，与 laRkdown 发行版本独立。第三方学术编辑技能保留原 LICENSE。工具官方来源及核验日期位于 `product/.agents/config/official-sources.json`。

PPTX 结构提取、原图保留、整页渲染与实际视觉核验分别验收；图片加载和渲染能力须按使用者环境检查。脚本通过不能替代科学判断。测试只使用合成数据及模拟接口，不执行真实科研任务。
