from __future__ import annotations

import json
import os
import shlex
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

import litellm

from harbor.agents.installed.base import ExecInput
from harbor.agents.installed.claude_code import ClaudeCode
from harbor.agents.installed.qwen_code import QwenCode
from harbor.environments.base import BaseEnvironment

from .workflow_guard import build_workflow_setup_command, wrap_workflow_instruction

try:
    from harbor.agents.installed.kimi_cli import (
        KimiCli,
        _OUTPUT_FILENAME as _KIMI_OUTPUT_FILENAME,
        _PROVIDER_CONFIG as _KIMI_PROVIDER_CONFIG,
    )
except ModuleNotFoundError:  # pragma: no cover - depends on installed Harbor version
    KimiCli = None
    _KIMI_OUTPUT_FILENAME = "kimi-cli.txt"
    _PROVIDER_CONFIG = {}

try:
    from harbor.agents.installed.codex import Codex
except ModuleNotFoundError:  # pragma: no cover - depends on installed Harbor version
    Codex = None


class _NoInstallSetupMixin:
    """Skip Harbor's install.sh setup and only do best-effort version detection."""

    async def setup(self, environment: BaseEnvironment) -> None:
        setup_dir = self.logs_dir / "setup"
        setup_dir.mkdir(parents=True, exist_ok=True)
        (setup_dir / "mode.txt").write_text(
            "skip install script; use preinstalled CLI in image\n",
            encoding="utf-8",
        )

        if getattr(self, "_version", None) is None:
            get_version_command = getattr(self, "get_version_command", None)
            parse_version = getattr(self, "parse_version", None)
            version_cmd = get_version_command() if callable(get_version_command) else None
            if version_cmd:
                try:
                    result = await environment.exec(command=version_cmd)
                    (setup_dir / "version-return-code.txt").write_text(
                        str(result.return_code), encoding="utf-8"
                    )
                    if result.stdout:
                        (setup_dir / "version-stdout.txt").write_text(
                            result.stdout, encoding="utf-8"
                        )
                    if result.stderr:
                        (setup_dir / "version-stderr.txt").write_text(
                            result.stderr, encoding="utf-8"
                        )
                    if result.return_code == 0 and result.stdout:
                        self._version = (
                            parse_version(result.stdout)
                            if callable(parse_version)
                            else result.stdout.strip()
                        )
                except Exception as exc:  # pragma: no cover
                    (setup_dir / "version-error.txt").write_text(
                        str(exc), encoding="utf-8"
                    )


class NoInstallClaudeCode(_NoInstallSetupMixin, ClaudeCode):
    """Claude Code agent that assumes `claude` is already available in the image."""

    @staticmethod
    def name() -> str:
        return ClaudeCode.name()

    def _workflow_name(self) -> str:
        return (self._extra_env.get("SKILLFLOW_EXECUTABLE_WORKFLOW") or "").strip()

    def _wrap_workflow_instruction(self, instruction: str) -> str:
        return wrap_workflow_instruction(instruction, self._workflow_name())

    async def run(self, instruction: str, environment: BaseEnvironment, context: Any) -> None:
        workflow_name = self._workflow_name()
        if workflow_name:
            # Harbor gives each run a fresh CLAUDE_CONFIG_DIR below /logs. Put
            # the mounted Workflow and its deny rule in that shared session
            # config so both the parent and all child agents inherit the block.
            workflow_dir = self.environment_logs_dir / "sessions" / "workflows"
            await self.exec_as_agent(
                environment,
                command=build_workflow_setup_command(workflow_dir, workflow_name),
            )
        await super().run(self._wrap_workflow_instruction(instruction), environment, context)

    def create_run_agent_commands(self, instruction: str):
        instruction = self._wrap_workflow_instruction(instruction)
        original_env = {key: os.environ.get(key) for key in self._extra_env}
        try:
            os.environ.update(self._extra_env)
            return super().create_run_agent_commands(instruction)
        finally:
            for key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value


