ARG BASE_IMAGE=skillflow/harbor-cli-base:ubuntu24.04
FROM ${BASE_IMAGE}

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && /root/.local/bin/uv python install 3.14

WORKDIR /opt/haitun-agent
COPY . /opt/haitun-agent

RUN /root/.local/bin/uv sync --frozen --no-dev \
    && /opt/haitun-agent/.venv/bin/python -m ensurepip --upgrade \
    && find /opt/haitun-agent/examples/haitun-workspace/tools \
        -mindepth 1 -maxdepth 1 \
        ! -name bash.py \
        ! -name read.py \
        ! -name write.py \
        ! -name run_flow.py \
        ! -name _runtime_paths.py \
        ! -name _user_profile.py \
        ! -name _background_process_registry.py \
        -exec rm -rf {} + \
    && find /opt/haitun-agent/examples/haitun-workspace/skills \
        -mindepth 1 -maxdepth 1 \
        ! -name workflow \
        -exec rm -rf {} + \
    && rm -f \
        /opt/haitun-agent/examples/haitun-workspace/AGENTS.md \
        /opt/haitun-agent/examples/haitun-workspace/TOOLS.md \
        /opt/haitun-agent/examples/haitun-workspace/BOOTSTRAP.md \
    && test -f /opt/haitun-agent/examples/haitun-workspace/tools/run_flow.py \
    && test -f /opt/haitun-agent/examples/haitun-workspace/skills/workflow/SKILL.md \
    && test -f /opt/haitun-agent/examples/haitun-workspace/skills/workflow/fusion_flow/workflow_runner.py

ENV PATH=/root/.local/bin:${PATH} \
    HAITUN_WORKSPACE_TEMPLATE=/opt/haitun-agent/examples/haitun-workspace
