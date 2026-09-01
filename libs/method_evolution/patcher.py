"""Evolve exactly one Haitun Method file."""

from __future__ import annotations

from libs.skill_evolution.patcher import SkillPatchEvolver


class MethodPatchEvolver(SkillPatchEvolver):
    """Allow evolution to change one Method file and nothing else."""

    ARTIFACT_PATH = "skillflow-method/skillflow-method.workflow"

    SYSTEM_PROMPT = """You evolve one Haitun Method from completed trial evidence.

The only hard artifact restriction is the mutation boundary: `upsert_files` is
either empty or contains exactly
`skillflow-method/skillflow-method.workflow`, and `delete_paths` is empty. Do
not create, update, rename, or delete any other file.

Within that one file, choose any Method structure, length, workflow topology,
number of agents, prompts, and recovery strategy supported by the evidence.
There is no fixed step sequence, line limit, or required agent count. Return an
empty patch when the evidence does not justify a change.

Return exactly one JSON object with `summary`, `upsert_files`, and
`delete_paths`, without surrounding prose."""

    USER_PROMPT_TEMPLATE = """# Single-Method evolution task

Update only `skillflow-method/skillflow-method.workflow`.

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

Infer any evidence-backed changes to the Method. Its internal graph and text
are unrestricted; only the output file boundary is fixed.

Return exactly this JSON shape and no surrounding prose:

```json
{{
  "summary": "brief evidence-based rationale",
  "upsert_files": {{
    "skillflow-method/skillflow-method.workflow": "complete Method source"
  }},
  "delete_paths": []
}}
```
"""
