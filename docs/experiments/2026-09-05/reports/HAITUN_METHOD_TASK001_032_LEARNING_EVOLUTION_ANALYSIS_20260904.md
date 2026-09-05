# Haitun + Method task001–032 学习演化分析

更新时间：2026-09-04

## 1. 分析目标与口径

本文只分析 Method 的“题后学习”：每个 task 结束并得到 verifier 反馈后，学习器对该题族的 workflow 及相关 instruction、program、template 文件做了什么修改，以及这些修改代表它学到了什么。任务执行结果只作为学习触发证据，不展开重复完整功能点报告。

采用的记录口径如下：

| Task 范围 | 采用记录 | 模型 | 说明 |
|---|---|---|---|
| task001–005 | 2026-09-03 `simpleprompt` 最新批次 | Claude Opus 5 | Compensation 题族，严格串行 |
| task006–010 | 2026-09-01 Opus 5 正式批次 | Claude Opus 5 | Cross-Format 题族，严格串行 |
| task011–017 | 2026-09-03 `simpleprompt` 最新批次 | Claude Opus 5 | DMAIC 题族，覆盖 09-01 旧版本 |
| task018–020 | 2026-09-01 Opus 5 正式批次 | Claude Opus 5 | Distribution 题族，三题均通过并 no-op |
| task021–022 | 2026-08-31 历史正式批次 | DeepSeek V4 Flash | 本地没有更晚的 Opus 5 Method 记录；该链从冷启动开始，**不是 task018–020 的连续继承状态** |
| task023–027 | 2026-09-02 Opus 5 批次 | Claude Opus 5 | Document-Fraud 题族，严格串行 |
| task028–032 | 2026-09-04 最新批次 | Claude Opus 5 | Embedded-Data 题族，严格按难度顺序运行 |

因此，本文能覆盖 task001–032 的逐题记录，但不能把 task020→task021 当成同一个连续学习轨迹，也不应把 32 题合并成一个同模型总分。

## 2. 总体结论

- 32 次题后 patch 中，25 次实际更新文件，7 次选择 no-op；所有已提交 patch 均应用成功，`delete_paths` 为空，没有删除文件，也没有应用错误。
- 学习表现最好的题族是 Cross-Format 和 Document-Fraud：前者首题形成规则后连续四题保持不变并全过，后者建立“生产 + 独立复核”两步流程后五题全过。
- Embedded-Data 展示了最清晰的纠错链：task029 暴露“刷新所有缓存值”会污染非目标单元格，task031 又暴露“完全不写缓存值”会让目标结果为空；最终规则收敛为“只刷新 directive 指定区域，其他单元格保持字节/缓存状态不变”，task032 随后通过。
- Compensation 和 DMAIC 的 workflow/工具增长明显，但题级 reward 没有改善到 1。两者更多是在逐题吸收隐藏合同细节，尚未证明形成了稳定泛化能力。
- Compensation 的编排从 1 步扩张到 3 步，再扩张到 4 步；DMAIC 则始终保持单步，但把复杂性转移到 108 行 instruction 和 604 行检查程序中。说明“学习”既可能表现为增加 Step，也可能表现为单步提示词和工具膨胀。
- 学习器会从通过题中提炼规则，但不同题族策略不一致：Cross-Format/Distribution 在通过后倾向 no-op；Document-Fraud/Embedded-Data 即使通过也继续更新。这种差异来自 patch 模型对“通过轨迹中是否存在可复用新证据”的判断。

## 3. task001–005：Compensation Scenario Modeling

本题族所有题后更新都只修改：

`compensation-scenario-modeling/compensation-scenario-modeling.workflow`

没有新增外部脚本或模板。最终 workflow 为 27,482 bytes，形成 4 个 Step 和 3 个中间 Artifact：

`map_source_layout → map_authored_geometry → build_deliverable → verify_deliverable`

中间产物为 `source_layout_contract`、`authored_layout_blueprint`、`candidate_deliverable`。

### task001 — `02_orchestra_archive_refresh_model`，reward 0

