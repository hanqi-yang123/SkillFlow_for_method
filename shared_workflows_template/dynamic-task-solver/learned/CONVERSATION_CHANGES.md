# Conversation-Driven Changes: Claude Code Workflow

This file records the experiment-design changes requested during the review of
the Skill, Method, and Claude Code Workflow comparison.

## Changes made

- The earlier executable Workflow was forced to use two or three agents, stay
  under 300 lines, and preserve a near-linear executor-to-auditor structure.
- Those line-count, agent-count, and graph-topology restrictions were removed,
  leaving only a single-JavaScript-file mutation boundary.
- Recursive exposure was fixed by denying `Skill(dynamic-task-solver)` in the
  inherited Claude session and by telling parent and child agents not to invoke
  the same Workflow recursively.
- The single-file restriction has now also been removed. Workflow may update
  `dynamic-task-solver.js` and may create, update, organize, or delete learned
  material below `dynamic-task-solver/learned/`.
- Workflow must not write outside its own namespace or delete its executable
  JavaScript entry point.

## Intended use of this directory

Store reusable scripts, detailed references, schemas, examples, checklists,
decision records, and troubleshooting material here. The JavaScript Workflow
cannot read files directly, so its prompts should tell an appropriate child
agent when and how to inspect or run these resources with ordinary tools.
