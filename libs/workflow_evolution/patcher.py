"""Evolve one executable Workflow and its private learned resources."""

from __future__ import annotations

from libs.skill_evolution.patcher import SkillPatchEvolver


class WorkflowPatchEvolver(SkillPatchEvolver):
    """Evolve a Workflow entry point plus resources in its learned namespace."""

    ARTIFACT_PATH = "dynamic-task-solver.js"
    LEARNED_DIR = "dynamic-task-solver/learned"

    SYSTEM_PROMPT = """You evolve one executable Claude Code JavaScript Workflow
from completed trial evidence.

You may update the executable entry point `dynamic-task-solver.js` and create,
update, organize, or delete supporting material anywhere under the private
`dynamic-task-solver/learned/` directory. Do not write outside those locations
and do not delete the executable entry point.

Within the JavaScript entry point, choose any executable workflow graph,
length, number of agents, topology, prompts, phases, APIs, and recovery strategy
supported by the runtime and trial evidence. There is no two-to-three-agent
rule, line limit, or required linear executor/auditor chain. Return an empty
patch when the evidence does not justify a change.

Use the JavaScript file for executable orchestration. Use `learned/` for
reusable scripts, detailed references, examples, schemas, checklists, or other
learned resources. The Workflow itself cannot read files directly, so when a
learned file should affect execution, tell an appropriate child agent when and
how to inspect or run it with ordinary tools from
`~/.claude/workflows/dynamic-task-solver/learned/`.

Return exactly one JSON object with `summary`, `upsert_files`, and
`delete_paths`, without surrounding prose."""

    USER_PROMPT_TEMPLATE = """# Single executable-Workflow evolution task

Update the executable Workflow's entry point and private learning space:
- `dynamic-task-solver.js`
- `dynamic-task-solver/learned/**`

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

Infer evidence-backed changes to the executable Workflow and any supporting
learned files. Its graph, JavaScript source, learned-file count, and
learned-file types are unrestricted within its private namespace.

Return exactly this JSON shape and no surrounding prose:

```json
{{
  "summary": "brief evidence-based rationale",
  "upsert_files": {{
    "dynamic-task-solver.js": "complete executable JavaScript Workflow source",
    "dynamic-task-solver/learned/example.md": "reusable learned material"
  }},
  "delete_paths": ["dynamic-task-solver/learned/obsolete.md"]
}}
```
"""
