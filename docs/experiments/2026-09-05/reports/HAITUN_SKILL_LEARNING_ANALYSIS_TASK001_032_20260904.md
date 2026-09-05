# Haitun + Skill 自学习情况分析（task001–032 范围）

> 逐题追踪 `SKILL.md` 与 `learned/` 相关文件的演化，以及每次验证后沉淀出的可复用知识。

- **实验分支：**仅 Haitun + Skill；不包含 Method 与 CC Workflow。
- **实际覆盖：**22 题，即 task001–005、task011–017、task023–032。
- **证据口径：**逐题 `patch.json`、`changes.json`、`applied.json`、`skill_patch_history.jsonl` 与最终 family Skill 状态。
- **范围说明：**“task001–032”是编号范围，不代表连续 32 题。本次近期实验没有运行 task006–010 与 task018–022，因此不为这些编号虚构学习记录。四个 family 分别维护自己的 Skill 状态，跨 family 不视为同一条连续学习链。

## 一、结论摘要

这 22 次迭代最明显的变化，是 Skill 从“经验性提醒”逐步演化为“可执行契约 + 自动检查脚本 + 失败纠正规则”。早期失败主要来自精确坐标、类型、键名和字面短语，而不是核心业务计算；随后每个失败都被转译成机器可检查的 gate。在 Document-Fraud-Detection 中，这套结构从第一题起连续 5/5 通过；在 Embedded-Data-Repair 中，前两题对缓存策略进行了正反纠偏，之后 3/3 通过。

| Family | 题数 | Reward 通过 | 学习主线 |
|---|---:|---:|---|
| Compensation-Scenario-Modeling | 5 | 0 / 5 | 从重建建议走向坐标、类型与记录数机器门禁 |
| DMAIC-Quality-Analysis | 7 | 0 / 7 | 从统计计算走向精确 JSON/Markdown 契约、会话生存与标识符纪律 |
| Document-Fraud-Detection | 5 | 5 / 5 | 形成稳定的多源对账框架，并连续扩展 crosswalk、revision、alias、状态门控 |
| Embedded-Data-Repair | 5 | 3 / 5 | 前两题纠正缓存策略，后三题实现 sheet/alias/decoy 迁移 |
| 合计 | 22 | 8 / 22 | 22 个 task patch 最终均成功写回对应 family 的 Skill 状态 |

## 二、最重要的学习模式

### 1. 失败会被转化成可执行门禁

典型路径是：评分失败 → 提炼精确契约 → 写入 `SKILL.md` 的决策规则 → 在 `learned/` 新建或更新 verifier、checklist、reference、template。最成熟的学习不只是文字总结，而是能在下次提交前自动失败的脚本。

### 2. Skill 会纠正自己的过度泛化

task004 修正 task003 的整列/整行类型假设；task013 推翻 task012 对 `points` 形状的错误推断；task014 删除近似 I-MR 常数；task029 纠正 task028 的“所有公式都补缓存”。这说明学习链不是单向累加，而是会基于后续证据覆盖旧规则。

### 3. 通过题主要带来泛化，失败题主要暴露边界

Document-Fraud-Detection 的五次通过不断扩展同一对账框架：crosswalk、revision、alias、JSON flatten、生命周期门控、非记录页、次级属性 override。Embedded-Data-Repair 的后三次通过则把正确缓存策略迁移到 sheet 解析、alias token 和 decoy/final 选择。

## 3、逐题学习：Compensation-Scenario-Modeling

5 题均未通过，但依次建立了工作簿重建、值类型、评分锚点、动态范围与 Summary/roster 契约。这个 family 的主要成果是把模糊的建模建议变成逐格检查器。

### task001 · 02_orchestra_archive_refresh_model（Reward 0，未通过）

**它学到了什么：**从一次标签抄写错误扩展出完整的工作簿重建纪律：迁移文本必须逐字复制；损坏的 #REF! 定义名称要重新指向并补齐年度 token 系列；不能只凭人工检查就宣布完成，必须发现并运行落盘测试或等价自检。