- 文件变化：更新 workflow；把原先单一执行 Step 拆为 `map_source_layout → build_deliverable → verify_deliverable` 三步，新增 `source_layout_contract` 和 `candidate_deliverable`。
- 学到的内容：迁移/保留任务应先固定 sheet 顺序、绝对锚点、文字字面值、源到目标的偏移和 defined name 引用；不能重排或重新设计布局；要检查命名范围的 off-by-one；保存后重新读取关键区域；不能声称运行了实际未运行的 verifier。
- 触发证据：输出把源工作簿重新设计成紧凑布局，导致标题、Roster 锚点、EE Calcs 表头和 defined names 全部偏移。
- 评价：学到了“先建立布局合同再构建”的正确方向，但由一次失败直接增加两个阶段，编排复杂度显著上升，尚未在本题族得到整题通过验证。

### task002 — `03_university_faculty_model`，reward 0

- 文件变化：保持三步拓扑，只更新各 Step 的 contract/build/verify 指令。
- 学到的内容：把单元格分类为迁移字面值、计算后的静态数值、合同指定的实时公式；派生的工龄等字段必须写为原生 `int/float`；验证时必须检查 Python 类型和跨年度 `+1` 关系，而不是只检查标签和公式字符串。
- 触发证据：verifier 对工龄执行算术时遇到字符串，出现 `str + int` TypeError；代理的大量自检没有覆盖类型和跨 sheet 算术。
- 评价：定位准确，规则可复用，但只修复了一个隐藏类型合同；没有改变 workflow 结构。

### task003 — `04_university_termload_refresh_model`，reward 0

- 文件变化：保持三步拓扑，更新 workflow 指令。
- 学到的内容：默认采用源工作簿的 identity address mapping；优先复制源工作簿并原位编辑，禁止自行压缩布局；保留源数据类型；合计行必须覆盖所有数值列；禁止通过直接修改 XLSX XML 来补缓存值或改变数值文本表现；复核 Step 可用源工作簿推翻错误 contract。
- 触发证据：约 9,937 个自写断言全部通过，但因为自建紧凑布局，B1、C5、B26、row 79 和工龄列仍与 verifier 的绝对坐标合同不一致。
- 评价：认识到“检查数量多不等于合同正确”，这是重要学习；但仍未解决题族完整布局复现。

### task004 — `05_property_management_model`，reward 0

- 文件变化：保持三步拓扑，更新 workflow 指令。
- 学到的内容：规格声明的实体数应视为待验证断言；出现短数时重新扫描空行、尾部和其他标识符来源；所有 sheet 应由同一有序实体清单驱动；自建 Summary 必须填充顶部标题；平行年度 sheet 的属性列保持固定索引；数值类型只要求非布尔、非文本的 number，不强制 float。
- 触发证据：标题为空、Roster 85 人、计算表 86 人、verifier 要求 87 人，且工龄索引处被金额列替代。
- 评价：其中“统一实体清单”和“稳定列索引”合理；但把 87 人直接视为可从材料重新扫描得到并不稳健，因为后来确认材料实际只有 85 人。这条学习有被隐藏 verifier 反向过拟合、甚至诱导补造记录的风险。

### task005 — `06_property_portfolio_refresh_model`，reward 0

- 文件变化：在原三步前增加 `map_authored_geometry`，形成最终四步；新增 `authored_layout_blueprint` Artifact。
- 学到的内容：不能把“不会输出的 context-only sheet”等同于“无需读取”；Packet Notes 等辅助 sheet 可能是标题、绝对行号和额外标识符的 oracle；为自建 sheet 建立候选 oracle 优先级；汇总所有标识符块；迁移属性列采用 identity mapping；Summary 公式行固定到来源暗示的绝对位置。
- 触发证据：B1 标题为空、Summary 公式块被压缩到 6–13 行而 verifier 检查 row 33、Roster 仍为 85、工龄列索引仍错。
- 评价：学习器用新增 Step 解决“自建 sheet 没有直接源模板”的问题，但本题仍为 0，且“辅助 sheet 必然含额外人员”的假设没有得到后续验证。Compensation 最终形成较重的四阶段流程，却没有题级成功证据。

## 4. task006–010：Cross-Format Data Reconciliation

本题族始终保持单一 `execute_task` Step，仅使用：

`skillflow-method/skillflow-method.workflow`

