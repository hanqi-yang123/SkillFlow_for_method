const task_instruction: Artifact;
const task_completion: Artifact;
const execute_task: Step;
const task_agent: Agent, Executor;

workflow skillflow_method {
  input_workflow(skillflow_method) == [task_instruction];
  consumes(execute_task) == [task_instruction];
  produces(execute_task) == [task_completion];
  output_workflow(skillflow_method) == [task_completion];
  step_executor(execute_task) == task_agent;
  step_name(execute_task) == "Execute SkillFlow Task";
  step_instruction(execute_task) == "Read task_instruction completely. Work only in the assigned task workspace. Inspect inputs before changing them, implement every explicit contract, and perform the strongest available structural and semantic checks. If validation fails, diagnose the deliverable, fix it without editing tests or harness files, and rerun validation. Leave only the requested deliverables and accurately report which validation was actually available.";
}
