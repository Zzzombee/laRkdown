# laRkdown

laRkdown 帮你用豆包整理科研工作，并把研究记录保存在飞书知识库中。

你可以直接告诉豆包今天做了什么实验、观察到了什么，让它整理项目现状、维护研究问题，或根据已有记录梳理项目故事。后续讨论可以围绕这些持续更新的记录展开。

当前版本：**v0.3.0** · [下载安装包](https://github.com/Zzzombee/laRkdown/releases/download/v0.3.0/laRkdown-v0.3.0.zip) · [使用指南](USER_GUIDE.md) · [版本说明](https://github.com/Zzzombee/laRkdown/releases/tag/v0.3.0)

## 可以用它做什么

- **记录实验进展**：把口述或零散笔记整理到项目现状，区分观察、结论和待验证假设。
- **梳理研究问题与故事**：追踪尚未解决的问题，根据已有证据组织论文思路，并标明目标叙事与实际结果的区别。
- **整理 PPTX 材料**：提取文字、备注和图表信息，结合图片核验后整理进科研记录。
- **编辑正文、核验文献**：润色学术表达，检查引用来源及其对论点的支持。
- **生成协作表格**：将科研文档整理成飞书多维表格，方便浏览和协作；文档继续作为事实来源。

例如，做完实验后可以直接说：

> 今天做了……实验，观察到……。请整理进项目现状，区分直接观察和可能的解释，缺少的信息标为待补。

## 第一次使用

在能够操作本地文件、运行命令的豆包工作任务中，发送：

> 请读取 https://raw.githubusercontent.com/Zzzombee/laRkdown/v0.3.0/USER_GUIDE.md，帮我安装 laRkdown v0.3.0，安装到【目标目录】。按照指南准备环境，打开科研项目，并带我完成必要的飞书授权。PPTX 功能等我需要时再准备。

也可以先手动下载上面的安装包，解压后让豆包继续操作。解压后有两个目录：

```text
laRkdown/       你的科研项目，在豆包中打开这个目录
maintenance/    环境准备和升级工具，与科研目录并列保留
```

环境入口会检查电脑上实际可用的 Python 和官方飞书 CLI，复用兼容工具，缺少时自动补齐。Windows 无需提前安装 Python 或 Node；macOS/Linux 的环境要求和手动命令见[使用指南](USER_GUIDE.md)。

软件和授权准备好后，告诉豆包你的研究体系及范围，即可建立项目现状、项目故事和研究问题。已有飞书记录时，可以提供链接绑定。技能未自动识别时，按使用指南导入。

## 已有项目如何更新

下载同一个 v0.3.0 安装包，解压到原科研项目之外的单独目录，然后告诉豆包：

> 请按照新包 maintenance/UPGRADING.md 的说明，将【原科研目录】升级到 v0.3.0。升级成功后为原项目准备环境，继续使用原来的飞书记录。出现冲突时停止并报告。

升级工具会先核验文件并备份，保留科研资料和飞书登记；用户修改与新版发生冲突时会停止。完成后继续打开**原科研目录**，无需重新初始化。详细命令及中断恢复方法见[升级说明](tools/UPGRADING.md)。

## 参与开发

本仓库用于源码开发。日常科研请使用 Release 安装包中的 `laRkdown/` 目录。

- `product/`：随安装包交付的科研规则、技能和运行脚本。
- `tools/`：环境准备、升级、构建和发布工具。
- `tests/`：使用合成数据和模拟接口的离线测试。

开发验证运行 `python -m pip install -r product/requirements.txt`，然后运行 `python -m unittest discover -s tests -v`。目录约定与发布步骤分别见[开发目录说明](tools/project-layout.md)和[发布规范](tools/RELEASING.md)。

laRkdown 基于 [maRkdown v0.1.0](https://github.com/Zzzombee/maRkdown) 改编，来源记录保存在 `tools/release/upstream.json`，原有第三方许可随包保留。环境组件的来源和许可见[环境说明](tools/ENVIRONMENT.md)。
