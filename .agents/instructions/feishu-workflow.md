# 飞书原生文档工作流

默认官方 `lark-cli`，显式 `--as user`；当前验证基线为 1.0.97。每次工具升级以 `--help`、`lark-cli skills read lark-shared` 和 `lark-cli skills read lark-doc` 的当前说明为准。缺少 CLI 时按官方安装说明安装；不自动换成第三方同名工具。

## 格式与身份

正式记录使用 `docs` 创建的飞书原生文档，不默认创建云盘 Markdown 文件或仅上传本地附件。技能指令可用普通 Markdown；科研正文以 DocxXML 原生块编写，日期、证据等级和状态写成可见正文或原生元数据表。

完整工作稿以唯一 `<title>` 开头，正文用 `<h1>` 至 `<h6>`、`<p>`、列表、表格、`<a href="真实URL">标签</a>` 和必要图片。只用当前官方 XML 文档支持的标签。需要图片时 `<img path="@./相对路径.png"/>` 指向当前工作目录内已存在的真实图片，不能用生成图补造科研证据。只转义文字中的 &、<、>，不把标签本身转义。

`lark-cli auth status --json` 检查现有身份，不为了预防错误主动重新登录。缺少用户授权时按实际错误及最小 docs/drive scope 发起登录；不得将 app secret、access token 或授权 device code 写入项目、日志或分发包。认证链接按当前官方规则原样交付并附二维码，由用户完成账户授权。

## 创建文档

1. 确定目标文档、读者任务和用户已授权范围。新建科研记录或修订稿属于对应执行请求；不因只读问题创建文档。
2. 编写 XML 工作稿。复杂创作按当前 `lark-doc-create-workflow.md` 选择适用 contract 并 `docs +script --command init-draft` 建草稿；该命令的自动工作目录须位于项目 `.work/` 内。空白框架模板属于保真结构初始化，不要求重新设计体裁。
3. `docs +script --command parse --content -` 通过 stdin 检查；`ok=true` 只代表调用成功，还须检查 assessment、diagnostics 与资源。工作稿的来源、数值和证据边界另行核对。
4. `docs +create --as user --doc-format xml --content -`；有已指定父目录时加 `--parent-token`，否则使用当前用户默认空间，不擅自选择其他团队目录或改变权限。
5. 检查 `ok`、`data.document.document_id/url`、warnings/tips，然后 `docs +fetch --doc 实际ID --doc-format xml --detail full --as user` 回读。
6. 确认内容和必要图片资源，再将真实 URL、版本、稳定 key 和完成状态写入本机登记及 outputs 下的交付记录。

若创建已成功但资源上传或回读失败，修复同一文档。返回不确定、超时或连接中断时保留 pending 记录并查证，不重试新建来“保证成功”。Python 桥接器会保留 pending 闩锁，只有核实结果后才能解除；已有文档用 bind 登记。

## 更新记录

飞书是唯一事实源。先读最新 outline/keyword，再读相关 section/range；结构修改前按需要读 `full` 并保存完整 JSON（包括 reference_map 和 comments）。本地旧 XML 不可直接覆盖飞书。

使用当前 block ID 和读取版本做局部修改。行内文字用 str_replace，整块用 block_replace，增补用 block_insert_after 或 append。CLI 的 `--revision-id` 传入编辑基线；基线不同或出现版本冲突时重新读取，重新合并人类修改后再编辑。保留图像、表格、附件、公式及资源 token，不把它们降级为纯文本。整篇 overwrite 仅在用户明确要求整篇替换且已核对完整结构时由 Agent 直接执行，桥接器不提供自动覆盖功能。

写后读取受影响内容，重新建立研究 ID 到 block ID 的映射。不能继续使用结构修改前的旧 block ID。新 SOL 与其 RQ 链接在同一批变更中维护；飞书跨文档操作没有事务，失败时记录已完成部分，在同一文档中修复，不删除已写事实。

## 链接、校验与交付

标题保留 OBS-001 等研究编号。当前返回的标题 block ID 可用于 `文档URL#block_id` 定位；以官方 fetch 返回的 ID 为准，不自行生成锚点。跨条目链接先登记并回读目标，后写真实 URL。反向关系需要明确链接，平台不会代替科研关系校验。

一次相关修改合并后，执行 maintain-research-state 的定向校验；外部文献按 literature-source-gate、正文按 academic-writing-editor。纯拼写/日期/只读请求不做结构审计。

正式交付直接给飞书链接及必要限制；outputs 仅保存完成清单和用户明确需要的导出。本机注册文件 `.agents/config/feishu-documents.json` 和 `.work/` 不公开分发。

官方依据：
- https://github.com/larksuite/cli
- https://github.com/larksuite/cli/blob/main/skills/lark-doc/references/lark-doc-xml.md
- https://github.com/larksuite/cli/blob/main/skills/lark-doc/references/lark-doc-fetch.md
- https://github.com/larksuite/cli/blob/main/skills/lark-doc/references/lark-doc-update.md
- https://www.feishu.cn/content/article/7623291503305083853

以上按 2026-10-13 的安装版本核对；网页 main 可能与安装版本不同，运行时帮助优先。