最终文件 3,247 bytes；task006 后由 1,591 bytes 增长到 3,247 bytes，task007–010 字节不再变化。

### task006 — `02-hospital-capacity-portfolio-diff`，reward 1

- 文件变化：更新 workflow，不改变 Step、Artifact、executor 和外部接口。
- 学到的内容：先把题目重述为数据合同清单，包括路径、精确 key/field、类型、排序、唯一性、粒度、模式和范围；完整枚举 PDF 页、表格、Excel sheet/字段/记录数；采用主解析与独立备用解析交叉核对；按来源做记录数守恒；通过独立路径重新推导交付物；明确区分“运行公开 tests”和“仅本地验证”。
- 评价：这是通过题驱动的正向归纳，后四题连续通过且无需再改，说明规则具有较强迁移效果。

### task007 — `03-retail-supply-category-diff`，reward 1

- 文件变化：no-op，workflow 字节不变。
- 学习判断：现有合同清单、完整枚举、双解析、类型/排序/唯一性/粒度和计数守恒已经覆盖新题；没有失败或近失误，不做推测性重写。
- 评价：合理 no-op；这是 task006 学习有效的第一条后继验证。

### task008 — `04-university-program-funding-diff`，reward 1

- 文件变化：no-op。
- 学习判断：现有方法再次覆盖 PDF + Excel 差异任务；缺少 verifier 的情况下诚实使用本地断言，不搜索依赖包测试。
- 评价：第二次稳定验证；usage 有缺失不影响题目和 patch 结论。

### task009 — `05-datacenter-hardware-registry-diff`，reward 1

- 文件变化：no-op。
- 学习判断：五页 PDF、工作簿和 125→121 的数量守恒均被现有规则覆盖；没有可归纳缺口。
- 评价：第三次稳定验证，支持“不要因为通过就强行增长 workflow”。

### task010 — `06-hospital-medication-reconciliation`，reward 1

- 文件变化：no-op。
- 学习判断：合同重述、全量枚举、双解析、类型与唯一性检查已足够；继续保持现状。
- 评价：Cross-Format 最终呈现“首题学习、四题验证”的理想学习曲线。

## 5. task011–017：DMAIC Quality Analysis

本节采用 09-03 最新 `simpleprompt` 链。七题均更新同一组文件：

- `dmaic-quality-analysis/dmaic-quality-analysis.workflow`
- `dmaic-quality-analysis/instructions/execute_task.md`
- `dmaic-quality-analysis/programs/check_literal_contract.py`

拓扑始终是单一 `execute_task` Step。最终 workflow 12,618 bytes，instruction 14,043 bytes / 108 行，检查器 27,785 bytes / 604 行。

### task011 — `harbor_hospital_lab_analyze_02`，reward 0

- 文件变化：保留单步；新增/更新独立 instruction，并新增通用 `check_literal_contract.py`。
- 学到的内容：先提取字面输出合同；题目中写的是裸文件名就逐字输出裸文件名；封闭列表中的 operational impacts 必须逐字复用，不能同义改写；固定字段与差异说明分离；检查 `/tests` 及其委托的 suite；提交前运行字面合同检查器。
- 评价：从单纯提示词进入“提示词 + 可执行验证程序”阶段，是 DMAIC 工具化的起点。

### task012 — `harbor_field_service_analyze_03`，reward 0

- 文件变化：更新上述三个文件；检查器新增 `non_empty_objects`、`required_any_keys`、`alias_keys`。
- 学到的内容：如果 instruction 只命名一个容器而未列出子键，应为每个窗口、过滤条件和计数生成描述性键，并同时提供常见别名，例如 `total_primary_records`；必须真实探测 `/tests`，不能用“不可见”放宽合同。
- 评价：开始针对隐藏 schema 生成防御性别名；覆盖面增加，但也开启了 schema 猜测和字段膨胀。

### task013 — `harbor_university_it_analyze_04`，reward 0

- 文件变化：更新上述三个文件；检查器新增 `scalar_keys`、`integer_keys`、`count_matches_list`。
- 学到的内容：复数/集合名若与标量统计并列，隐藏合同可能要求“数量”而非“值列表”；主键写整数 count，原始序列移到 `<key>_values` 或 `individual_values`。
- 触发证据：`imr_summary.points` 写成列表，verifier 要整数 35。
- 评价：字段 shape 推断更精细，但属于根据单个隐藏断言追加启发式，尚未形成题级成功。

