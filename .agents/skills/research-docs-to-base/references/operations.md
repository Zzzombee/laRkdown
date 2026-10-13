# 官方 CLI 与恢复

核验日期 2026-10-13，本机 CLI 1.0.97。[官方 CLI](https://github.com/larksuite/cli)、[Base 技能](https://github.com/larksuite/cli/blob/main/skills/lark-base/SKILL.md)、[字段 schema](https://github.com/larksuite/cli/blob/main/skills/lark-base/references/lark-base-field-schema.md)、[读取与分页 SOP](https://github.com/larksuite/cli/blob/main/skills/lark-base/references/lark-base-record-query-and-analysis-sop.md)。后续版本参数改变时按本机官方帮助修复，不退回猜测 REST API。

脚本复用 laRkdown 的 `feishu_bridge.py` 作为官方 CLI 启动器，Windows 直接执行 npm 的 Node runner，JSON 不经过 shell 插值。保留用户身份和当前认证，不自动重新授权。权限不足按实际缺失 scope 提示用户本人授权，不打印密钥。

`extract`/`preview` 可在无目标时运行；没有 Base 时 preview 仅显示待构建数据量。`init` 必须对应用户构建/绑定指令，先完整读取三文档，失败不创建知识库多维表格。新建使用 `+base-create` 自定义首表；复制母版使用 `+base-copy --without-content`。保存真实返回 token/URL；如果初始化已登记研究 Wiki 空间，用官方 `wiki +move --obj-type bitable --obj-token 实际BaseToken --target-space-id 实际SpaceID` 将新 Base 迁入该空间，再用 `wiki +node-get` 核对空间、节点与底层 Base token。移动结果不明时已设置一次性闩锁，后续只查询实际节点，不再次发起移动；异步任务按官方返回的 task_id 查证。用户绑定的已有 Base 不自动移动。随后补齐其它表和字段，复制地址与目标地址必须不同。已有 schema 不改类型、不删字段、不改原有视图/权限。六表补齐后用 `+view-list` 定位视图、`+view-set-visible-fields` 只展示阅读字段；新 Base 使用新建的网格视图，已有 Base 或模板副本另建“科研阅读”网格视图并保留其旧视图。设置结果和 view ID 写入本机配置；中断后先检查已建视图，不能重复创建同名视图。技术同步字段保持存在但在阅读视图隐藏。

`+record-list --format ndjson --output ... --limit 2000` stdout 是 manifest，**没有常规 ok 包装**。逐行数据是字段名称映射加 record_id。读取下一页必须采用 next_offset；页间 rev/query_context 不一致、重复 record_id、记录计数不符或未到 has_more=false 都失败，禁止进行归档。未指定 view/filter，整表读完。

`+record-upsert --json 字段映射`：无 record-id 是创建，有则更新，不自动按编号匹配。只写本技能管理字段；不批量覆盖整行。写前校验已有管理字段相对本机成功日志未被修改，并再次核对源版本。AI 扩展、formula/lookup/system 等不作为普通可写字段；链接值只能是真实目标 Record ID。保存每次 write-ahead 日志，回读确认字段和归档状态后才推进基线。未知 warnings/ignored_fields 停止并保留日志。

## 恢复

- `.work/research-base/state.json` 保存已验证记录的基线；`pending.json` 保存尚未验证操作。失败不清除 pending、不重复创建。
- `recover` 只读目标整表，按同步项目+同步键查证唯一记录，并比较 pending 的字段。完全一致才将该操作记为成功并清除 pending；不存在、重复或内容不一致则停止，交付查证结果，让用户决定修复路径。然后重新 preview/sync，只补未完成部分。
- `init-pending.json` 阻止结果不明的 Base 创建重试。若实际返回丢失，使用官方标题检索或用户实际链接找到已创建资源，再用 `init --base-url 实际链接` 绑定；不得删掉 guard 后重新建。表/字段中断后重新列举再补缺失即可。
- 新 Base 迁入 Wiki 时若进程中断，查看本机配置的 `wiki_space_id`、`wiki_move_attempted_at` 与可选的 `wiki_move_task_id`，用 `wiki +node-get --node-token 实际BaseToken` 查证，异步任务使用官方 `drive +task_result --scenario wiki_move`；不重复调用 `wiki +move`。核实成功后继续 `init`，它会回读节点并补齐六表。
- 进程异常退出后若残留 `run.lock`，先核对其中 PID 是否仍在运行；确认无同步进程后仅清理该锁文件，保留 pending 和成功基线。
- 已管理行被人工修改时脚本停止；先让用户明确保留哪一侧，然后将认可内容更新到**源文档**或专门迁移基线。备注等非管理字段不触发这种冲突。
- 本地锁阻止同一工作根目录并发；CLI 没有记录级 compare-and-swap，不能保证跨电脑同时修改的原子性。实际同步时避免同事同时改管理字段，错误报告不能声称具备分布式事务。

结束时再次读取来源版本；若写入期间来源变动，保留已验证基线并报告需要同步最新版本，不交付过时的成功报告。同步完成报告包含真实 Base URL、三文档来源版本、每表新增/更新/归档/未变数量、未解析关系和媒体仅保留定位的边界。首次部署还需在豆包客户端验证技能可选/可加载；Python 测试通过不等于豆包平台已导入。
