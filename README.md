# laRkdown

面向豆包工作与飞书知识库的个人科研预设。科研源码在 product/，构建、环境准备和升级工具在 tools/，离线验证在 tests/；开发与科研 AGENTS 分离。本仓库不直接作为科研项目打开。

当前版本 v0.3.0。部署前说明见 [USER_GUIDE.md](USER_GUIDE.md)，下载见 [v0.3.0 Release](https://github.com/Zzzombee/laRkdown/releases/tag/v0.3.0)。

## 给豆包的部署入口

> 请下载 laRkdown 最新已发布的统一 ZIP，解压到我指定的目录。运行其中 maintenance/ 的环境入口，复用兼容 Python 和官方 CLI，缺失时补齐；先准备基础科研，PPTX 按需启用。只把 laRkdown/ 作为项目打开，确认五技能可用，带我完成实际需要的飞书用户授权。检查环境不创建科研记录。

ZIP 内 laRkdown/ 是科研预设，maintenance/ 是独立工具。Windows 一次执行 `powershell -NoProfile -ExecutionPolicy Bypass -File <解压目录>/maintenance/bootstrap.ps1`；macOS/Linux 执行 `sh <解压目录>/maintenance/bootstrap.sh`。默认准备相邻科研目录，其他目标按工具帮助指定。环境入口不操作飞书数据；有效身份复用，不重建已有科研记录。

五技能：学术编辑、状态维护、PPTX/故事与路线、文献核验、知识库六表。刚做完实验直接告诉豆包“我做了……，观察到……，请整理进项目现状”；科研任务按需读相关规则，写前取最新内容并写后回读。

## 开发与交付

product/ 是科研包唯一源码；tools/release/ 保存版本、发行清单及历史基线。根 README/USER_GUIDE、tests/、构建脚本不进科研目录。完整边界见 [目录合同](tools/project-layout.md)。

```text
python -m pip install -r product/requirements.txt
python tools/build_release.py --prepare
python -m unittest discover -s tests -v
python tools/build_release.py --check
python tools/build_release.py --preview-build outputs/releases/laRkdown-v0.3.0.zip
```

预览仅用于本地审核；公开发行需干净提交构建并由 CI 发布，不能直接 git archive 根目录。[发行规范](tools/RELEASING.md)。不在开发仓库初始化科研或访问真实飞书。

已有项目下载同一 ZIP，在旧项目外解压后一次执行 `python <新目录>/maintenance/upgrade_larkdown.py --project <原科研目录> --apply`。脚本核验、冲突检查、备份与恢复，成功短回执；后续运行环境入口更新本机路径。日常不触发发行检查。[升级与恢复](tools/UPGRADING.md) · [环境与组件来源](tools/ENVIRONMENT.md)。

来源固定 maRkdown v0.1.0，逐文件记录在 tools/release/upstream.json；第三方学术技能 LICENSE 保留。固定工具与依赖记录在维护目录，不宣称豆包为所有用户预装环境。结构提取、原图保留、渲染和实际视觉核验分别验收；脚本通过不能代替科学判断。
