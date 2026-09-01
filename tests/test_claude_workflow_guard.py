from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from pathlib import PurePosixPath

from libs.harbor_noinstall_agents.workflow_guard import (
    MERGE_SETTINGS_SCRIPT,
    build_workflow_setup_command,
    wrap_workflow_instruction,
)


class ClaudeWorkflowGuardTests(unittest.TestCase):
    def test_setup_copies_workflow_and_denies_same_name_skill(self) -> None:
        command = build_workflow_setup_command(
            PurePosixPath("/logs/agent/sessions/workflows"),
            "dynamic-task-solver",
        )
        self.assertIn("~/.claude/workflows", command)
        self.assertIn("/logs/agent/sessions/settings.json", command)
        self.assertIn("permissions", command)
        self.assertIn("Skill(", command)
        self.assertIn("dynamic-task-solver", command)

    def test_deny_rule_merge_is_idempotent_and_preserves_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            settings_path.write_text(
                json.dumps({"model": "test", "permissions": {"deny": ["Bash(rm:*)"]}}),
                encoding="utf-8",
            )
            for _ in range(2):
                subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        MERGE_SETTINGS_SCRIPT,
                        str(settings_path),
                        "dynamic-task-solver",
                    ],
                    check=True,
                )
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            self.assertEqual(settings["model"], "test")
            self.assertEqual(
                settings["permissions"]["deny"],
                ["Bash(rm:*)", "Skill(dynamic-task-solver)"],
            )

    def test_prompt_forbids_recursive_skill_and_workflow_invocation(self) -> None:
        prompt = wrap_workflow_instruction("make output.txt", "dynamic-task-solver")
        self.assertIn("Never invoke", prompt)
        self.assertIn("Skill(dynamic-task-solver)", prompt)
        self.assertIn("must not invoke", prompt)
        self.assertIn("recursively", prompt)

if __name__ == "__main__":
    unittest.main()
