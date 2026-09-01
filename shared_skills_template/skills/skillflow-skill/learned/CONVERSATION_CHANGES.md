# Conversation-Driven Changes: Skill

This file records the experiment-design changes requested during the review of
the Skill, Method, and Claude Code Workflow comparison.

## Changes made

- The earlier Skill arm could carry scripts and reference files while the other
  arms had much narrower mutation budgets.
- It was temporarily restricted to updating only
  `skillflow-skill/SKILL.md` to make the comparison single-artifact.
- That single-file restriction has now been removed. The Skill may update its
  runtime entry point and may create, update, organize, or delete any reusable
  learned material below `skillflow-skill/learned/`.
- The Skill must not write outside its own namespace or delete `SKILL.md`.

## Intended use of this directory

Store reusable scripts, detailed references, schemas, examples, checklists,
decision records, and troubleshooting material here. Keep essential runtime
instructions in `SKILL.md`, and link or point to learned resources from
`SKILL.md` when future agents should use them.