**`SKILL.md` 的变化：**SKILL.md 新增“源文本逐字迁移、定义名称修复、提交前验证”主流程，并把详细操作下沉到参考与脚本。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 新建 `skillflow-skill/learned/workbook-rebuild.md`
- 新建 `skillflow-skill/learned/verify_workbook.py`

### task002 · 03_university_faculty_model（Reward 0，未通过）

**它学到了什么：**学会区分“公式字符串”和“评分器按数值读取的单元格”。openpyxl 写入公式后没有缓存值，data_only 读取可能得到文本或空值；因此要为每个受检单元格明确 literal/formula/progression 类型契约。同时记录环境中应使用 python3。

**`SKILL.md` 的变化：**SKILL.md 增加值类型决策表、迟挂载评分器假设与数值进阶检查，避免把公式写进评分器要求数字的格子。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 新建 `skillflow-skill/learned/check_value_types.py`
- 新建 `skillflow-skill/learned/grader-contract.md`

### task003 · 04_university_termload_refresh_model（Reward 0，未通过）

**它学到了什么：**确认“来源布局”不等于“评分锚点布局”：标题、驱动值和总计可能被固定检查在特定坐标；只填自己认为有意义的列会留下空洞，受检区域应按完整矩形覆盖。

**`SKILL.md` 的变化：**SKILL.md 加入 graded anchors 优先、矩形完整性和分阶段 gate；把已知坐标契约与可执行布局检查拆成专门文件。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 新建 `skillflow-skill/learned/graded-anchor-contract.md`
- 新建 `skillflow-skill/learned/check_layout.py`

### task004 · 05_property_management_model（Reward 0，未通过）

**它学到了什么：**纠正 task003 后形成的过度泛化：同一驱动行里 C5 可以是字面值，而 D5 必须是相对公式；类型契约应落到单元格而非整列。检查范围也不能硬编码，应从表头、数据末行和 totals 行动态发现。

**`SKILL.md` 的变化：**SKILL.md 改写为逐单元格类型契约；修订已有锚点参考中的错误说明，并新增自动发现服务年限列、数据范围和 Summary 驱动区的 gate。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 新建 `skillflow-skill/learned/gate_build.py`
- 更新 `skillflow-skill/learned/graded-anchor-contract.md`

### task005 · 06_property_portfolio_refresh_model（Reward 0，未通过）

**它学到了什么：**标题拼接不能随意删掉 population noun（如 Staff）；Summary 的受检块可能延伸到更深行并要求跨表公式；当评分器明确要求最少记录数时，不能机械坚持“只使用源表已有记录”的旧规则。

**`SKILL.md` 的变化：**SKILL.md 加入标题组成、深层 Summary 引用与记录数断言协调；用新参考文件明确纠正旧的“不补记录”建议。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 新建 `skillflow-skill/learned/summary-roster-contract.md`
- 新建 `skillflow-skill/learned/check_graded_contract.py`

## 4、逐题学习：DMAIC-Quality-Analysis

7 题均未通过；失败集中在隐藏输出契约、精确数值路径、产物落盘和标识符一致性。学习密度最高，形成了 reference、template、checklist 与 verifier 四层结构。

### task011 · harbor_hospital_lab_analyze_02（Reward 0，未通过）

**它学到了什么：**统计结果本身正确仍会因输出契约失分：source_file 要写裸文件名，要求的运营影响短语要逐字出现。核心学习从“分析方法”转向“先提取字面输出契约，再机器自检”。

**`SKILL.md` 的变化：**SKILL.md 增加 contract-first、裸文件名、原文短语和提交前契约检查；同时沉淀正确的 DMAIC/I-MR 计算约定。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 新建 `skillflow-skill/learned/scripts/verify_contract.py`
- 新建 `skillflow-skill/learned/checklists/output-contract-checklist.md`
- 新建 `skillflow-skill/learned/references/dmaic-analysis-conventions.md`

