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

## 开始使用

在能够操作本地文件、运行命令的豆包工作任务中，发送：

> 请按 https://raw.githubusercontent.com/Zzzombee/laRkdown/main/tools/DOUBAO_SETUP.md 安装 laRkdown v0.3.0，目标目录是【目标目录】。

第一次安装、飞书授权、日常请求示例和已有项目更新，都可以按[新手使用指南](USER_GUIDE.md)操作。上面的一句话让豆包直接读取独立的部署指令；本页介绍项目，使用指南向用户解释具体步骤。

## 参与开发

本仓库用于源码开发。日常科研请使用 Release 安装包中的 `laRkdown/` 目录。

- `product/`：随安装包交付的科研规则、技能和运行脚本。
- `tools/`：环境准备、升级、构建和发布工具。
- `tests/`：使用合成数据和模拟接口的离线测试。

开发验证运行 `python -m pip install -r product/requirements.txt`，然后运行 `python -m unittest discover -s tests -v`。目录约定与发布步骤分别见[开发目录说明](tools/project-layout.md)和[发布规范](tools/RELEASING.md)。

laRkdown 基于 [maRkdown v0.1.0](https://github.com/Zzzombee/maRkdown) 改编，来源记录保存在 `tools/release/upstream.json`，原有第三方许可随包保留。环境组件的来源和许可见[环境说明](tools/ENVIRONMENT.md)。
