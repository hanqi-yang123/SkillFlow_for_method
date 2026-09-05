# task001–032 最新有效数据

整理日期：2026-09-05  
口径：同一系统、同一任务选择日期最新且协议可接受的正式结果；有效重测和 corrected rerun 覆盖旧结果。仅改变 max_tokens、single-skill、等待参数、smoke、partial、超时批次和早期工作副本不混入正式主表，统一放在 `09_旧版与非标准实验/`。

## 当前覆盖结论

| 系统 | 有当前标准结果 | 明确缺口 |
|---|---:|---|
| Skill | 30 / 32 | task021–022 只有旧 DeepSeek 口径，已移入 `09` |
| Method | 30 / 32 | task021–022 只有旧 DeepSeek / max_tokens 口径，已移入 `09` |
| CC Dynamic Workflow | 31 / 32 | task022 只有旧的无效 Workflow 运行；task006–010、018–021 当前只有汇总数据；task017 有效重测的本地原始 trial 未返回 |

`TASK001_032_最新来源.csv` 是机器可读来源表。原始运行仍放在 `../06_本地原始运行/`，压缩证据放在 `../07_证据压缩包/`。

## Skill

| Tasks | 当前来源 |
|---|---|
| 001–005 | `06_本地原始运行/01_Skill/HAITUN_SKILL_OPUS5_SELECTED_FINAL_20260902_1335` |
| 006–010 | `06_本地原始运行/01_Skill/haitun-skill-opus5-task006-010-20260901` |
| 011–017 | `06_本地原始运行/01_Skill/HAITUN_SKILL_OPUS5_SELECTED_FINAL_20260902_1335` |
| 018–020 | `06_本地原始运行/01_Skill/haitun-skill-opus5-task018-020-20260901-nonthinking` |
| 021–022 | 当前标准数据缺失；旧 DeepSeek 数据在 `09` |
| 023–027 | `06_本地原始运行/01_Skill/HAITUN_SKILL_OPUS5_SELECTED_FINAL_20260902_1335` |
| 028–032 | `06_本地原始运行/01_Skill/HAITUN_SKILL_OPUS5_TASK028_032_FINAL_20260904` |

## Method

| Tasks | 当前来源 |
|---|---|
| 001–005 | `06_本地原始运行/02_Method/HAITUN_METHOD_001_005_SIMPLEPROMPT_20260903_RAW` |
| 006–010 | `06_本地原始运行/02_Method/haitun-method-opus5-task006-010-20260901-1355` |
| 011–017 | `06_本地原始运行/02_Method/HAITUN_METHOD_011_017_SIMPLEPROMPT_20260903_RAW` |
| 018–020 | `06_本地原始运行/02_Method/CURRENT_TASK018_020_FROM_METHOD_OPUS5_20260901` |
| 021–022 | 当前标准数据缺失；旧 DeepSeek / max_tokens 数据在 `09` |
| 023–027 | `06_本地原始运行/02_Method/CURRENT_TASK023_027_FROM_METHOD_SELECTED17_20260902` |
| 028–032 | `06_本地原始运行/02_Method/HAITUN_METHOD_028_032_20260904` |

## CC Dynamic Workflow

| Tasks | 当前来源 / 覆盖规则 |
|---|---|
| 001、004、014、016、031 | `06_本地原始运行/03_CC_Dynamic_Workflow/CC_DW_SELECTED_TASKS_WAIT0_RERUN_COMPLETE_20260905_EVIDENCE` |
| 002–003、005、011–013、015、023–027 | `06_本地原始运行/03_CC_Dynamic_Workflow/CURRENT_RETAINED_12_TASKS_FROM_CC_DW_COMPLETE_20260902` |
| 006–010 | `03_CC_仅有汇总的当前数据/CC_TASK006_010_CURRENT_SUMMARY.json` |
| 017 | `03_CC_仅有汇总的当前数据/CC_TASK017_VALID_RETEST_CURRENT_SUMMARY.json`；2026-09-04 有效重测 1/9，本地尚无该 trial 原始目录 |
| 018–020 | `03_CC_仅有汇总的当前数据/CC_TASK018_020_CURRENT_SUMMARY.json` |
| 021 | `03_CC_仅有汇总的当前数据/CC_TASK021_CURRENT_SUMMARY.json` |
| 022 | 当前标准数据缺失；旧运行的 Workflow 调用无效，已移入 `09` |
| 028–029 | `06_本地原始运行/03_CC_Dynamic_Workflow/CURRENT_TASK028_029_FROM_CC_DW_20260904` |
| 030、032 | `06_本地原始运行/03_CC_Dynamic_Workflow/CURRENT_TASK030_AND_032_FROM_CC_CORRECTED_20260904` |

## 关于 wait0

task001、004、014、016、031 的 wait0 结果是这些任务目前日期最新且运行有效的数据，因此被列为当前来源；同时它改变了等待上限，做跨系统“完全同配置”比较时仍应标注该变量。

## task033–037

task033–037 不在本次 task001–032 清理范围内，三路最新批次继续保留在 `06`、`07` 和 `05`。