### task014 — `harbor_gdpval_35`，reward 0

- 文件变化：更新上述三个文件；检查器加入统计过程族和别名组。
- 学到的内容：`include at least` 是最低集合；对 ANOVA、回归、t-test、控制图、过程能力等命名过程，输出完整常规统计量，并提供短名/长名别名，例如 `f_stat` 与 `f_statistic`。
- 触发证据：输出有 `f_statistic`，隐藏 verifier 检查 `anova_by_weekday.f_stat`。
- 评价：显著增强统计 schema 覆盖，但继续依赖“多发别名”应对未公开字段。

### task015 — `harbor_hospital_safety_01`，reward 0

- 文件变化：更新上述三个文件；检查器加入 series/rate 统计族、单位后缀、对象列表和跨容器相等检查。
- 学到的内容：按单位生成 `mean_min` 等别名；rate 容器同时输出分子/分母合计；每个过程容器提供 `rows` 等计数；排名必须是带字段名的对象列表；派生分析容器应回显顶层选中的过程指针。
- 评价：从单字段别名扩展到对象形状和跨容器一致性，但五个隐藏 key 失败仍说明 coverage 不足。

### task016 — `harbor_devops_pipeline_02`，reward 0

- 文件变化：更新上述三个文件；检查器新增 `string_keys`、对象项标签、顶层 key 引用和 slope/t-stat 别名族。
- 学到的内容：统计字段同时按指标名和单位限定，如 `mean_failure_rate`、`sample_std_sec`；趋势提供 `trend_slope_per_index`；rate totals 同时给全称和 head noun；排名和指针使用机器 key 而非展示标题；plan/approach/assessment/methodology 的主键可能要求长描述字符串，结构化细节移到 `<key>_detail`；30/60/90 要逐个展开字面短语。
- 评价：instruction 和 checker 继续快速膨胀，属于强力合同枚举，但 reward 仍为 0，显示新增规则没有及时转化为完整成功。

### task017 — `harbor_logistics_chain_03`，reward 0

- 文件变化：更新上述三个文件；检查器新增 `pair_list_keys`、`identifier_value_keys`、`object_child_keys`。
- 学到的内容：未枚举的类别默认使用小写 identifier；置信区间/范围除 low/high 外，还要提供按题目短语命名的二元素列表；instruction 中叙述的每个规则/阈值都应在 mandated container 中有 assessment/evaluation；名称包含 30/60/90 等分段时，计划键应为对象并包含 `day_30/day_60/day_90`。
- 评价：到 task017 已形成相当庞大的隐藏 schema 防御器，但七题 reward 仍为 0。该族的“学习”是真实发生的，却主要是逐题追补字段，泛化成功尚未得到验证；维护成本和过拟合风险都较高。

## 6. task018–022：Distribution Center Auditing

这里存在两个不连续实验链，必须分开理解。

### Opus 5 链：task018–020

该链从 1,591-byte 单步基线开始，三题都通过，三次 patch 全部 no-op，最终 workflow 与基线字节一致。

#### task018 — `harbor_trailer_detention_audit`，reward 1

- 文件变化：no-op。
- 学习判断：现有单步方法已能落实精确文件名、sheet、过滤、排序、总计行、具体值和 DOCX 内容约束，并在 `/tests` 不可见时使用补充自检。
- 评价：通过证明基线足够，没有证据支持增加规则。

#### task019 — `harbor_promo_register_audit`，reward 1

- 文件变化：no-op。
- 学习判断：同一基线再次完成分组、排序、总计和文档合同；不把本题特定表格规则写进通用 Method。
- 评价：合理 no-op。

#### task020 — `harbor_service_queue_sla_audit`，reward 1

- 文件变化：no-op。
- 学习判断：排除额外 sheet、读取规则阈值和输出具体值被视为任务显式合同，而非需要新增的通用方法。
- 评价：第三次通过，说明基线在该子集稳定。

### 历史 DeepSeek 冷启动链：task021–022

