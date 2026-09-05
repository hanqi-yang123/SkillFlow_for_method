#!/usr/bin/env python3
"""Reconstruct a Method template by applying one audited evolution patch."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from libs.skill_evolution.patcher import SkillPatchEvolver, SkillPatchResult


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.patch.read_text(encoding="utf-8"))
    patch = SkillPatchResult(**payload)
    shutil.copytree(args.source, args.destination, dirs_exist_ok=True)
    applied = SkillPatchEvolver.apply_patch(args.destination, patch)
    print(json.dumps(applied, ensure_ascii=False))


if __name__ == "__main__":
    main()
