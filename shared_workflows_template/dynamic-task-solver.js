export const meta = {
  name: 'dynamic-task-solver',
  description: 'Execute and independently validate one benchmark task',
  phases: [
    { title: 'Execute' },
    { title: 'Audit and fix' }
  ]
}

phase('Execute')
const execution = await agent(`Complete the task in the current workspace.
Inspect relevant inputs, produce the exact requested deliverables, and validate
them from disk. Perform the work directly with ordinary tools. Do not invoke
dynamic-task-solver as either a Skill or Workflow from this child agent.

TASK:
${args.instruction}`, { label: 'executor', phase: 'Execute' })

phase('Audit and fix')
const audit = await agent(`Independently inspect and validate the task outputs
in the current workspace. Correct any defect you find and rerun the strongest
available checks. Do not trust the prior report, and do not invoke
dynamic-task-solver as either a Skill or Workflow from this child agent.

TASK:
${args.instruction}

PRIOR REPORT:
${execution || '<none>'}`, { label: 'auditor-fixer', phase: 'Audit and fix' })

return { execution, audit }
