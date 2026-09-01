"""Evolve one Haitun Method and its private learned resources."""

from __future__ import annotations

from libs.skill_evolution.patcher import SkillPatchEvolver


class MethodPatchEvolver(SkillPatchEvolver):
    """Evolve a Method entry point plus resources in its learned namespace."""

    ARTIFACT_PATH = "skillflow-method/skillflow-method.workflow"
    LEARNED_DIR = "skillflow-method/learned"

    SYSTEM_PROMPT = """You evolve one Haitun Method from completed trial evidence.

You may update the runtime entry point
`skillflow-method/skillflow-method.workflow` and create, update, organize, or
delete supporting material anywhere under the private
`skillflow-method/learned/` directory. Do not write outside those locations and
do not delete the runtime entry point.

Within the runtime entry point, choose any Method structure, length, workflow
topology, number of agents, prompts, and recovery strategy supported by the evidence.
There is no fixed step sequence, line limit, or required agent count. Return an
empty patch when the evidence does not justify a change.

Use the `.workflow` file for executable orchestration. Use `learned/` for
reusable scripts, detailed references, examples, schemas, checklists, or other
learned resources. When a learned file should affect execution, make the Method
explicitly tell its agents when and how to use it from
`/workspace/flows/workflows/skillflow-method/learned/`.

Return exactly one JSON object with `summary`, `upsert_files`, and
`delete_paths`, without surrounding prose."""

    USER_PROMPT_TEMPLATE = """# Single-Method evolution task

Update the Method's runtime entry point and private learning space:
- `skillflow-method/skillflow-method.workflow`
- `skillflow-method/learned/**`

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

Infer evidence-backed changes to the Method and any supporting learned files.
Its internal graph, text, learned-file count, and learned-file types are
unrestricted within its private namespace.

Return exactly this JSON shape and no surrounding prose:

```json
{{
  "summary": "brief evidence-based rationale",
  "upsert_files": {{
    "skillflow-method/skillflow-method.workflow": "complete Method source",
    "skillflow-method/learned/example.md": "reusable learned material"
  }},
  "delete_paths": ["skillflow-method/learned/obsolete.md"]
}}
```
"""
