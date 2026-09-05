from pathlib import Path

import pytest

from iterative_shared_skills_runner import (
    expand_config_environment,
    load_task_manifest,
    select_manifest_tasks,
)


def test_expand_config_environment_recurses(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKILLFLOW_TEST_KEY", "secret-from-environment")

    expanded = expand_config_environment(
        {"agents": [{"env": {"API_KEY": "${SKILLFLOW_TEST_KEY}"}}]}
    )

    assert expanded["agents"][0]["env"]["API_KEY"] == "secret-from-environment"


def test_expand_config_environment_rejects_missing_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SKILLFLOW_MISSING_KEY", raising=False)

    with pytest.raises(ValueError, match="SKILLFLOW_MISSING_KEY"):
        expand_config_environment("${SKILLFLOW_MISSING_KEY}")


def test_manifest_preserves_requested_order(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        '{"Finance": ["task-b", "task-a"]}',
        encoding="utf-8",
    )
    manifest = load_task_manifest(manifest_path)
    paths = [tmp_path / "task-a", tmp_path / "task-b"]

    assert select_manifest_tasks(paths, "Finance", manifest) == [
        tmp_path / "task-b",
        tmp_path / "task-a",
    ]


def test_manifest_rejects_unknown_tasks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="missing-task"):
        select_manifest_tasks(
            [tmp_path / "task-a"],
            "Finance",
            {"Finance": ["missing-task"]},
        )
