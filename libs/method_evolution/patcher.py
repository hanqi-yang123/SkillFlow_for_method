"""Evolve one reusable Haitun workflow and its supporting files."""

from __future__ import annotations

from libs.skill_evolution.patcher import SkillPatchEvolver, SkillPatchResult


class MethodPatchEvolver(SkillPatchEvolver):
    """Keep generated changes inside one canonical family workflow bundle."""

    WORKFLOW_PATH = "skillflow-method/skillflow-method.workflow"
    BUNDLE_DIR = "skillflow-method"
    INSTRUCTIONS_DIR = "skillflow-method/instructions"
    PROGRAMS_DIR = "skillflow-method/programs"

    SYSTEM_PROMPT = """You evolve one reusable executable Haitun/FusionFlow workflow from completed execution evidence.

A workflow expresses a reusable method as a dataflow graph:

- Steps represent distinct parts of the work.
- Artifacts represent explicit inputs, intermediate results, and outputs.
- `consumes(...)` and `produces(...)` define the dataflow between Steps.
- Every Step has a supported executor and a clear `step_instruction(step)`.

Improve the workflow and its supporting files when the evidence supports a
reusable change.

Preserve behavior that worked. Prefer concrete execution results over
unsupported self-reports. Make focused changes, avoid redundant Steps or agents,
and use only as much orchestration as the evidence supports. Encode each learned
rule in the relevant Step instruction or graph relationship.

Keep the workflow parseable, executable, self-contained, and reusable. Preserve
its external input and output interfaces unless the evidence requires a compatible
correction. Do not retain one-off values, answers, identifiers, or incidental
details from the completed task.

Modify only the workflow bundle and paths specified in the update request.
Never use absolute paths or `..`, modify generated runtime state, or delete the
primary workflow source. Create supporting files only when the workflow uses
them.

Return an empty patch when no defensible reusable improvement is supported.

Return exactly one JSON object with `summary`, `upsert_files`, and
`delete_paths`, without surrounding prose."""

    USER_PROMPT_TEMPLATE = """# Single-workflow evolution task

Update the active Haitun workflow bundle:
- Primary workflow: `{workflow_path}`
- Step instructions: `{bundle_dir}/instructions/**`
- Program Step helpers: `{bundle_dir}/programs/**`

All response paths are relative to `/workspace/flows/workflows/`.
Do not use any other workflow bundle or directory.

## Current workflow tree
{tree_json}

## Current workflow contents
{files_block}

## Trial evidence
- Task: {task_name}
- Family: {task_source}
- Verifier passed: {verifier_passed}
- Reward: {reward}
- Exception: {exception_info}
- Failed tests: {failed_tests}

## Verifier feedback from the completed trial
{verifier_feedback}

## Final agent message
{final_message}

## Compacted execution trace
{trajectory_json}

## Update procedure
1. Compare the workflow execution trace with verifier results; verifier results
   take precedence over agent self-reports.
2. Identify which workflow Step, Step instruction, Artifact dependency, handoff,
   decision rule, validation practice, or recovery path should change.
3. Preserve behavior that worked and change only what the evidence supports.
4. Update the executable workflow graph and, when useful, its supporting files
   so future related tasks execute the improved behavior.
5. Avoid redundant orchestration and keep all Step instructions generalized to
   the task family rather than the completed task.
6. Return an empty patch when no defensible reusable improvement is supported.

Return exactly this JSON shape and no surrounding prose:

```json
{{
  "summary": "brief evidence-based rationale",
  "upsert_files": {{
    "{workflow_path}": "complete workflow source",
    "{bundle_dir}/instructions/example.md": "reusable Step instruction"
  }},
  "delete_paths": ["{bundle_dir}/instructions/obsolete.md"]
}}
```
"""

    def __init__(
        self,
        model_name: str,
        api_base: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 8192,
        extra_headers: dict[str, str] | None = None,
        workflow_path: str = WORKFLOW_PATH,
        bundle_dir: str | None = None,
    ) -> None:
        super().__init__(
            model_name=model_name,
            api_base=api_base,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_headers=extra_headers,
        )
        resolved_bundle = bundle_dir or workflow_path.rsplit("/", 1)[0]
        if (
            not self._is_safe_relative_path(workflow_path)
            or not self._is_safe_relative_path(resolved_bundle)
            or not workflow_path.startswith(f"{resolved_bundle}/")
            or not workflow_path.endswith(".workflow")
        ):
            raise ValueError(f"Invalid Method workflow bundle: {workflow_path!r}")
        self.WORKFLOW_PATH = workflow_path
        self.BUNDLE_DIR = resolved_bundle
        self.INSTRUCTIONS_DIR = f"{resolved_bundle}/instructions"
        self.PROGRAMS_DIR = f"{resolved_bundle}/programs"
        self.USER_PROMPT_TEMPLATE = (
            type(self).USER_PROMPT_TEMPLATE
            .replace("{workflow_path}", self.WORKFLOW_PATH)
            .replace("{bundle_dir}", self.BUNDLE_DIR)
        )

    @staticmethod
    def _is_safe_relative_path(path: str) -> bool:
        if not path or "\\" in path or path.startswith("/"):
            return False
        return all(part not in {"", ".", ".."} for part in path.split("/"))

    def _is_supporting_path(self, path: str) -> bool:
        return self._is_safe_relative_path(path) and any(
            path.startswith(f"{directory}/")
            for directory in (self.INSTRUCTIONS_DIR, self.PROGRAMS_DIR)
        )

    def _is_allowed_upsert(self, path: str) -> bool:
        return path == self.WORKFLOW_PATH or self._is_supporting_path(path)

    def _constrain_to_artifact(self, patch: SkillPatchResult) -> SkillPatchResult:
        """Keep Method mutations inside the active family workflow bundle."""
        safe_upserts = {
            path: content
            for path, content in patch.upsert_files.items()
            if self._is_allowed_upsert(path)
        }
        safe_deletes = [
            path for path in patch.delete_paths if self._is_supporting_path(path)
        ]
        ignored_upserts = sorted(set(patch.upsert_files) - set(safe_upserts))
        ignored_deletes = sorted(set(patch.delete_paths) - set(safe_deletes))

        summary = patch.summary
        ignored: list[str] = []
        if ignored_upserts:
            ignored.append(f"ignored out-of-scope upserts: {', '.join(ignored_upserts)}")
        if ignored_deletes:
            ignored.append(f"ignored out-of-scope deletes: {', '.join(ignored_deletes)}")
        if ignored:
            note = "; ".join(ignored)
            summary = f"{summary} [Path filter: {note}]" if summary else f"Path filter: {note}"

        return SkillPatchResult(
            summary=summary,
            upsert_files=safe_upserts,
            delete_paths=safe_deletes,
            attempt_count=patch.attempt_count,
            attempt_modes=list(patch.attempt_modes),
            successful_attempt=patch.successful_attempt,
            successful_prompt_mode=patch.successful_prompt_mode,
            successful_attempt_kind=patch.successful_attempt_kind,
        )
