---
name: upgrade-larkdown
description: 将已初始化的 laRkdown 科研项目升级到新的公开发行版本，预览文件差异并保护飞书文档登记、本机配置、科研资料和同步基线。用户要求升级现有项目、更新 laRkdown 技能或检查版本兼容性时使用；首次安装不触发。
---

# 升级已有 laRkdown 项目

区分“新版本发行包目录”和“用户正在使用的科研项目目录”。升级器从**新版本**运行，目标是已有项目。先读取目标 AGENTS.md、当前安装版本和[升级说明](../../../UPGRADING.md)；不初始化新科研文档或 Base。

使用新版本完整发行包里的 `upgrade_larkdown.py`。项目根目录的实际路径由用户提供或当前工作区确定；不猜豆包技能托管路径。先预览，报告新版本、增删改与冲突；用户明确要求升级时执行应用。示例：

```text
python <新版本解压目录>/upgrade_larkdown.py --project <已有科研项目目录> --package <新版本的 laRkdown-vX.Y.Z.zip>
python <新版本解压目录>/upgrade_larkdown.py --project <已有科研项目目录> --package <新版本的 laRkdown-vX.Y.Z.zip> --apply
```

当前版本的升级器也支持 `--latest`：从 `Zzzombee/laRkdown` 公共 GitHub Release 下载 ZIP 并校验 GitHub 提供的 SHA256，再预览或应用。无 GitHub 网络时使用已下载的 `--package`。如果旧项目还没有升级器，先下载并解压含升级器的新版本，再运行其脚本。

AGENTS.md 中不重叠的用户增补会自动按行合并；同一处编辑冲突或其他托管规则、技能被修改时，任何冲突都阻止整次应用，不默默覆盖。项目内 `.agents/config/*.local.json`、飞书文档登记、`.work/`、`sources/`、`outputs/` 和已有飞书资源不在升级器托管范围内。升级文件时先做本地备份和写前日志；中断后运行同脚本 `--project <目录> --recover`，核对后完成或回滚。

版本跨度不受支持、科研结构版本变化而缺迁移程序时停止并说明。文件升级成功后，提醒用户在豆包工作里刷新或重新导入升级过的技能目录；本地文件替换不证明平台注册已经更新。核对原文档登记仍指向同一批文档，再用项目适用的只读检查或预览验证；科研记录同步另按用户指令执行。
