# Conversation-Driven Changes: Method

This file records the experiment-design changes requested during the review of
the Skill, Method, and Claude Code Workflow comparison.

## Changes made

- The earlier Method arm was limited to one `.workflow` file and also carried
  extra structural requirements, a fixed validation sequence, and a line cap.
- The structural, line-count, topology, and agent-count restrictions were
  removed first, leaving only a single-file mutation boundary.
- That single-file restriction has now also been removed. Method may update
  `skillflow-method/skillflow-method.workflow` and may create, update, organize,
  or delete learned material below `skillflow-method/learned/`.
- Method must not write outside its own namespace or delete its executable
  `.workflow` entry point.
- The added `configs/method.yaml` is only a runtime example. An earlier revision
  accidentally selected Claude Sonnet 4.5; it now uses explicit provider/model
  placeholders so an experiment must supply the same model used by the Skill
  and Workflow arms.

## Intended use of this directory

Store reusable scripts, detailed references, schemas, examples, checklists,
decision records, and troubleshooting material here. Keep executable
orchestration in the `.workflow` file, and make its agent instructions point to
learned resources when they should affect a future run.