该链没有继承 task018–020 的 Opus 5 状态，最终 workflow 为 2,874 bytes；以下变化只能解释该历史链本身。

#### task021 — `harbor_timesheet_policy_audit`，reward 1

- 文件变化：更新 `skillflow-method/skillflow-method.workflow`，保持单步拓扑。
- 学到的内容：执行前枚举每个必需交付物及精确路径；缺失或损坏的交付物是验证失败；返回前逐个确认文件真实存在。
- 评价：通过题中提炼出“输出存在性门禁”，规则通用且简洁。

#### task022 — `harbor_returns_disposition_audit`，reward 0

- 文件变化：更新同一 workflow，保持单步拓扑。
- 学到的内容：开始和提交前各检查一次 `/tests`；读取 legacy wrapper 及其委托 suite；不可见 verifier 时从源数据独立重算每个派生指标/汇总；重新读取 DOCX，核对标识符和最低出现次数；准确报告实际验证范围。
- 评价：针对格式化数据、Summary 和 Word 内容失败做了合理补强，但该链到此结束，没有后继任务验证修正效果。

## 7. task023–027：Document Fraud Detection

本题族五题均 reward 1，但学习器持续从通过轨迹中外化可复用方法。最终形成：

- 两步 workflow：`Produce SkillFlow Deliverable → Independently Verify And Repair`
- 中间 Artifact：`draft_report`
- `templates/RECONCILIATION_PLAYBOOK.md`
- `templates/OUTPUT_CONTRACT_CHECKLIST.md`
- `templates/validate_contract.py`
- `templates/compare_json.py`
- `templates/README.md`
- `templates/CONVERSATION_CHANGES.md`

最终 workflow 15,833 bytes，六个模板/程序合计约 68 KB。

### task023 — `speaker-honorarium-review`，reward 1

- 文件变化：把薄单步执行器拆为“生产 + 独立复核”两步；新增 playbook、contract checklist、README、decision/change 记录和通用 JSON validator。
- 学到的内容：匹配时归一化但输出时逐字复制；0.85 模糊匹配兜底；多个原因命中时按列表中的第一个原因输出；金额容差 0.01；区分 null 与空字符串；保持 1-based 页码升序；对未标记记录也建立解释。
- 评价：第一次就把成功轨迹外化为工作流和工具，且后四题持续通过，说明该结构有效。

### task024 — `clinic-shift-claim-review`，reward 1

- 文件变化：保持两步；新增 `compare_json.py`；更新 workflow、所有文档模板和 validator。validator 增加 key-order、not-null、目录白名单等检查。
- 学到的内容：识别 PDF ref→crosswalk→authorization 的多跳链；区分“标签行缺失”和“标签存在但值无效”，决定 nullable verbatim 字段；理由清单是封闭集合，不能因为可疑但未列出的重复使用而新增 flag；独立复核应重建完整链并比较 JSON。
- 评价：学习从单表匹配扩展到多跳引用和封闭判定集合，仍保持通过。

### task025 — `field-service-workorder-audit`，reward 1

- 文件变化：更新 workflow 和五个文档模板；两个脚本无需修改。
- 学到的内容：身份集合是 canonical + alias/variant sheet 的并集；先过滤 base 状态，再应用最高版本且已批准的 revision，draft/pending 不生效且不能复活已过滤记录；复核器应使用与生产器不同的解析栈；报告文字错误与交付物错误分开处理；再次确认理由优先级抑制。
- 评价：脚本保持稳定，只补充策略；第三次通过显示两步复核和通用 validator 已足够。

### task026 — `fleet-maintenance-chargeback-audit`，reward 1

- 文件变化：更新 workflow 和五个文档模板；脚本不变。
- 学到的内容：支持按 group 嵌套的 JSON ledger，扁平化前后记录分组计数并检查跨组重复 ID；把 amendment 规则抽象为“审批列 + 版本列 + 修订值”的角色，而非固定字段名；PDF 页数用多种独立方式交叉验证；报告纠错数量由明细列表自动决定，避免前后自相矛盾。
- 评价：从具体字段名提升为数据角色抽象，是较好的泛化学习。

### task027 — `research-stipend-reconciliation`，reward 1

