# Haitun Method task033–037 详细结果

## 实验信息

- 方法：Method-only 自学习；未运行 Skill 或 Dynamic Workflow。
- 模型：`claude-opus-5`，provider 为 `anthropic`，reasoning effort 为 `none`。
- 执行方式：同一题族内按官方难度严格串行。
- 实际顺序：task033 → task034 → task037 → task035 → task036。
- 单题超时：3600 秒。
- 服务器运行目录：`jobs/haitun-method-opus5-task033-037-simpleprompt-20260904-022651`
- 本地原始数据：`local-archive/HAITUN_METHOD_033_037_20260904_RAW`
- 原始数据规模：162 个文件，1,861,012 字节。

## 总体结果

- 完成：5/5。
- reward：0/5 通过，五题均为 `0.0`。
- 运行异常：0/5；所有 `exception_info` 均为 `null`，无环境启动超时、凭据失效或模型接口错误。
- verifier 可见检查点合计：10 对、5 错。
- 每题均先通过“输出工作簿存在”和“工作表名称及顺序正确”两项，随后在第一个明细表的 `A2` 标题精确匹配处失败。
- verifier 是 fail-fast：标题失败后，其余数据、公式、控制行等检查没有继续执行，因此不能把未执行项计为通过或失败。

## 每题明细

| 顺序 | 任务 | reward | 可见检查点 | 首个失败点 | 异常 | 时间（UTC） |
|---:|---|---:|---|---|---|---|
| 1 | task033 `cedar_accrual_rollforward` | 0.0 | 2 对 / 1 错 | `Payroll Accrual #2105!A2 title mismatch` | 无 | 02:27:13–02:33:43 |
| 2 | task034 `northstar_warranty_reserve_consolidation` | 0.0 | 2 对 / 1 错 | `Consumer Warranty #2440!A2 title mismatch` | 无 | 02:35:50–02:50:48 |
| 3 | task037 `solstice_commission_asset_alignment` | 0.0 | 2 对 / 1 错 | `Field Comm Asset #1510!A2 title mismatch` | 无 | 02:53:04–03:24:43 |
| 4 | task035 `orchid_project_cost_rollforward` | 0.0 | 2 对 / 1 错 | `Cap Impl #1460!A2 title mismatch` | 无 | 03:27:46–03:42:16 |
| 5 | task036 `peregrine_rebate_template_update` | 0.0 | 2 对 / 1 错 | `Channel Rebates #6120!A2 title mismatch` | 无 | 03:46:23–04:09:02 |

### task033

- 已通过：输出工作簿存在；工作表名称及顺序正确。
- 失败：`Payroll Accrual #2105!A2` 没有使用 verifier 期望的来源标题。
- 学习更新：把单一执行过程拆成来源调查、工作簿构建、独立审核三个步骤；要求为标题区建立逐单元格规格，并明确公式、最终有效行和真实验证状态。
- 学习补丁：已应用，`errors=[]`。

### task034

- 已通过：输出工作簿存在；工作表名称及顺序正确。
- 失败：`Consumer Warranty #2440!A2` 标题不匹配。
- 学习更新：要求完整读取路由/映射文件中的字符串字段，不只读取路由键；新增 `title_block_conventions.md`；扩大 verifier 路径探测范围。
- 学习补丁：已应用，`errors=[]`。

### task037

- 已通过：输出工作簿存在；工作表名称及顺序正确。
- 失败：`Field Comm Asset #1510!A2` 标题不匹配。
- 学习更新：新增带来源路径的完整字符串清单和确定性标题候选排序；新增只读工具 `programs/list_source_strings.py`；明确 fail-fast 前面的 PASS 不能证明后续检查通过。
- 学习补丁：已应用，`errors=[]`。

### task035

- 已通过：输出工作簿存在；工作表名称及顺序正确。
- 失败：`Cap Impl #1460!A2` 被写成工作表名，而材料中存在真实的日程/账户标题。
- 学习更新：把“工作表名可能可疑”提升为按账户编号匹配的硬规则；新增 `programs/check_title_provenance.py`，要求构建和审核都验证标题逐字来源；识别 `SystemExit: FAIL`、`INTERNALERROR`、`no tests ran` 的组合仍是实际内容失败。
- 该题调用模型 38 次：输入 966,845 tokens，其中缓存 727,158；输出 23,892 tokens。其余四题的结果文件未记录 token 统计，不能据此推断为零调用。
- 学习补丁：已应用，`errors=[]`。

### task036

- 已通过：输出工作簿存在；工作表名称及顺序正确。
- 失败：`Channel Rebates #6120!A2` 标题不匹配。
- 根因进一步明确：任务材料含模板工作簿，但此前两个标题检查工具只解析 JSON/CSV/文本，没有读取模板工作簿单元格；执行时重写工作表导致模板标题区丢失。
- 学习更新：字符串清单和标题来源检查工具现在逐单元格解析 `.xlsx/.xlsm/.xltx/.xltm`；模板同位置单元格成为最高优先级标题来源；清除数据仅允许从首个数据行向下，必须保留模板上方标题区；未读完所有来源格式前禁止断言“材料中没有标题”。
- 学习补丁：已应用，`errors=[]`。

## Workflow 最终状态

- 文件：`shared_methods/Financial-Statement-Rolling/financial-statement-rolling/financial-statement-rolling.workflow`
- 服务器最终更新时间：2026-09-04 04:13:27 UTC。
- 大小：18,405 字节。
- SHA-256：`5823b19e05466aee799e16174436b29356f5f4653102406afce0f2bf3459c4f1`
- 最终支持文件：
  - `instructions/survey_sources.md`
  - `instructions/build_workbook.md`
  - `instructions/audit_workbook.md`
  - `instructions/title_block_conventions.md`
  - `programs/list_source_strings.py`
  - `programs/check_title_provenance.py`

## 结论

这五题没有发生环境或接口故障，失败模式高度一致：产物存在、工作表结构正确，但第一个明细表 `A2` 没有逐字保留材料中的日程标题。学习器确实连续更新了 workflow，最终已经定位到更具体的工具覆盖缺口——模板工作簿没有被当作标题来源读取。最后形成的 workflow 已增加工作簿级字符串来源检查和模板标题区保护，但该改进是在 task036 评分后生成的，尚未通过同题重跑验证。