class NoInstallHaitun(_NoInstallSetupMixin, ClaudeCode):
    """Run a preinstalled Haitun session inside the Harbor task container."""

    learning_mode = "skill"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Upload credentials through a protected file rather than exposing
        # them in the host process command line.
        self._haitun_runtime_env = dict(self._extra_env)
        self._extra_env = {}

    @staticmethod
    def name() -> str:
        return "haitun"

    @staticmethod
    def _usage_counts(payload: dict[str, Any]) -> tuple[int, int, int] | None:
        usage = payload.get("token_usage") if "token_usage" in payload else payload.get("totals")
        if not isinstance(usage, dict) or usage.get("complete") is not True:
            return None
        values = (
            usage.get("input_tokens"),
            usage.get("output_tokens"),
            usage.get("cached_input_tokens"),
        )
        if any(type(value) is not int or value < 0 for value in values[:2]):
            return None
        cached = values[2] if values[2] is not None else 0
        if type(cached) is not int or cached < 0 or cached > values[0]:
            return None
        return values[0], values[1], cached

    def _collect_haitun_usage(self, context: Any) -> None:
        report_paths = [self.logs_dir / "haitun-session-usage.json"]
        report_paths.extend(sorted(self.logs_dir.glob("haitun-workflow-token-usage-*.json")))
        counts: list[tuple[int, int, int]] = []
        for report_path in report_paths:
            if not report_path.exists():
                continue
            try:
                payload = json.loads(report_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return
            if not isinstance(payload, dict):
                return
            parsed = self._usage_counts(payload)
            if parsed is None:
                return
            counts.append(parsed)
        if not counts:
            return

        context.n_input_tokens = sum(value[0] for value in counts)
        context.n_output_tokens = sum(value[1] for value in counts)
        context.n_cache_tokens = sum(value[2] for value in counts)
        try:
            input_cost, output_cost = litellm.cost_per_token(
                model=self.model_name,
                prompt_tokens=context.n_input_tokens,
                completion_tokens=context.n_output_tokens,
                cache_read_input_tokens=context.n_cache_tokens,
            )
            context.cost_usd = float(input_cost + output_cost)
        except Exception:
            context.cost_usd = None

    async def run(self, instruction: str, environment: BaseEnvironment, context: Any) -> None:
        secret_env_file: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                prefix="haitun-agent-env-",
                suffix=".sh",
                delete=False,
            ) as handle:
                for key, value in self._haitun_runtime_env.items():
                    handle.write(f"export {key}={shlex.quote(str(value))}\n")
                secret_env_file = Path(handle.name)
            await environment.upload_file(secret_env_file, "/tmp/haitun-agent.env")
        finally:
            if secret_env_file is not None and secret_env_file.exists():
                secret_env_file.unlink()

        prompt = instruction
        materialize = 'cp -a /mnt/learning/. "$AGENT_DIR/skills/"'
        runtime_preflight = ":"
        usage_roots = "/workspace/.psi/fusion-flow/runs"
        if self.learning_mode == "method":
            workflow_path = (
                self._haitun_runtime_env.get("SKILLFLOW_METHOD_WORKFLOW_PATH")
                or "flows/workflows/skillflow-method/skillflow-method.workflow"
            ).strip()
            workflow_parts = PurePosixPath(workflow_path)
            if (
                workflow_parts.is_absolute()
                or workflow_parts.suffix != ".workflow"
                or workflow_parts.parts[:2] != ("flows", "workflows")
                or any(part in {"", ".", ".."} for part in workflow_parts.parts)
            ):
                raise ValueError(f"Invalid Haitun Method workflow path: {workflow_path!r}")
            absolute_workflow_path = f"/workspace/{workflow_path}"
            workflow_bundle_path = str(PurePosixPath(absolute_workflow_path).parent)
            materialize = "cp -a /mnt/learning/. /workspace/flows/workflows/"
            usage_roots += f" {shlex.quote(f'{workflow_bundle_path}/runs')}"
            runtime_preflight = f'''for required in \
  "$AGENT_DIR/tools/bash.py" \
  "$AGENT_DIR/tools/read.py" \
  "$AGENT_DIR/tools/write.py" \
  "$AGENT_DIR/tools/run_flow.py" \
  "$AGENT_DIR/skills/workflow/SKILL.md" \
  "{absolute_workflow_path}"; do
  if [ ! -f "$required" ]; then
    echo "Missing required Haitun workflow runtime file: $required" >&2
    exit 1
  fi
done'''
            prompt = (
                "Use the preloaded Haitun workflow at "
                f"`{workflow_path}`. "
                "Read its declared input, then call `run_flow` exactly once with "
                "the current benchmark instruction as the `task_instruction` "
                "artifact. Do not bypass, re-author, or simulate the workflow. "
                "After `run_flow` returns, report its output artifact mapping.\n\n"
                f"Benchmark instruction:\n{instruction}"
            )

        script = f'''set -euo pipefail
RUN_DIR="$(mktemp -d /tmp/haitun-harbor-XXXXXX)"
AGENT_DIR="$RUN_DIR/agent"
AI_SOCKET="$RUN_DIR/ai.sock"
CHANNEL_SOCKET="$RUN_DIR/channel.sock"
cleanup() {{
  if [ -n "${{SESSION_PID:-}}" ]; then kill "$SESSION_PID" 2>/dev/null || true; wait "$SESSION_PID" 2>/dev/null || true; fi
  if [ -n "${{AI_PID:-}}" ]; then kill "$AI_PID" 2>/dev/null || true; wait "$AI_PID" 2>/dev/null || true; fi
  rm -rf "$RUN_DIR"
}}
trap cleanup EXIT
test -r /tmp/haitun-agent.env || {{ echo "Missing Haitun runtime environment file" >&2; exit 1; }}
. /tmp/haitun-agent.env
rm -f /tmp/haitun-agent.env
cp -a "$HAITUN_WORKSPACE_TEMPLATE" "$AGENT_DIR"
if [ -d /mnt/learning ]; then
  mkdir -p "$AGENT_DIR/skills" /workspace/flows/workflows
  {materialize}
fi
{runtime_preflight}
export PYTHONUNBUFFERED=1
export PYTHONPATH="$AGENT_DIR/tools${{PYTHONPATH:+:$PYTHONPATH}}"
export PSI_AGENT_USAGE_PATH=/logs/agent/haitun-session-usage.json
/opt/haitun-agent/.venv/bin/psi-agent ai --session-socket "$AI_SOCKET" > /logs/agent/haitun-ai.log 2>&1 &
AI_PID=$!
for _ in $(seq 1 240); do [ -S "$AI_SOCKET" ] && break; kill -0 "$AI_PID" 2>/dev/null || break; sleep 0.25; done
if ! kill -0 "$AI_PID" 2>/dev/null || [ ! -S "$AI_SOCKET" ]; then
  echo "Haitun AI failed to become ready" >&2; cat /logs/agent/haitun-ai.log >&2 || true; exit 1
fi
/opt/haitun-agent/.venv/bin/psi-agent session --workspace /workspace --agent "$AGENT_DIR" \
  --channel-socket "$CHANNEL_SOCKET" --ai-socket "$AI_SOCKET" > /logs/agent/haitun-session.log 2>&1 &
SESSION_PID=$!
for _ in $(seq 1 240); do [ -S "$CHANNEL_SOCKET" ] && break; kill -0 "$SESSION_PID" 2>/dev/null || break; sleep 0.25; done
if ! kill -0 "$SESSION_PID" 2>/dev/null || [ ! -S "$CHANNEL_SOCKET" ]; then
  echo "Haitun Session failed to become ready" >&2; cat /logs/agent/haitun-session.log >&2 || true; exit 1
fi
set +e
/opt/haitun-agent/.venv/bin/psi-agent channel cli --session-socket "$CHANNEL_SOCKET" --message {shlex.quote(prompt)} \
  > /logs/agent/haitun.txt 2>&1
CHANNEL_STATUS=$?
set -e
usage_index=0
while IFS= read -r usage_file; do
  cp "$usage_file" "/logs/agent/haitun-workflow-token-usage-$usage_index.json"
  usage_index=$((usage_index + 1))
done < <(find {usage_roots} -type f -name token-usage.json 2>/dev/null | sort -u)
exit "$CHANNEL_STATUS"
'''
        await self.exec_as_agent(environment, command="bash -lc " + shlex.quote(script))
        self._collect_haitun_usage(context)


