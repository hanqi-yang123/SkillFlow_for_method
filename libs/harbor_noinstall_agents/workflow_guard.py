"""Session setup for executable Claude Workflows."""

from __future__ import annotations

import shlex


MERGE_SETTINGS_SCRIPT = """import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
workflow_name = sys.argv[2]
data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
if not isinstance(data, dict):
    raise TypeError("Claude settings must be a JSON object")
permissions = data.setdefault("permissions", {})
if not isinstance(permissions, dict):
    raise TypeError("Claude permissions settings must be a JSON object")
deny = permissions.setdefault("deny", [])
if not isinstance(deny, list):
    raise TypeError("Claude permissions.deny must be a JSON array")
rule = f"Skill({workflow_name})"
if rule not in deny:
    deny.append(rule)
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
"""


def wrap_workflow_instruction(instruction: str, workflow_name: str) -> str:
    """Require one top-level Workflow call and explicitly forbid recursion."""
    if not workflow_name:
        return instruction
    return f"""Complete this benchmark task through Claude Code's executable Workflow tool.

Mandatory protocol:
1. Invoke the Workflow tool once with `name` set to `{workflow_name}` and
   `args.instruction` set to the complete original task below.
2. Wait for the workflow and all of its agents to finish, then inspect the
   resulting workspace and status.
3. `{workflow_name}` is an executable Workflow, not a Skill. Never invoke
   `Skill({workflow_name})`. Agents launched by the workflow must not invoke
   this Workflow or Skill recursively; they should perform only their assigned
   work with ordinary tools.

Original task:
{instruction}
"""


def build_workflow_setup_command(workflow_dir, workflow_name: str) -> str:
    """Copy a Workflow and deny its same-name Skill alias for the session."""
    settings_path = workflow_dir.parent / "settings.json"
    quoted_workflow_dir = shlex.quote(workflow_dir.as_posix())
    return (
        f"mkdir -p {quoted_workflow_dir} && "
        "if [ -d ~/.claude/workflows ]; then "
        f"cp -r ~/.claude/workflows/. {quoted_workflow_dir}/; "
        "fi && "
        f"python3 -c {shlex.quote(MERGE_SETTINGS_SCRIPT)} "
        f"{shlex.quote(settings_path.as_posix())} {shlex.quote(workflow_name)}"
    )
