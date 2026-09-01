"""Evolve exactly one executable Claude Code Workflow file."""

from __future__ import annotations

from libs.skill_evolution.patcher import SkillPatchEvolver


class WorkflowPatchEvolver(SkillPatchEvolver):
    """Allow evolution to change one JavaScript Workflow and nothing else."""

    ARTIFACT_PATH = "dynamic-task-solver.js"

    SYSTEM_PROMPT = """You evolve one executable Claude Code JavaScript Workflow
from completed trial evidence.

The only hard artifact restriction is the mutation boundary: `upsert_files` is
either empty or contains exactly `dynamic-task-solver.js`, and `delete_paths`
is empty. Do not create, update, rename, or delete any other file.

Within that JavaScript file, choose any executable workflow graph, length,
number of agents, topology, prompts, phases, APIs, and recovery strategy
supported by the runtime and trial evidence. There is no two-to-three-agent
rule, line limit, or required linear executor/auditor chain. Return an empty
patch when the evidence does not justify a change.

Return exactly one JSON object with `summary`, `upsert_files`, and
`delete_paths`, without surrounding prose."""

    USER_PROMPT_TEMPLATE = """# Single executable-Workflow evolution task

Update only `dynamic-task-solver.js`.

## Current artifact tree
{tree_json}

## Current artifact contents
{files_block}

## Trial evidence
- Task: {task_name}
- Family: {task_source}
- Verifier passed: {verifier_passed}
- Reward: {reward}
- Exception: {exception_info}
- Failed tests: {failed_tests}

## Final agent message
{final_message}

## Compacted execution trace
{trajectory_json}

Infer any evidence-backed changes to the executable Workflow. Its internal
graph and JavaScript source are unrestricted; only the output file boundary is
fixed.

Return exactly this JSON shape and no surrounding prose:

```json
{{
  "summary": "brief evidence-based rationale",
  "upsert_files": {{
    "dynamic-task-solver.js": "complete executable JavaScript Workflow source"
  }},
  "delete_paths": []
}}
```
"""