class NoInstallHaitunMethod(NoInstallHaitun):
    """Haitun adapter that requires the learned FusionFlow Method."""

    learning_mode = "method"


class NoInstallQwenCode(_NoInstallSetupMixin, QwenCode):
    """Qwen Code agent that assumes `qwen` is already available in the image."""

    @staticmethod
    def name() -> str:
        return QwenCode.name()

    def create_run_agent_commands(self, instruction: str):
        original_env = {key: os.environ.get(key) for key in self._extra_env}
        try:
            os.environ.update(self._extra_env)
            return super().create_run_agent_commands(instruction)
        finally:
            for key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value


if KimiCli is not None:

    class NoInstallKimiCli(_NoInstallSetupMixin, KimiCli):
        """Kimi CLI agent that assumes `kimi` is already available in the image."""

        _STDERR_FILENAME = "kimi-cli.stderr.txt"

        @staticmethod
        def _build_safe_wire_command(escaped_prompt: str, mcp_enabled: bool) -> str:
            mcp_flag = "--mcp-config-file /tmp/kimi-mcp.json" if mcp_enabled else ""
            output_log = f"/logs/agent/{_KIMI_OUTPUT_FILENAME}"
            stderr_log = f"/logs/agent/{NoInstallKimiCli._STDERR_FILENAME}"
            return (
                "bash -lc "
                + shlex.quote(
                    f"""
set -u
PROMPT_FIFO="/tmp/kimi-prompt-$$.fifo"
OUTPUT_FIFO="/tmp/kimi-output-$$.fifo"
OUTPUT_LOG="{output_log}"
STDERR_LOG="{stderr_log}"
rm -f "$PROMPT_FIFO" "$OUTPUT_FIFO"
mkfifo "$PROMPT_FIFO" "$OUTPUT_FIFO"
cleanup() {{
  rm -f "$PROMPT_FIFO" "$OUTPUT_FIFO"
}}
trap cleanup EXIT
: > "$OUTPUT_LOG"
: > "$STDERR_LOG"
kimi --config-file /tmp/kimi-config.json --wire --yolo {mcp_flag} < "$PROMPT_FIFO" > "$OUTPUT_FIFO" 2>> "$STDERR_LOG" &
KIMI_PID=$!
{{
  printf '%s\\n' {escaped_prompt}
  while kill -0 "$KIMI_PID" 2>/dev/null; do
    sleep 1
  done
}} > "$PROMPT_FIFO" &
WRITER_PID=$!
SAW_FINISHED=0
while IFS= read -r line; do
  echo "$line" >> "$OUTPUT_LOG"
  case "$line" in
    *'"id":"1","result":{{"status":"finished"'* )
      SAW_FINISHED=1
      kill "$WRITER_PID" 2>/dev/null || true
      break
      ;;
  esac
done < "$OUTPUT_FIFO"
wait "$WRITER_PID" 2>/dev/null || true
if [ "$SAW_FINISHED" -eq 1 ] && kill -0 "$KIMI_PID" 2>/dev/null; then
  kill "$KIMI_PID" 2>/dev/null || true
fi
wait "$KIMI_PID"
KIMI_STATUS=$?
if [ "$SAW_FINISHED" -eq 1 ]; then
  if [ "$KIMI_STATUS" -eq 0 ] || [ "$KIMI_STATUS" -eq 143 ]; then
    exit 0
  fi
fi
exit "$KIMI_STATUS"
"""
                )
            )

        def create_run_agent_commands(self, instruction: str):
            if not self.model_name or "/" not in self.model_name:
                raise ValueError("Model name must be in format provider/model_name")

            provider, model = self.model_name.split("/", 1)

            original_env = {key: os.environ.get(key) for key in self._extra_env}
            try:
                os.environ.update(self._extra_env)
                config_json = self._build_config_json(provider, model)
                skills_cmd = self._build_register_skills_command()
                mcp_cmd = self._build_register_mcp_servers_command()
            finally:
                for key, original_value in original_env.items():
                    if original_value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = original_value

            escaped_config = shlex.quote(config_json)
            prompt_request = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "prompt",
                    "id": "1",
                    "params": {"user_input": instruction},
                }
            )
            escaped_prompt = shlex.quote(prompt_request)

            env: dict[str, str] = {}
            pcfg = _PROVIDER_CONFIG.get(provider, {})
            for key in pcfg.get("env_keys", []):
                val = self._extra_env.get(key) or os.environ.get(key)
                if val:
                    env[key] = val

            setup_parts = [f"echo {escaped_config} > /tmp/kimi-config.json"]
            if skills_cmd:
                setup_parts.append(skills_cmd)
            if mcp_cmd:
                setup_parts.append(mcp_cmd)

            commands = [ExecInput(command=" && ".join(setup_parts), env=env)]
            commands.append(
                ExecInput(
                    command=self._build_safe_wire_command(
                        escaped_prompt=escaped_prompt,
                        mcp_enabled=bool(mcp_cmd),
                    ),
                    env=env,
                )
            )
            return commands

        @staticmethod
        def name() -> str:
            return KimiCli.name()

else:

    class NoInstallKimiCli:
        """Compatibility placeholder when the installed Harbor build has no Kimi agent."""

        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError(
                "harbor.agents.installed.kimi_cli is not available in the current Harbor installation"
            )

        @staticmethod
        def name() -> str:
            return "kimi-cli"


if Codex is not None:

    class NoInstallCodex(_NoInstallSetupMixin, Codex):
        """Codex CLI agent that assumes `codex` is already available in the image."""

        @staticmethod
        def name() -> str:
            return Codex.name()

        def create_run_agent_commands(self, instruction: str):
            original_env = {key: os.environ.get(key) for key in self._extra_env}
            try:
                os.environ.update(self._extra_env)
                return super().create_run_agent_commands(instruction)
            finally:
                for key, original_value in original_env.items():
                    if original_value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = original_value

else:

    class NoInstallCodex:
        """Compatibility placeholder when the installed Harbor build has no Codex agent."""

        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError(
                "harbor.agents.installed.codex is not available in the current Harbor installation"
            )

        @staticmethod
        def name() -> str:
            return "codex"
