# PPTX 图片证据管线

仅用于指定实验 PPTX 的实际提取。以用户指定研究目录 ROOT 与本技能目录 SKILL 为基准；工作路径在 ROOT/.work/pptx/输入标识/，正式结果写入飞书原生文档。保留原文件，不要求用户先手工截图。

## 环境与结构

Python 3.11+、python-pptx 1.x、支持 TIFF 的 Pillow。原生整页渲染默认 Windows PowerShell + Microsoft PowerPoint；Python 结构提取可跨平台。云环境缺少渲染器时，须取得经过核验的整页渲染或由用户明确选择另一实现并验证；不得把结构提取成功当作视觉路径完成。

```text
python SKILL/scripts/preflight.py input.pptx --output ROOT/.work/pptx/输入标识/preflight.json
python SKILL/scripts/extract_pptx.py input.pptx --output ROOT/.work/pptx/输入标识/structure.json
python SKILL/scripts/prepare_media_preview.py input.pptx --output-dir ROOT/.work/pptx/输入标识/media
powershell -File SKILL/scripts/render_pptx.ps1 -InputPath input.pptx -OutputDir ROOT/.work/pptx/输入标识/slides
python SKILL/scripts/make_contact_sheet.py ROOT/.work/pptx/输入标识/slides --output-dir ROOT/.work/pptx/输入标识/contact-sheets
```

ROOT/SKILL 为说明性占位符，由 Agent 替换真实路径。preflight 返回 2 表示缺少默认 PowerPoint 渲染条件，不阻止可运行的结构提取，仍阻止未经核验的完整视觉录入。

structure.json 保留源 SHA-256、页码、形状路径、文字、备注、合并单元格和原生图表数值。media/manifest.json 保留每张原图 SHA-256、出现页码/形状、PNG 代理及多帧信息。代理用于查看；高位深/浮点/调色板转换记录显示映射，精确像素分析使用原图。

## 豆包实际视觉读取

先看 contact sheets 确认页覆盖，再实际打开每张证据页的整页 PNG；contact sheet 只用于定位。读轴、单位、图例、组别、样本标签、显著性标记、曲线/显微图及阴性结果。小字密集图再读取原图/局部裁图，裁图保留轴、图例和分组标记；禁止生成式补字或超分辨率补造科研细节。

通过当前客户端可用视觉工具显式加载每张图片，按信息量分批处理。官方模型文档指出缩放可能丢失小字，工作客户端的实际精度与图片加载方式仍需实测；不假设其暴露 API detail 参数。

为每张证据页记录实际读取文件、条件、直接观察、解释/假设、未知字段与来源。实际看图后由 Agent 写 visual-review.json：

```json
{"schema_version":1,"source_sha256":"实际输入SHA256","reviews":[{"slide":1,"evidence_bearing":true,"render":"slides/Slide1.PNG","inspected_files":["slides/Slide1.PNG"],"reader":"实际视觉工具名称","conditions":"已读条件与缺口","observations":"图上直接观察","interpretations":"作者解释或待验证解释","unreadable":[],"completed":true}]}
```

每页登记，非证据页标 evidence_bearing=false。示例不可当作已完成记录照抄。completed=true 仅在实际看图后填写；关键字段不可读时写 unreadable 并设 false。台账不证明实际执行过视觉工具，验收还须对照工具轨迹与抽查。

## 检查与交付

```text
python SKILL/scripts/validate_extraction.py --structure ROOT/.work/pptx/输入标识/structure.json --renders ROOT/.work/pptx/输入标识/slides --media-manifest ROOT/.work/pptx/输入标识/media/manifest.json --visual-review ROOT/.work/pptx/输入标识/visual-review.json --output ROOT/.work/pptx/输入标识/validation.json
```

检查源 hash、页覆盖、原图/代理完整性和视觉台账状态，不判断科学真伪或实际识图准确率。结构与视觉路径都完成才整理正式观察。原生精确数值、图上明确标签、视觉估读分开记录。

通过 feishu-workflow 的 XML img path 将必要实测图加入飞书；指向已提取真实图，不使用生成图替换。详细来源留在本地证据台账，用户要求时附入飞书。发布后回读确认文字与图片块，再交付链接。

官方模型限制：https://docs.volcengine.com/docs/ark/image-understanding?lang=zh（2026-10-13 核验；不等同于工作客户端实测）。