### task012 · harbor_field_service_analyze_03（Reward 0，未通过）

**它学到了什么：**不能自创 JSON 键名；record_counts 的精确字段名属于评分契约。若测试文件可见，应在写产物前直接读取并执行，而不是推断 schema。

**`SKILL.md` 的变化：**SKILL.md 把读取评分测试提升为 step 0，并禁止擅造 key；新建 Harbor DMAIC JSON 契约参考，强化输出检查清单。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 新建 `skillflow-skill/learned/references/harbor-dmaic-json-contract.md`
- 更新 `skillflow-skill/learned/checklists/output-contract-checklist.md`

### task013 · harbor_university_it_analyze_04（Reward 0，未通过）

**它学到了什么：**用实证推翻上一题的错误推断：imr_summary.points 是整数计数，不是数值序列；同时确认测试可能只在评分时挂载，运行期找不到测试不等于没有隐藏契约。

**`SKILL.md` 的变化：**SKILL.md 新增值形状判断和隐藏评分器现实；修正 JSON 契约与分析约定，新增可复用分析模板，并删除不具运行价值的实验元说明。

**相关文件变化：**

- 删除 `skillflow-skill/learned/CONVERSATION_CHANGES.md`
- 更新 `skillflow-skill/SKILL.md`
- 更新 `skillflow-skill/learned/references/harbor-dmaic-json-contract.md`
- 更新 `skillflow-skill/learned/references/dmaic-analysis-conventions.md`
- 新建 `skillflow-skill/learned/scripts/dmaic_analyze_template.py`
- 更新 `skillflow-skill/learned/checklists/output-contract-checklist.md`

### task014 · harbor_gdpval_35（Reward 0，未通过）

**它学到了什么：**纠正 I-MR 上控制限公式：不能用 2.66×MRbar 的近似捷径，应按 grader 路径使用 CL + 3×(MRbar/1.128)，并把绝对误差容限纳入设计。还学会处理多 sheet、尾随空格列名、Unnamed 列和拼写异常。

**`SKILL.md` 的变化：**SKILL.md 删除近似常数路径并规定 canonical constants；更新分析模板和检查清单，新增常数参考、契约补充与独立 UCL 复算脚本。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 新建 `skillflow-skill/learned/references/control-chart-constants.md`
- 新建 `skillflow-skill/learned/references/harbor-dmaic-contract-addendum.md`
- 更新 `skillflow-skill/learned/references/dmaic-analysis-conventions.md`
- 更新 `skillflow-skill/learned/scripts/dmaic_analyze_template.py`
- 新建 `skillflow-skill/learned/scripts/check_imr_limits.py`
- 更新 `skillflow-skill/learned/checklists/output-contract-checklist.md`

### task015 · harbor_hospital_safety_01（Reward 0，未通过）

**它学到了什么：**失败并非统计错误，而是长时间探索后工具调用中断，最终没有任何交付文件。由此形成 artifact-first：先在精确路径写入可恢复的占位产物，每一步及时落盘；避免超大单次命令和整表倾倒。

**`SKILL.md` 的变化：**SKILL.md 把产物先行与会话生存规则放到主流程前部；新增占位产物引导脚本、多过程安全分析契约、分析模板和会话检查清单。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 新建 `skillflow-skill/learned/scripts/bootstrap_deliverables.py`
- 新建 `skillflow-skill/learned/references/harbor-multiprocess-safety-contract.md`
- 新建 `skillflow-skill/learned/scripts/multi_process_analyze_template.py`
- 新建 `skillflow-skill/learned/checklists/session-survival-checklist.md`

### task016 · harbor_devops_pipeline_02（Reward 0，未通过）

**它学到了什么：**产物存在且统计正确仍会被定性 schema 拒绝：每过程块需要精确别名，改进计划要有 30/60/90 日层级，Markdown 要含评分器匹配的字面短语。另记录本地 inspect.py 会遮蔽标准库并破坏 pandas 导入。