- 文件变化：更新 workflow 和五个文档模板；脚本不变。
- 学到的内容：先按首页/首行判定 scope，页码仍保持原始 1-based 索引；总页数应满足 out-of-scope + clean + flagged 守恒；多字段 override 必须全部来自同一 winning revision；同名字段必须绑定“表 + 角色”，不能只按列名理解；增加原始 PDF object walk 作为第三种独立读取方式。
- 评价：五题全过且规则逐步从具体案例抽象为 scope、overlay、role-bound schema 和独立解析，是本批次最成功的持续学习链之一。

## 8. task028–032：Embedded Data Repair

本题族始终保持单一 `execute_task` Step，所有任务只更新：

`embedded-data-repair/embedded-data-repair.workflow`

没有新增 supporting files。最终 workflow 9,196 bytes。

### task028 — `fx-cross-rate-inverse-fix`，reward 1

- 文件变化：更新 workflow，拓扑不变。
- 学到的内容：Office 文档是 ZIP package，应按 part 修改并保持其他 part 不变；指令可能位于 body XML 而非真正 notes part，要搜索所有载体；公式驱动结果应通过反解可写输入得到，尊重 rounding，不能硬编码公式结果；无 verifier 时重开公式和值、用可用引擎重算并对原包做 diff。
- 评价：成功提炼了 embedded repair 的核心方法，但“刷新缓存值”规则过宽，为 task029 埋下回归。

### task029 — `warehouse-slot-factor-refresh`，reward 0

- 文件变化：更新 workflow，撤销 blanket cache refresh。
- 学到的内容：非目标公式单元格的缓存状态也属于必须保持的内容；不能把缺失缓存变成新数值；headless recalculation 只能在一次性验证副本上运行，不能把结果回写原交付物；提交前同时按公式模式和 `data_only` 模式 diff，差异集合必须等于目标集合。
- 触发证据：非目标单元格 `(3,5)` 从 `None` 变成 `0.5`。
- 评价：这是明确的失败→规则修正；task030 随即通过，说明修正至少对下一题有效。

### task030 — `supplier-pack-matrix-refresh`，reward 1

- 文件变化：更新 workflow，拓扑不变。
- 学到的内容：载体可能含多个指令和多个 sheet，应选择 live/final 指令并忽略 archived/superseded；按 sheet label 而非索引定位；缓存状态要区分“没有 `<v>`”“空 `<v/>`”“有值 `<v>`”三种，不能归一化。
- 评价：验证了 task029 的范围控制，并把缓存保真进一步精细化。

### task031 — `catalyst-balance-matrix-sync`，reward 0

- 文件变化：更新 workflow，细化 target-region 缓存策略。
- 学到的内容：task029 的“保留空缓存”不能机械应用到目标区域；directive 指定的输入、direct result、reciprocal/dependent result 在 `data_only=True` 下都必须读到目标数值；可在临时重算副本中取得结果，只把目标区域对应 `<v>` 回写；区域外仍保持原状态；`calcPr fullCalcOnLoad` 不能替代评分器需要的存储值。
- 触发证据：公式正确但目标 direct rate 在 `data_only=True` 下为 `None`。
- 评价：修正了 task029 规则的另一极端，形成“目标区刷新、非目标区冻结”的更完整边界。

### task032 — `buffer-dilution-matrix-repair`，reward 1

- 文件变化：更新 workflow，拓扑不变。
- 学到的内容：目标单元格可能由 directive 中的 bracketed identifier 在行标题×列标题交点确定，转置交点保存 reciprocal；非目标 sheet 中即使存在过时、矛盾文字也不能顺手修复；completion summary 应记录匹配到的行列标签。
- 评价：在 task031 修正后通过，说明最终缓存边界策略和 matrix mapping 规则至少完成一次后继验证。该族最终 3/5，通过率不满，但学习链条最容易观察和解释。

## 9. 最终 workflow/相关文件状态

