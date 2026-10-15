# 豆包部署指令

仅安装或升级 laRkdown 时读取。适用于 v0.3.0 起的统一 ZIP。按下列步骤执行，无需再读仓库 README 或 USER_GUIDE；安装后按科研项目 AGENTS 和任务相关技能做科研。

## 输入与下载

- 新安装需要目标安装目录；升级需要原科研目录。缺少必要路径时一次询问。原目录已有项目时保留，先明确用户要新建还是升级。
- 用户指定版本时读取 `https://api.github.com/repos/Zzzombee/laRkdown/releases/tags/<tag>`；未指定时读取 `https://api.github.com/repos/Zzzombee/laRkdown/releases/latest`。
- 从该 Release 下载 `laRkdown-<tag>.zip` 及同名 `.sha256`，用系统工具核对 SHA-256。不匹配或附件缺失时停止。
- 用户已有解压包时，复用该目录和可用的原 ZIP、校验附件；缺少版本或完整性依据时从对应 Release 补齐并核对，不覆盖用户文件或重复安装到另一目录。
- 新安装解压到目标安装目录；升级解压到原科研目录之外的新目录。包内 `laRkdown/` 是科研项目，`maintenance/` 是并列工具目录。

## 新安装

1. 准备基础环境，运行以下对应系统的入口。路径含空格时正确引用。

   Windows：
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File "<解压目录>/maintenance/bootstrap.ps1"
   ```
   macOS/Linux：
   ```sh
   sh "<解压目录>/maintenance/bootstrap.sh"
   ```
2. 入口负责检查并复用兼容 Python/官方 CLI、补齐缺失组件。根据其简短 JSON 回执判断结果。成功后读取科研目录 `.agents/config/runtime.local.json`，后续使用其中实际登记的解释器与 CLI 路径。失败才读回执指向的报告；相关手动排障见同包 `maintenance/ENVIRONMENT.md`，无需全盘审计。
3. 将 `laRkdown/` 作为豆包科研项目打开。仅验证 academic-writing-editor、maintain-research-state、pptx-to-research-state、literature-source-gate、research-docs-to-base 五个科研技能是否可发现，未识别时引导用户使用客户端实际提供的技能导入入口。
4. 需要飞书身份时按当前官方 `lark-shared` 检查，复用有效用户身份；缺授权才提供官方授权入口，由用户本人完成。部署期间不创建科研资源。

## 升级已有项目

1. 用已有兼容 Python 执行下列命令。没有可用 Python 时，先对新解压的 `laRkdown/` 执行上面的环境入口，再从其 `runtime.local.json` 取解释器绝对路径。
   ```text
   <可用Python的绝对路径> <解压目录>/maintenance/upgrade_larkdown.py --project <原科研目录> --apply
   ```
2. 一次执行升级，脚本负责核验、备份、冲突保护和回执。冲突或未知版本时停止，按回执报告必要信息；不手工覆盖文件。中断恢复按同包 `maintenance/UPGRADING.md` 处理。
3. 成功后对**原科研目录**准备环境：Windows 在 bootstrap.ps1 后添加 `-Project "<原科研目录>"`；macOS/Linux 在 bootstrap.sh 后传入 `"<原科研目录>"`。
4. 重新打开原科研目录继续使用，保留原飞书登记和科研记录，无需重新初始化。

## 按需功能与完成回执

- 默认只准备 core。用户首次需要知识库六表时，同一入口选择 base；需要本地 PPTX 时选择 pptx。Windows 添加 `-Feature base` 或 `-Feature pptx`；sh 依次传科研目录和 `base` 或 `pptx`。
- 不预装 PPTX 依赖或渲染器；需要相关功能时再处理。软件准备成功不代表飞书已授权或 PPTX 已完成视觉核验。
- 成功仅报告版本、实际科研目录、环境与技能状态、是否还需用户授权。环境只在首次使用、环境变化或相关失败时检查；日常科研不重跑部署流程。