**`SKILL.md` 的变化：**SKILL.md 增加 narrative contract、标题/短语正则、per-process alias superset 和标准库遮蔽检查；新增专门契约、校验脚本和清单。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 新建 `skillflow-skill/learned/references/harbor-devops-pipeline-contract.md`
- 新建 `skillflow-skill/learned/scripts/check_narrative_contract.py`
- 新建 `skillflow-skill/learned/checklists/narrative-and-markdown-checklist.md`

### task017 · harbor_logistics_chain_03（Reward 0，未通过）

**它学到了什么：**统计再次不是主因，真正问题是标识符、枚举大小写和跨块一致性：展示名不能替代 snake_case id，severity 必须是小写枚举，最高波动过程要在多个块中保持同一 id；还要覆盖单位后缀和 Wilson 区间别名。

**`SKILL.md` 的变化：**SKILL.md 增加 identifier/enum 阶段和 alias families；新增物流链契约、标识符检查清单与机器审计脚本。该 patch 最终在第 2 次尝试成功。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 新建 `skillflow-skill/learned/references/harbor-logistics-chain-contract.md`
- 新建 `skillflow-skill/learned/checklists/identifier-and-enum-checklist.md`
- 新建 `skillflow-skill/learned/scripts/check_identifier_contract.py`

## 5、逐题学习：Document-Fraud-Detection

5 题全部通过。Skill 从单层 PDF/CSV/Excel 对账，扩展到多跳 crosswalk、修订表、别名表、嵌套 JSON、状态门控与非记录页过滤。

### task023 · speaker-honorarium-review（Reward 1，通过）

**它学到了什么：**形成一套通过验证的跨文档对账方法：先完整盘点与解析所有来源；标准化姓名并用约 0.85 的相似度阈值容忍头衔、标点和轻微拼写差异；金额按 0.01 容差比较；每条记录只保留首个命中原因并按页排序；最终从磁盘重读 JSON 验证。

**`SKILL.md` 的变化：**SKILL.md 写入常驻对账流程与路由；新增详细 playbook 和参数化脚本模板。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 新建 `skillflow-skill/learned/cross-document-reconciliation.md`
- 新建 `skillflow-skill/learned/scripts/reconcile_template.py`

### task024 · clinic-shift-claim-review（Reward 1，通过）

**它学到了什么：**新增多跳连接：文档中的外部代码先经 crosswalk 映射到内部授权，再连接金额与人员；无法映射应判 invalid-code，而不是金额或归属问题。重复授权码本身不是异常，必须结合 owner 判断。

**`SKILL.md` 的变化：**SKILL.md 增加 crosswalk hop 和不臆造 duplicate rule；扩展对账参考与模板，支持可选 crosswalk、token 排序标准化和理由词表检查；删除实验元说明。

**相关文件变化：**

- 删除 `skillflow-skill/learned/CONVERSATION_CHANGES.md`
- 更新 `skillflow-skill/SKILL.md`
- 更新 `skillflow-skill/learned/cross-document-reconciliation.md`
- 更新 `skillflow-skill/learned/scripts/reconcile_template.py`

### task025 · field-service-workorder-audit（Reward 1，通过）

**它学到了什么：**识别两种新来源结构：实体工作簿的 aliases sheet 要加入匹配候选；额外 CSV 可能是 revision/amendment 表而非 crosswalk，预期金额应取最高版本且 approved 的记录，draft 要忽略；closed 状态属于无效工单。

