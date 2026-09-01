from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from libs.method_evolution import MethodPatchEvolver
from libs.skill_evolution.patcher import SkillPatchEvolver, SkillPatchResult
from libs.workflow_evolution import WorkflowPatchEvolver


class EvolutionArtifactBoundaryTests(unittest.TestCase):
    def _evolver(self, evolver_type):
        return evolver_type(model_name="unused")

    def test_each_evolver_accepts_entry_point_and_learned_tree(self) -> None:
        cases = (
            (SkillPatchEvolver, "skillflow-skill/SKILL.md", "skillflow-skill/learned"),
            (
                MethodPatchEvolver,
                "skillflow-method/skillflow-method.workflow",
                "skillflow-method/learned",
            ),
            (WorkflowPatchEvolver, "dynamic-task-solver.js", "dynamic-task-solver/learned"),
        )
        for evolver_type, artifact_path, learned_dir in cases:
            with self.subTest(evolver=evolver_type.__name__):
                patch = SkillPatchResult(
                    summary="valid",
                    upsert_files={
                        artifact_path: "arbitrary full contents",
                        f"{learned_dir}/notes.md": "notes",
                        f"{learned_dir}/scripts/helper.py": "print('learned')",
                    },
                    delete_paths=[f"{learned_dir}/obsolete.md"],
                )
                constrained = self._evolver(evolver_type)._constrain_to_namespace(patch)
                self.assertEqual(constrained.upsert_files, patch.upsert_files)
                self.assertEqual(constrained.delete_paths, patch.delete_paths)

    def test_file_outside_private_namespace_rejects_entire_patch(self) -> None:
        evolver = self._evolver(WorkflowPatchEvolver)
        patch = SkillPatchResult(
            summary="attempted escape",
            upsert_files={
                "dynamic-task-solver.js": "valid target",
                "helper.js": "not allowed",
            },
            delete_paths=[],
        )
        constrained = evolver._constrain_to_namespace(patch)
        self.assertEqual(constrained.upsert_files, {})
        self.assertIn("out-of-scope upserts: helper.js", constrained.summary)

    def test_entry_point_deletion_rejects_the_entire_patch(self) -> None:
        evolver = self._evolver(MethodPatchEvolver)
        patch = SkillPatchResult(
            summary="attempted deletion",
            upsert_files={evolver.ARTIFACT_PATH: "replacement"},
            delete_paths=[evolver.ARTIFACT_PATH],
        )
        constrained = evolver._constrain_to_namespace(patch)
        self.assertEqual(constrained.upsert_files, {})
        self.assertEqual(constrained.delete_paths, [])
        self.assertIn("out-of-scope deletes", constrained.summary)

    def test_unsafe_paths_are_rejected(self) -> None:
        evolver = self._evolver(SkillPatchEvolver)
        unsafe_paths = (
            "/skillflow-skill/learned/absolute.md",
            "skillflow-skill/learned/../escape.md",
            "skillflow-skill/learned\\windows-escape.md",
            "skillflow-skill/learned//empty-component.md",
        )
        for unsafe_path in unsafe_paths:
            with self.subTest(path=unsafe_path):
                patch = SkillPatchResult(
                    summary="unsafe",
                    upsert_files={unsafe_path: "content"},
                    delete_paths=[],
                )
                constrained = evolver._constrain_to_namespace(patch)
                self.assertEqual(constrained.upsert_files, {})
                self.assertIn("out-of-scope upserts", constrained.summary)

    def test_learned_files_can_be_created_updated_and_deleted(self) -> None:
        evolver = self._evolver(MethodPatchEvolver)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            obsolete = root / evolver.LEARNED_DIR / "obsolete.md"
            obsolete.parent.mkdir(parents=True)
            obsolete.write_text("old", encoding="utf-8")
            patch = SkillPatchResult(
                summary="learned update",
                upsert_files={
                    f"{evolver.LEARNED_DIR}/notes.md": "new notes",
                    f"{evolver.LEARNED_DIR}/scripts/helper.py": "print('ok')",
                },
                delete_paths=[f"{evolver.LEARNED_DIR}/obsolete.md"],
            )
            constrained = evolver._constrain_to_namespace(patch)
            applied = SkillPatchEvolver.apply_patch(root, constrained)
            self.assertEqual(len(applied["upserted"]), 2)
            self.assertEqual(len(applied["deleted"]), 1)
            self.assertFalse(obsolete.exists())
            self.assertEqual(
                (root / evolver.LEARNED_DIR / "notes.md").read_text(encoding="utf-8"),
                "new notes",
            )

    def test_workflow_content_has_no_agent_or_line_limit(self) -> None:
        evolver = self._evolver(WorkflowPatchEvolver)
        unrestricted_source = "\n".join(["// no agent call"] * 1_000)
        patch = SkillPatchResult(
            summary="large nonlinear design is permitted",
            upsert_files={evolver.ARTIFACT_PATH: unrestricted_source},
            delete_paths=[],
        )
        constrained = evolver._constrain_to_namespace(patch)
        self.assertEqual(constrained.upsert_files[evolver.ARTIFACT_PATH], unrestricted_source)

    def test_method_content_has_no_structure_or_line_limit(self) -> None:
        evolver = self._evolver(MethodPatchEvolver)
        unrestricted_source = "\n".join(["arbitrary method source"] * 1_000)
        patch = SkillPatchResult(
            summary="arbitrary topology is permitted",
            upsert_files={evolver.ARTIFACT_PATH: unrestricted_source},
            delete_paths=[],
        )
        constrained = evolver._constrain_to_namespace(patch)
        self.assertEqual(constrained.upsert_files[evolver.ARTIFACT_PATH], unrestricted_source)


if __name__ == "__main__":
    unittest.main()
