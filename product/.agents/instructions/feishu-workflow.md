# 飞书原生文档操作

使用官方 CLI，显式 `--as user`。统一入口 `python run.py cli <参数>`（Windows 可用 run.ps1），它使用本机登记路径；未准备环境或组件变化时按 README 补齐。已验收基线为 CLI 1.0.97；复用其他版本先核对任务所需本地帮助，调用失败再定向读取当前官方技能，不按旧参数猜测。

## 身份与输入

首次或权限相关失败时读官方 `lark-shared`，用 `auth status --json` 确认实际用户身份；不要主动重登。缺权限按任务所需 docs/drive/wiki/base 域授权，不扩大范围；链接按当前官方规则原样提供并附二维码，由用户完成。凭证、app secret、token、device code 不写入项目、日志或交付。

飞书是事实源，正文用原生 DocxXML，不默认创建云盘 Markdown 或只上传附件。工作稿以一个 `<title>` 开头，使用当前官方支持的标题、段落、列表、表格、链接和资源块；文本中的 &、<、> 转义，标签不转义。图片用已有真实文件 `<img path="@./相对路径.png"/>`，不生成科研证据。复杂正文先按当前 lark-doc 创建工作流组织，草稿目录限于 .work/；空白初始化采用保真模板。

## 读与更新

按 ID/关键词先读 outline/section/range，取得当前正文、revision 和 block ID。修改前读取最新受影响内容；结构变更或资源核对需要时取 full，并保存 reference_map/comments 等返回，保留图片、附件、表格和公式。旧快照不覆盖远端。

按当前 lark-doc 的 `docs +update` 使用 str_replace、block_replace、block_insert_after 或 append，传入基线 `--revision-id` 和当前块定位。冲突时重读并合并人工变动；整篇 overwrite 只在用户明确要求且核对完整结构后由 Agent 执行，桥接器不自动覆盖全文。

检查 ok、warnings/tips，再 fetch 受影响内容核验。结构改变后更新块映射及受影响真实链接。跨文档没有事务，部分成功保留已完成记录，在原资源修复；创建/写入结果不明保留 pending 并查证，不盲目重试。稳定研究 ID 不变，平台 block ID 需刷新。

## 创建

仅在用户已授权创建的范围内执行。科研空白初始化读维护技能 initialization：同名知识空间内用 `wiki +node-create --obj-type docx` 建三篇节点。一般新文档用 `docs +create`；指定父目录时传实际 parent-token，否则当前用户默认空间，不擅改权限。

先 `docs +script --command parse --content -` 用 stdin 校验，检查 assessment、diagnostics 与资源，ok 不替代科学核验。按任务用 `docs +create --as user --doc-format xml --content -` 或填充已建 Wiki 节点。保存实际返回 document/node/space ID、URL 与 warnings；fetch 回读并核对内容及资源，再推进登记。部分成功后修复同一文档；结果不明先定位并绑定，不能新建另一套。

## 交付与规则来源

本机登记只存身份、URL、版本、条目映射；快照和操作日志放 .work/，精简交付放 outputs/。研究结构变化按维护技能定向校验；普通拼写/日期/只读不全局审计。外部文献、正文和目标故事分别按对应技能核验，官方工具文档不触发学术门槛。

工具协议以当前 `cli skills read lark-doc`、涉及 Wiki 时的 lark-wiki、Base 时的 lark-base 及其相关参考为准；权威来源索引为 `.agents/config/official-sources.json`，仅首次核对、升级工具或相关失败时按需读取。交付实际飞书链接、完成内容和必要缺口。