| 题族 | 最终拓扑 | 最终主要文件 | 学习状态判断 |
|---|---|---|---|
| Compensation | 4 Step，3 个中间 Artifact | 27,482-byte workflow | 学到了布局合同、几何和类型检查，但 0/5 reward；过重且未验证成功 |
| Cross-Format | 1 Step | 3,247-byte workflow | task006 后稳定，task007–010 no-op 且全过；学习成功 |
| DMAIC | 1 Step | 12,618-byte workflow + 14,043-byte instruction + 27,785-byte checker | 文件和规则大幅增长，仍 0/7 reward；学习发生但泛化未成功 |
| Distribution task018–020 | 1 Step | 1,591-byte baseline workflow | 三题全过、合理 no-op；无需学习 |
| Distribution task021–022 历史链 | 1 Step | 2,874-byte workflow | 学到交付物门禁与独立复核；task022 后无同链验证 |
| Document-Fraud | 2 Step，1 个中间 Artifact | 15,833-byte workflow + 6 个模板/程序 | 五题全过并持续抽象；学习成功，但文档规模较大 |
| Embedded-Data | 1 Step | 9,196-byte workflow | 3/5；缓存值和修改范围规则经历失败—修正—再验证，部分成功 |

## 10. 对“学到了什么”的综合判断

### 已得到后续任务验证的学习

1. Cross-Format 的合同清单、全量枚举、双解析和数量守恒：task006 后 task007–010 连续通过且无需再改。
2. Document-Fraud 的生产/独立复核双阶段、多跳关联、封闭理由集合、版本覆盖和独立解析：task023–027 连续通过。
3. Embedded-Data 的非目标缓存保真：task029 修正后 task030 通过。
4. Embedded-Data 的目标区域必须有 `data_only` 存储值：task031 修正后 task032 通过。

### 学到了规则，但尚未证明有效

1. Compensation 的四阶段布局合同和 authored geometry：五题均未整题通过，且最后新增的第四步没有后继验证。
2. DMAIC 的大量字段别名、shape 推断和 schema 检查器：能解释每次失败，但没有任何后继题达到 reward 1，仍可能只是逐题追补隐藏 key。
3. Distribution task022 后新增的 DOCX 读回和独立重算：该历史链没有后续任务验证。

### 可能需要回退或重审的学习

1. Compensation task004 把 instruction 的 87 人要求当成“材料里一定能重新扫描出的事实”，但已确认实际 roster 只有 85 人。这条规则可能促使代理编造缺失实体，应改成“以材料为主并记录冲突，不补造；如果 verifier 强制不一致数字，标记为评测合同问题”。
2. Compensation 的 Step 数从 1→3→4，但 reward 没改善，说明复杂编排没有带来可观察收益；后续应做消融，判断 `map_authored_geometry` 是否可以合并回 source contract。
3. DMAIC 的 helper 已达 604 行，却仍然不断追加隐藏字段别名。更稳妥的方向可能是让评分合同公开或让 verifier 返回 expected/actual，而不是继续无限扩充猜测性 schema。
4. Document-Fraud 在每个通过题后都更新多个模板，虽然结果很好，但应监控模板规模，避免成功轨迹也无限增长。

## 11. 证据来源

- task001–005：`HAITUN_METHOD_001_005_SIMPLEPROMPT_20260903_RAW/.../method_patch_history.jsonl`
- task006–010：`skillflow-haitun-method/reports/haitun-method-opus5-task006-010-20260901-1355/.../method_patch_history.jsonl`
- task011–017：`HAITUN_METHOD_011_017_SIMPLEPROMPT_20260903_RAW/.../method_patch_history.jsonl`
- task018–020：`skillflow-haitun-method/reports/audits/haitun-method-opus5-task011-020-20260901-1507/.../method_patch_history.jsonl`
- task021–022：`skillflow-haitun-method/reports/haitun-method-task021-030-maxtokens32768-20260831-064048/.../method_patch_history.jsonl`
- task023–027：`HAITUN_METHOD_OPUS5_PRE_MAIN65A8906_SELECTED17_FULL_20260902_RAW/.../Document-Fraud-Detection/method_patch_history.jsonl`
- task028–032：`HAITUN_METHOD_028_032_20260904/.../method_patch_history.jsonl`

逐题结论以 `method_patch_history.jsonl.summary` 为主，并用各题 `skill_evolution/{patch,changes,applied,outcome}.json`、最终 `shared_methods` 文件树和 verifier 结果交叉核对。本文没有把代理自述当作 verifier 事实，也没有把无效中断分支的 patch 混入有效学习链。
