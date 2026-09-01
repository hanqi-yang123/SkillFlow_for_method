from __future__ import annotations

import unittest

from libs.method_evolution import MethodPatchEvolver
from libs.skill_evolution.patcher import SkillPatchEvolver, SkillPatchResult
from libs.workflow_evolution import WorkflowPatchEvolver


class EvolutionArtifactBoundaryTests(unittest.TestCase):
    def _evolver(self, evolver_type):
        return evolver_type(model_name="unused")

    def test_each_evolver_accepts_only_its_single_artifact(self) -> None:
        cases = (
            (SkillPatchEvolver, "skillflow-skill/SKILL.md"),
            (MethodPatchEvolver, "skillflow-method/skillflow-method.workflow"),
            (WorkflowPatchEvolver, "dynamic-task-solver.js"),
        )
        for evolver_type, artifact_path in cases:
            with self.subTest(evolver=evolver_type.__name__):
                patch = SkillPatchResult(
                    summary="valid",
                    upsert_files={artifact_path: "arbitrary full contents"},
                    delete_paths=[],
                )
                constrained = self._evolver(evolver_type)._constrain_to_artifact(patch)
                self.assertEqual(constrained.upsert_files, patch.upsert_files)
                self.assertEqual(constrained.delete_paths, [])

    def test_any_second_file_rejects_the_entire_patch(self) -> None:
        evolver = self._evolver(WorkflowPatchEvolver)
        patch = SkillPatchResult(
            summary="attempted escape",
            upsert_files={
                "dynamic-task-solver.js": "valid target",
                "helper.js": "not allowed",
            },
            delete_paths=[],
        )
        constrained = evolver._constrain_to_artifact(patch)
        self.assertEqual(constrained.upsert_files, {})
        self.assertIn("unexpected paths: helper.js", constrained.summary)

    def test_deletion_rejects_the_entire_patch(self) -> None:
        evolver = self._evolver(MethodPatchEvolver)
        patch = SkillPatchResult(
            summary="attempted deletion",
            upsert_files={evolver.ARTIFACT_PATH: "replacement"},
            delete_paths=[evolver.ARTIFACT_PATH],
        )
        constrained = evolver._constrain_to_artifact(patch)
        self.assertEqual(constrained.upsert_files, {})
        self.assertEqual(constrained.delete_paths, [])
        self.assertIn("deletions are not permitted", constrained.summary)

    def test_workflow_content_has_no_agent_or_line_limit(self) -> None:
        evolver = self._evolver(WorkflowPatchEvolver)
        unrestricted_source = "\n".join(["// no agent call"] * 1_000)
        patch = SkillPatchResult(
            summary="large nonlinear design is permitted",
            upsert_files={evolver.ARTIFACT_PATH: unrestricted_source},
            delete_paths=[],
        )
        constrained = evolver._constrain_to_artifact(patch)
        self.assertEqual(constrained.upsert_files[evolver.ARTIFACT_PATH], unrestricted_source)

    def test_method_content_has_no_structure_or_line_limit(self) -> None:
        evolver = self._evolver(MethodPatchEvolver)
        unrestricted_source = "\n".join(["arbitrary method source"] * 1_000)
        patch = SkillPatchResult(
            summary="arbitrary topology is permitted",
            upsert_files={evolver.ARTIFACT_PATH: unrestricted_source},
            delete_paths=[],
        )
        constrained = evolver._constrain_to_artifact(patch)
        self.assertEqual(constrained.upsert_files[evolver.ARTIFACT_PATH], unrestricted_source)


if __name__ == "__main__":
    unittest.main()
