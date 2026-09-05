#!/usr/bin/env python3
"""Run the Haitun + Method arm of the SkillFlow experiment."""

from __future__ import annotations

import sys

from iterative_shared_skills_runner import main


if __name__ == "__main__":
    sys.argv[1:1] = ["--evolution-kind", "method"]
    main()
