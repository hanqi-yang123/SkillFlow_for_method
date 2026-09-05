#!/usr/bin/env python3
"""Emit compact, billing-aware audit rows for downloaded Haitun Method trials."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


def timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_counts(path: Path) -> tuple[int | None, int | None]:
    if not path.exists():
        return None, None
    candidates: list[tuple[int, int]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "passed" not in line and "failed" not in line:
            continue
        passed = sum(int(value) for value in re.findall(r"(\d+) passed", line))
        failed = sum(int(value) for value in re.findall(r"(\d+) failed", line))
        if passed or failed:
            candidates.append((passed, failed))
    return max(candidates, key=lambda item: sum(item), default=(None, None))


def complete_usage(path: Path) -> dict[str, int | float]:
    rows = []
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    complete = []
    for row in rows:
        usage = row.get("token_usage") or {}
        fields = ("input_tokens", "cached_input_tokens", "output_tokens")
        if usage.get("complete") is True and all(usage.get(key) is not None for key in fields):
            complete.append(usage)
    input_tokens = sum(int(row["input_tokens"]) for row in complete)
    cache_tokens = sum(int(row["cached_input_tokens"]) for row in complete)
    output_tokens = sum(int(row["output_tokens"]) for row in complete)
    cost = ((input_tokens - cache_tokens) * 5 + cache_tokens * 0.5 + output_tokens * 25) / 1_000_000
    return {
        "usage_records": len(rows),
        "complete_usage_records": len(complete),
        "incomplete_usage_records": len(rows) - len(complete),
        "complete_input_tokens": input_tokens,
        "complete_cache_tokens": cache_tokens,
        "complete_output_tokens": output_tokens,
        "complete_records_cost_usd": cost,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+", type=Path)
    args = parser.parse_args()

    trials = []
    for root in args.roots:
        for result_path in sorted(root.rglob("result.json")):
            trial_dir = result_path.parent
            if not (trial_dir / "agent").is_dir():
                continue
            result = json.loads(result_path.read_text(encoding="utf-8"))
            agent = result.get("agent_result") or {}
            verifier = result.get("verifier_result") or {}
            rewards = verifier.get("rewards") or {}
            started = timestamp(result.get("started_at"))
            finished = timestamp(result.get("finished_at"))
            passed, failed = test_counts(trial_dir / "verifier" / "test-stdout.txt")
            trials.append(
                {
                    "run": root.name,
                    "trial": trial_dir.name,
                    "task_name": result.get("task_name"),
                    "family": result.get("source"),
                    "reward": rewards.get("reward"),
                    "tests_passed": passed,
                    "tests_failed": failed,
                    "exception_type": (result.get("exception_info") or {}).get("exception_type"),
                    "started_at": result.get("started_at"),
                    "finished_at": result.get("finished_at"),
                    "duration_seconds": (finished - started).total_seconds() if started and finished else None,
                    "agent_input_tokens": agent.get("n_input_tokens"),
                    "agent_cache_tokens": agent.get("n_cache_tokens"),
                    "agent_output_tokens": agent.get("n_output_tokens"),
                    "agent_cost_usd": agent.get("cost_usd"),
                    "billing_complete": ((agent.get("metadata") or {}).get("haitun_billing") or {}).get("complete"),
                    "patch_archived": (trial_dir / "skill_evolution" / "patch.json").exists(),
                    "patch_applied": (trial_dir / "skill_evolution" / "applied.json").exists(),
                    **complete_usage(trial_dir / "agent" / "haitun-ai-usage.jsonl"),
                }
            )
    print(json.dumps(trials, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
