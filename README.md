# SkillFlow

**[Website](https://zhangzi-a.github.io/SkillFlow-project-page/)** · **[Paper](https://arxiv.org/abs/2604.17308)** · **[Hugging Face Data](https://huggingface.co/datasets/zhang-ziao/SkillFlow-Task)** · **[Hugging Face Paper](https://huggingface.co/papers/2604.17308)** · **[Harbor Docs](https://www.harborframework.com/docs)**

SkillFlow is an open benchmark for evaluating autonomous agents on executable office and data workflows, with support for both baseline runs and iterative shared-skill evolution.

## Introduction

SkillFlow is a benchmark for studying how agents solve workflow tasks, externalize reusable skills, and improve through cross-task skill evolution under executable evaluation settings.

SkillFlow focuses on two settings:

- **Baseline**: run each workflow family without cross-task skill evolution
- **Iterative**: evolve shared skills across tasks within a workflow family

This repository contains the code, runners, analysis scripts, and Docker setup for the benchmark.
Task data is distributed separately via Hugging Face.
For readers interested in inspecting the final evolved shared-skill library produced by the iterative setting, we also release collected final skills at [Hugging Face](https://huggingface.co/datasets/zhang-ziao/SkillFlow-exp-skills).

## Quick Start

```bash
# Install Harbor
uv tool install 'harbor @ git+https://github.com/laude-institute/harbor.git'

# Install project dependencies
uv sync

# Download task data from Hugging Face
hf download zhang-ziao/SkillFlow-Task --repo-type dataset --local-dir test_tasks

# Build the base image
./docker/harbor-cli-base/build.sh

# Optionally prebuild task images
python utils/prebuild_task_images.py --tasks-root test_tasks --image-prefix skillflow-prebuilt
```

After downloading, the local layout is expected to look like:

```text
test_tasks/
  <workflow-family>/
    ALL_TASK_DIFFICULTY_RANKING.json
    <task-name>/
      instruction.md
      task.toml
      environment/
      tests/
      solution/
```

## Run the Benchmark

### Baseline

Edit `configs/baseline.yaml`, then run:

```bash
python family_job_runner.py
```

### Iterative Shared Skills

Edit `configs/iter.yaml`, then run:

```bash
python iterative_shared_skills_runner.py
```

The iterative setting uses `shared_skills_template/skills` as the default initial shared-skill directory.

The runner can also compare three single-artifact evolution modes:

```bash
python iterative_shared_skills_runner.py --evolution-kind skill
python iterative_shared_skills_runner.py --evolution-kind method
python iterative_shared_skills_runner.py --evolution-kind workflow
```

Method mode uses the Haitun `run_flow` adapter. Build its runtime image from a
sibling `haitun-agent` checkout, then use `configs/method.yaml`:

```bash
bash docker/haitun-agent/build.sh
python iterative_shared_skills_runner.py --config configs/method.yaml --evolution-kind method
```

Their mutation budgets are intentionally symmetric: Skill may update only
`skillflow-skill/SKILL.md`, Method only
`skillflow-method/skillflow-method.workflow`, and executable Workflow only
`dynamic-task-solver.js`. Deletions and additional files are rejected as a
whole patch. Method and executable Workflow have no imposed line, agent-count,
or graph-topology limits.

Workflow mode sets `SKILLFLOW_EXECUTABLE_WORKFLOW=dynamic-task-solver`, mounts
the JavaScript artifact in Claude's Workflow directory, and writes a session
permission rule denying `Skill(dynamic-task-solver)`. This prevents the parent
or a spawned agent from recursively treating the executable Workflow as a
same-name Skill while leaving the top-level Workflow invocation available.

## Repository Layout

- `configs/`: example configs for baseline and iterative runs
- `docker/harbor-cli-base/`: base image with preinstalled agent CLIs
- `docker/haitun-agent/`: reproducible Haitun Method runtime overlay
- `analysis/`: result summarization and plotting scripts
- `utils/prebuild_task_images.py`: prebuild task images and write `docker_image` into `task.toml`
- `shared_skills_template/`: initial shared-skill template
- `shared_methods_template/`: initial single-Method template
- `shared_workflows_template/`: initial executable-Workflow template

## Notes

- This release does **not** include OpenHands in the base image.
- Domestic package mirrors are intentionally removed from the Docker setup.
- Replace API keys, model names, and endpoints in the example configs before running.

## BibTeX

```bibtex
@article{zhang2026skillflow,
  title         = {SkillFlow: Benchmarking Skill Evolution for Autonomous Agents},
  author        = {Zhang, Ziao and others},
  year          = {2026},
  journal       = {arXiv preprint arXiv:2604.17308},
  eprint        = {2604.17308},
  archivePrefix = {arXiv},
  url           = {https://arxiv.org/abs/2604.17308}
}
```