**`SKILL.md` 的变化：**SKILL.md 增加“按列结构分类附加参考文件”、approved revision 解析、状态门控和枚举所有 worksheet 的规则。注意：patch 摘要称会泛化参考与模板，但实际落盘 changes.json/applied.json 只更新了 SKILL.md，因此本报告按实际变更记载。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`

### task026 · fleet-maintenance-chargeback-audit（Reward 1，通过）

**它学到了什么：**扩展到嵌套 JSON 授权：先 flatten depots→orders，再只接受 approved 生命周期；多行 amendment 只取 decision=approved 中最高 amendment_no；实体名标准化还要剥离 co/inc/ltd/llc/corp 等公司后缀。

**`SKILL.md` 的变化：**SKILL.md、对账 playbook 和脚本模板共同扩展，支持 JSON authority、状态门控、alias sheet 与多版本修订，同时保留既有理由优先级。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 更新 `skillflow-skill/learned/cross-document-reconciliation.md`
- 更新 `skillflow-skill/learned/scripts/reconcile_template.py`

### task027 · research-stipend-reconciliation（Reward 1，通过）

**它学到了什么：**PDF 页数不等于记录数，需先以页首标题筛掉说明页；修订表可以覆盖金额以外的任意次级属性，如 campus_code；被 rejected 的修订必须忽略。再次确认基础 authority 的 archived 状态应优先判 Invalid Ref。

**`SKILL.md` 的变化：**SKILL.md 增加 record-scoping、任意字段 override 与显式理由优先级；更新 playbook 的逐页判定表，并把模板泛化为可配置的次级属性比较。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 更新 `skillflow-skill/learned/cross-document-reconciliation.md`
- 更新 `skillflow-skill/learned/scripts/reconcile_template.py`

## 6、逐题学习：Embedded-Data-Repair

前两题失败并完成缓存规则的正反纠偏，后三题连续通过。最终形成“先解析容器与真实 sheet，再限定 allowed-change-set，最后按 grader 读取方式验证”的稳定流程。

### task028 · fx-cross-rate-inverse-fix（Reward 0，未通过）

**它学到了什么：**首次确认嵌入工作簿的缓存值也是交付内容：公式逻辑与 fullCalcOnLoad 正确仍不够，data_only=True 若读不到 <v> 就会失败。容器重打包还必须保留 entry 顺序、压缩类型和 external_attr；没有 unzip 时用 Python zipfile。

**`SKILL.md` 的变化：**SKILL.md 增加 grader-read-mode 验证与公式缓存要求；新增嵌入数据修复 playbook、同时写 <f>/<v> 的补丁脚本和缓存检查器；删除实验元说明。

**相关文件变化：**

- 删除 `skillflow-skill/learned/CONVERSATION_CHANGES.md`
- 更新 `skillflow-skill/SKILL.md`
- 新建 `skillflow-skill/learned/embedded-data-repair.md`
- 新建 `skillflow-skill/learned/scripts/patch_embedded_xlsx.py`
- 新建 `skillflow-skill/learned/scripts/check_embedded_workbook.py`

### task029 · warehouse-slot-factor-refresh（Reward 0，未通过）

**它学到了什么：**反向纠正 task028 的过度学习：不能给所有公式补缓存。评分器要求除允许变更集合外的 data_only 值逐格不变，原本为空的缓存也必须保持空；只为明确受检单元格写缓存。

**`SKILL.md` 的变化：**SKILL.md 和修复 playbook 把 blanket cache 改为 scoped cache；重写缓存检查器，并新增 input/output 差分门禁以捕捉 collateral changes。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 更新 `skillflow-skill/learned/embedded-data-repair.md`
- 新建 `skillflow-skill/learned/scripts/check_no_collateral_change.py`
- 更新 `skillflow-skill/learned/scripts/check_embedded_workbook.py`

### task030 · supplier-pack-matrix-refresh（Reward 1，通过）

**它学到了什么：**目标矩阵可能位于第二个 worksheet，首个 sheet 是带“不要编辑”文字的 decoy；不能默认修改 sheet1.xml，必须通过 workbook.xml 与关系文件把 sheet 名解析到真实 part。测试不可见时，要从题面与族 invariant 重建契约，并先定位 /root 输入。

**`SKILL.md` 的变化：**SKILL.md 强制 sheet-part resolution、显式 sheet 参数、无测试文件 fallback 与输入 staging；新增 sheet/contract discovery 参考和 part 解析器。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 新建 `skillflow-skill/learned/sheet-and-contract-discovery.md`
- 新建 `skillflow-skill/learned/scripts/resolve_sheet_part.py`

### task031 · catalyst-balance-matrix-sync（Reward 1，通过）

**它学到了什么：**题面短 token 可能要经 sibling alias CSV 才能映射到工作簿标签；目标算术已正确但缺缓存时应做 cache-only 最小编辑。矩阵方向应由角落表头决定，不能靠习惯；矩阵内部也可能并不全局自洽，不能用过强一致性门禁。

**`SKILL.md` 的变化：**SKILL.md 增加 alias 解析、cache-only edit shape、方向与 decoy 规则；新增 token/alias 参考和标签别名解析脚本。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 新建 `skillflow-skill/learned/token-alias-and-cache-only-edits.md`
- 新建 `skillflow-skill/learned/scripts/resolve_label_aliases.py`

### task032 · buffer-dilution-matrix-repair（Reward 1，通过）

**它学到了什么：**题面可能同时出现 DRAFT 与 FINAL 比率，目标选择必须显式遵循最终批准值；decoy Summary sheet 也可能包含搜索 token，token 命中要限制在已解析的矩阵 sheet。空缓存冻结规则只适用于允许变更集合之外；缺少 alias 表是正常分支。

**`SKILL.md` 的变化：**SKILL.md 写入 final-over-draft、matrix-sheet filtering、allowed-change-set 与 optional-alias 规则；新增 decoy/superseded values 参考。

**相关文件变化：**

- 更新 `skillflow-skill/SKILL.md`
- 新建 `skillflow-skill/learned/decoy-and-superseded-values.md`

## 七、最终形成的 family 级知识资产

| Family | 最终知识资产 |
|---|---|
| Compensation-Scenario-Modeling | 工作簿重建说明；grader/anchor/summary-roster 契约；值类型、布局、动态构建和总契约检查脚本。 |
| DMAIC-Quality-Analysis | 输出/会话/叙事/标识符四类清单；DMAIC、I-MR、Harbor JSON、多过程与具体任务契约；分析模板、产物 bootstrap 和多类校验脚本。 |
| Document-Fraud-Detection | 一份持续更新的跨文档对账 playbook，以及支持 crosswalk、alias、revision、状态门控、页面过滤和次级属性 override 的模板脚本。 |
| Embedded-Data-Repair | 嵌入工作簿修复、sheet/contract discovery、token alias/cache-only、decoy/final 选择四份参考；容器补丁、缓存检查、无旁路变更、sheet part 与 alias 解析脚本。 |

## 八、评估与后续建议

**有效之处：**每次 task 后都有成功落盘的 Skill patch；关键失败几乎都被具体化为新规则或检查器。尤其是 task023–027 的连续通过和 task030–032 的连续通过，说明同 family 内存在可观察的正迁移。

**主要风险：**失败证据有时会诱发过度泛化，必须允许后续 task 覆盖旧规则；task025 还表明 patch 的自然语言 summary 可能比实际 applied 变更更乐观，因此评估学习情况应以 `changes.json`/`applied.json` 为准。

**建议的下一步：**继续保留逐题的 before/after Skill 快照，并为每条新规则记录“来源 task、支持证据、反例、适用 family、对应检查脚本”。对已被纠正的规则加 superseded 标记，避免旧参考继续误导后续 agent。

## 九、证据来源

1. `local-archive/06_本地原始运行/01_Skill/HAITUN_SKILL_OPUS5_SELECTED_FINAL_20260902_1335`
2. `local-archive/06_本地原始运行/01_Skill/HAITUN_SKILL_OPUS5_TASK028_032_FINAL_20260904`

逐题事实优先级：`applied.json` / `changes.json`（实际文件操作）→ `patch.json` summary（学习解释）→ `result.json` 与 verifier 输出（成败背景）→ `family_state`（最终累计状态）。
