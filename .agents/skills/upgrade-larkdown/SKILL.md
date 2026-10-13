---
name: upgrade-larkdown
description: 用户要求升级已初始化的 laRkdown 项目或检查版本兼容性时使用；预览差异并保留科研资料、飞书文档登记和同步基线。
---

# 升级已有 laRkdown 项目

从**新版本发行包**运行升级器，目标是已有科研项目。先读取目标 AGENTS.md、当前版本和[升级说明](../../../UPGRADING.md)。

使用新版本完整发行包里的 `upgrade_larkdown.py`。项目根目录的实际路径由用户提供或当前工作区确定；不猜豆包技能托管路径。先预览，报告新版本、增删改与冲突；用户明确要求升级时执行应用。示例：

```text
python <新版本解压目录>/upgrade_larkdown.py --project <已有科研项目目录> --package <新版本的 laRkdown-vX.Y.Z.zip>
python <新版本解压目录>/upgrade_larkdown.py --project <已有科研项目目录> --package <新版本的 laRkdown-vX.Y.Z.zip> --apply
```

当前版本的升级器也支持 `--latest`：从 `Zzzombee/laRkdown` 公共 GitHub Release 下载 ZIP 并校验 SHA256；API 限流时改用 Release 页面与 `.sha256` 附件。无 GitHub 网络时使用已下载的 `--package`。如果旧项目还没有升级器，先下载并解压含升级器的新版本，再运行其脚本。

AGENTS.md 中不重叠的用户增补会自动按行合并；同一处编辑冲突或其他托管规则、技能被修改时，任何冲突都阻止整次应用，不默默覆盖。项目内 `.agents/config/*.local.json`、飞书文档登记、`.work/`、`sources/`、`outputs/` 和已有飞书资源不在升级器托管范围内。升级文件时先做本地备份和写前日志；中断后运行同脚本 `--project <目录> --recover`，核对后完成或回滚。

版本跨度不受支持或缺少必要迁移时停止并说明。升级后确认豆包打开的项目根目录含 `.agents/skills/`，刷新并检查六个技能；若未识别，再按当前客户端的导入方式处理。核对飞书文档登记与同步基线，科研记录同步另按用户指令执行。
