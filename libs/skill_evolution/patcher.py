"""
skill_evolution.patcher
-----------------------
用于从 ATIF 轨迹压缩、共享技能快照、patch 生成与应用的核心模块。
目标：将 agent 与环境输出精简后，给模型打 patch，支持新增/更新/删除技能。
"""

from __future__ import annotations

import json
import shutil
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# 可选导入：若实际调用 LLM 时缺失则抛出明确错误
try:
    from libs.terminus_agent.llms.lite_llm import LiteLLM
except Exception as _e:  # pragma: no cover
    LiteLLM = None  # type: ignore[misc,assignment]


@dataclass
class CompactionConfig:
    """轨迹压缩配置。"""
    max_steps: int = 20  # 最多保留最近 N 个交互步
    max_obs_chars: int = 3000  # 单条环境输出最大字符数
    include_agent_message: bool = True
    include_tool_calls: bool = True
    include_env_output: bool = True


@dataclass
class SkillPatchResult:
    """patch 调用结果。"""
    summary: str
    upsert_files: dict[str, str]  # 相对路径 -> 内容
    delete_paths: list[str]
    attempt_count: int = 0
    attempt_modes: list[str] = field(default_factory=list)
    successful_attempt: int | None = None
    successful_prompt_mode: str | None = None
    successful_attempt_kind: str | None = None


@dataclass
class TrialOutcome:
    """一次 trial 的精简结果，用于给模型做 patch 输入。"""
    trial_name: str
    task_name: str
    task_source: str
    verifier_passed: bool
    reward: float | None
    exception_type: str | None
    exception_message: str | None
    failed_test_names: list[str]
    # 压缩后的轨迹（只包含 agent 和环境输出）
    compacted_trajectory: list[dict[str, Any]]
    # 最终 agent 回复（可选）
    final_agent_message: str | None
    # verifier 的可操作失败输出（可选）；仅用于题后学习
    verifier_feedback: str | None = None


def ensure_standard_trajectory(trial_dir: Path) -> Path | None:
    """Return a standard ATIF trajectory path for a trial, materializing from raw Claude logs when needed."""
    trajectory_path = trial_dir / "agent" / "trajectory.json"
    if trajectory_path.exists():
        return trajectory_path

    raw_claude_log_path = trial_dir / "agent" / "claude-code.txt"
    if not raw_claude_log_path.exists():
        return None

    analysis_dir = Path(__file__).resolve().parents[2] / "analysis"
    if str(analysis_dir) not in sys.path:
        sys.path.insert(0, str(analysis_dir))

    try:
        from skill_usage_parser import load_trajectory  # type: ignore
    except Exception:
        return None

    trajectory = load_trajectory(raw_claude_log_path)
    if not isinstance(trajectory, dict):
        return None

    trajectory_path.write_text(
        json.dumps(trajectory, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return trajectory_path


class TrajectoryCompactor:
    """
    从 ATIF trajectory.json 中抽取 agent 与环境输出，忽略其余信息。
    输出为适合做 skill patch 的精简 JSON 列表。
    """

    def __init__(self, config: CompactionConfig | None = None) -> None:
        self.cfg = config or CompactionConfig()

    def compact(self, trajectory_path: Path) -> list[dict[str, Any]]:
        """
        读取 trajectory.json，返回精简后的 step 列表。
        每个 step 仅保留：source, agent_message, tool_calls, env_outputs。
        """
        if not trajectory_path.exists():
            return []

        with open(trajectory_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        steps = data.get("steps", [])
        total_steps = len(steps)
        # 如果步数超限，只保留最后 max_steps 步（包含任务描述的首步通常保留）
        if total_steps > self.cfg.max_steps:
            # 保留首步（user task）+ 最近 max_steps-1 步
            keep_first = 1
            keep_last = self.cfg.max_steps - keep_first
            steps = steps[:keep_first] + steps[-keep_last:]

        compacted: list[dict[str, Any]] = []
        for step in steps:
            source = step.get("source", "")
            compacted_step: dict[str, Any] = {"source": source}

            # agent message（来自 agent 的文本回复）
            if self.cfg.include_agent_message and source == "agent":
                msg = step.get("message", "")
                if msg and msg != "(tool use)":
                    compacted_step["agent_message"] = msg

            # tool_calls：记录工具名 + 参数摘要（不做全量参数）
            if self.cfg.include_tool_calls and source == "agent":
                tool_calls = step.get("tool_calls") or []
                if tool_calls:
                    calls_summary = []
                    for tc in tool_calls:
                        fn = tc.get("function_name", "")
                        args = tc.get("arguments") or {}
                        # 对 args 做极简摘要：只保留字符串值的前 100 字符
                        args_summary = {}
                        for k, v in args.items():
                            if isinstance(v, str):
                                args_summary[k] = v[:100] if len(v) > 100 else v
                            elif isinstance(v, (int, float, bool)):
                                args_summary[k] = v
                            elif isinstance(v, dict):
                                args_summary[k] = f"<dict:{len(v)} keys>"
                            elif isinstance(v, list):
                                args_summary[k] = f"<list:{len(v)}>"
                            else:
                                args_summary[k] = f"<{type(v).__name__}>"
                        calls_summary.append({"function": fn, "args": args_summary})
                    compacted_step["tool_calls"] = calls_summary

            # 环境输出：来自 observation.results 中各工具返回的内容
            if self.cfg.include_env_output and source == "agent":
                obs = step.get("observation") or {}
                results = obs.get("results") or []
                if results:
                    env_outputs = []
                    for r in results:
                        content = r.get("content", "")
                        if content:
                            # 对输出内容做字符截断
                            if len(content) > self.cfg.max_obs_chars:
                                content = content[: self.cfg.max_obs_chars] + "\n...<truncated>"
                            env_outputs.append(content)
                    if env_outputs:
                        compacted_step["env_outputs"] = env_outputs

            # metrics 不保留（避免 token 浪费）

            # 省略空步
            if compacted_step:
                compacted.append(compacted_step)

        return compacted

    def extract_trial_outcome(
        self,
        trajectory_path: Path,
        trial_name: str,
        task_name: str,
        task_source: str,
        trial_result: dict[str, Any] | None,
        verifier_ctr: dict[str, Any] | None,
        verifier_feedback: str | None = None,
    ) -> TrialOutcome:
        """
        从 trajectory + result + verifier 构造精简的 TrialOutcome。
        trial_result: 来自 result.json 的 dict（TrialResult.model_dump()）
        verifier_ctr: 来自 verifier/ctrf.json 的 dict
        """
        compacted = self.compact(trajectory_path)

        # 从 trial_result 提取关键信息
        reward = None
        exception_type = None
        exception_message = None
        verifier_passed = False
        failed_test_names: list[str] = []

        if trial_result:
            reward = trial_result.get("reward")
            exc = trial_result.get("exception_info") or {}
            exception_type = exc.get("exception_type")
            exception_message = exc.get("exception_message")
            # verifier 是否通过：reward == 1.0 或 verifier_result.success
            verifier_passed = bool(reward == 1.0)

        if verifier_ctr:
            results = verifier_ctr.get("results") or {}
            summary = results.get("summary") or {}
            total = summary.get("tests", 0)
            passed = summary.get("passed", 0)
            verifier_passed = total > 0 and (passed == total)

            # 提取失败测试名
            tests = results.get("tests") or []
            for t in tests:
                if t.get("status") == "failed":
                    failed_test_names.append(t.get("name", "<unknown>"))

        # 最终 agent message
        final_agent_message = None
        if compacted:
            last_step = compacted[-1]
            final_agent_message = last_step.get("agent_message")

        return TrialOutcome(
            trial_name=trial_name,
            task_name=task_name,
            task_source=task_source,
            verifier_passed=verifier_passed,
            reward=reward,
            exception_type=exception_type,
            exception_message=exception_message,
            failed_test_names=failed_test_names,
            compacted_trajectory=compacted,
            final_agent_message=final_agent_message,
            verifier_feedback=verifier_feedback,
        )


class SkillSnapshotter:
    """
    将共享技能目录打包成快照（tree + 文件内容），用于 patch prompt 输入。
    """

    @staticmethod
    def is_text_file(p: Path) -> bool:
        """判断是否为文本文件（可读）。"""
        # 简单启发式：排除常见二进制后缀
        binary_exts = {
            ".pyc", ".so", ".dylib", ".dll", ".exe", ".bin",
            ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf",
            ".zip", ".tar", ".gz", ".rar",
        }
        if p.suffix.lower() in binary_exts:
            return False
        # 尝试读取前 8KB，检测是否包含 null
        try:
            with open(p, "rb") as f:
                chunk = f.read(8192)
                if b"\x00" in chunk:
                    return False
            return True
        except Exception:
            return False

    @staticmethod
    def snapshot(shared_skills_dir: Path) -> dict[str, Any]:
        """
        返回快照字典：
        {
            "tree": ["skill-foo/SKILL.md", "skill-foo/scripts/bar.py", ...],
            "files": {
                "skill-foo/SKILL.md": "...content...",
                ...
            }
        }
        """
        if not shared_skills_dir.exists():
            return {"tree": [], "files": {}}

        tree: list[str] = []
        files: dict[str, str] = {}

        for p in sorted(shared_skills_dir.rglob("*")):
            if p.is_dir():
                continue
            rel = p.relative_to(shared_skills_dir).as_posix()
            tree.append(rel)
            if SkillSnapshotter.is_text_file(p):
                try:
                    content = p.read_text(encoding="utf-8")
                    files[rel] = content
                except Exception:
                    files[rel] = f"<binary or unreadable: {p.suffix}>"
            else:
                files[rel] = f"<binary: {p.suffix}>"

        return {"tree": tree, "files": files}


class SkillPatchEvolver:
    """
    使用 LLM 根据上一次 trial 的轨迹和完成情况，生成共享技能 patch。
    patch 格式：{
        "summary": "...",
        "upsert_files": {"skill-foo/SKILL.md": "..."},
        "delete_paths": ["skill-bar/SKILL.md"]
    }
    """

    ARTIFACT_PATH = "skillflow-skill/SKILL.md"

    SYSTEM_PROMPT = """You evolve one reusable Skill from completed trial evidence.

The entire learned state must remain in exactly `skillflow-skill/SKILL.md`.
You may replace that file's full contents, but may not create, update, rename, or
delete any other file. Do not emit scripts, references, assets, or a second Skill.

The file must remain a valid Skill: begin with YAML frontmatter containing
`name` and `description`, then provide operational Markdown instructions.
Prefer verifier evidence and concrete execution results over the agent's
self-report. Generalize useful workflows, decision rules, validation steps, and
failure recovery from the trace. Return an empty patch if the evidence does not
justify a reusable change.

Return exactly one JSON object with `summary`, `upsert_files`, and
`delete_paths`. `upsert_files` is either empty or contains only
`skillflow-skill/SKILL.md`; `delete_paths` is always empty."""

    USER_PROMPT_TEMPLATE = """# Single-Skill evolution task

Update only `skillflow-skill/SKILL.md`.

## Current artifact tree
{tree_json}

## Current artifact contents
{files_block}

## Trial evidence
- Task: {task_name}
- Family: {task_source}
- Verifier passed: {verifier_passed}
- Reward: {reward}
- Exception: {exception_info}
- Failed tests: {failed_tests}

## Final agent message
{final_message}

## Compacted execution trace
{trajectory_json}

Return exactly this JSON shape and no surrounding prose:

```json
{{
  "summary": "brief evidence-based rationale",
  "upsert_files": {{
    "skillflow-skill/SKILL.md": "---\nname: skillflow-skill\ndescription: reusable guidance and when to use it\n---\n\n# SkillFlow Skill\n..."
  }},
  "delete_paths": []
}}
```
"""

    def __init__(
        self,
        model_name: str,
        api_base: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 8192,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.model_name = model_name
        self.api_base = api_base
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_headers = extra_headers or {}

    def _constrain_to_artifact(self, patch: SkillPatchResult) -> SkillPatchResult:
        """Reject a patch that attempts to mutate anything except ARTIFACT_PATH."""
        invalid_paths = sorted(set(patch.upsert_files) - {self.ARTIFACT_PATH})
        if patch.delete_paths or invalid_paths:
            reasons: list[str] = []
            if invalid_paths:
                reasons.append(f"unexpected paths: {', '.join(invalid_paths)}")
            if patch.delete_paths:
                reasons.append("deletions are not permitted")
            return SkillPatchResult(
                summary=f"Rejected out-of-scope patch ({'; '.join(reasons)}). {patch.summary}",
                upsert_files={},
                delete_paths=[],
                attempt_count=patch.attempt_count,
                attempt_modes=patch.attempt_modes,
                successful_attempt=patch.successful_attempt,
                successful_prompt_mode=patch.successful_prompt_mode,
                successful_attempt_kind=patch.successful_attempt_kind,
            )

        artifact = patch.upsert_files.get(self.ARTIFACT_PATH)
        return SkillPatchResult(
            summary=patch.summary,
            upsert_files={self.ARTIFACT_PATH: artifact} if artifact is not None else {},
            delete_paths=[],
            attempt_count=patch.attempt_count,
            attempt_modes=patch.attempt_modes,
            successful_attempt=patch.successful_attempt,
            successful_prompt_mode=patch.successful_prompt_mode,
            successful_attempt_kind=patch.successful_attempt_kind,
        )

    @staticmethod
    def _strip_json_code_fence(text: str) -> str:
        stripped = text.strip()
        if not stripped.startswith("```"):
            return stripped

        lines = stripped.splitlines()
        if lines and lines[0].lstrip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()

    @staticmethod
    def _extract_json_object_candidates(text: str) -> list[str]:
        candidates: list[str] = []
        for start, ch in enumerate(text):
            if ch != "{":
                continue

            depth = 0
            in_string = False
            escape_next = False

            for end in range(start, len(text)):
                char = text[end]

                if escape_next:
                    escape_next = False
                    continue
                if char == "\\":
                    escape_next = True
                    continue
                if char == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue

                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        candidates.append(text[start : end + 1])
                        break

        return candidates

    @staticmethod
    def _is_openai_native_endpoint(api_base: str | None) -> bool:
        if not api_base:
            return False
        normalized = api_base.rstrip("/").lower()
        return normalized.endswith("/v1/openai/native")

    @staticmethod
    def _build_openai_native_chat_url(api_base: str) -> str:
        return api_base.rstrip("/") + "/chat/completions"

    @staticmethod
    def _strip_provider_prefix(model_name: str) -> str:
        normalized = model_name.strip()
        if "/" not in normalized:
            return normalized
        provider, rest = normalized.split("/", 1)
        if provider.lower() in {"openai", "anthropic", "gemini"} and rest:
            return rest
        return normalized

    def _call_openai_native_http(
        self,
        *,
        prompt: str,
        message_history: list[dict[str, str]],
        max_tokens: int,
    ) -> str:
        if not self.api_base:
            raise ValueError("api_base is required for native OpenAI HTTP calls")
        if not self.api_key:
            raise ValueError("api_key is required for native OpenAI HTTP calls")

        url = self._build_openai_native_chat_url(self.api_base)
        messages = message_history + [{"role": "user", "content": prompt}]
        payload = {
            "model": self._strip_provider_prefix(self.model_name),
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": self.temperature,
        }
        request_payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        for key, value in self.extra_headers.items():
            headers[key] = value

        request_log = {
            "transport": "openai_native_http",
            "url": url,
            "model": payload["model"],
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": self.temperature,
            "headers": {k: ("<redacted>" if k.lower() == "authorization" else v) for k, v in headers.items()},
        }

        req = urllib.request.Request(url, data=request_payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                raw_body = resp.read().decode("utf-8")
                status_code = resp.getcode()
        except urllib.error.HTTPError as exc:
            raw_body = exc.read().decode("utf-8", errors="replace")
            error_log = request_log | {
                "status_code": exc.code,
                "response_text": raw_body,
                "error": str(exc),
            }
            raise RuntimeError(f"HTTP {exc.code}: {raw_body[:500]}") from exc
        except Exception:
            raise

        data = json.loads(raw_body)
        choices = data.get("choices") or []
        if not choices:
            raise ValueError(f"Native OpenAI response has no choices: {raw_body[:500]}")
        first_choice = choices[0]
        message = first_choice.get("message") or {}
        finish_reason = first_choice.get("finish_reason")
        content = message.get("content")
        if finish_reason == "length":
            raise RuntimeError("Model hit max_tokens limit. Response was truncated.")
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"Native OpenAI response content is empty: {raw_body[:500]}")
        return content

    @classmethod
    def _parse_patch_response(cls, content: str) -> dict[str, Any]:
        required_keys = {"summary", "upsert_files", "delete_paths"}
        attempts: list[str] = []
        stripped = content.strip()
        if stripped:
            attempts.append(stripped)
            unwrapped = cls._strip_json_code_fence(stripped)
            if unwrapped != stripped:
                attempts.append(unwrapped)

        best_data: dict[str, Any] | None = None
        best_score: tuple[int, int] | None = None
        last_error: Exception | None = None

        for text in attempts:
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    return data
            except Exception as exc:
                last_error = exc

            for candidate in cls._extract_json_object_candidates(text):
                try:
                    data = json.loads(candidate)
                except Exception as exc:
                    last_error = exc
                    continue

                if not isinstance(data, dict):
                    continue

                score = (len(required_keys & set(data.keys())), len(candidate))
                if score[0] == 0:
                    continue
                if best_score is None or score > best_score:
                    best_score = score
                    best_data = data

        if best_data is not None:
            return best_data
        if last_error is not None:
            raise last_error
        raise ValueError("No valid JSON object found in patch response")

    def _build_user_prompt(
        self,
        snapshot: dict[str, Any],
        outcome: TrialOutcome,
        *,
        compact_mode: bool = False,
    ) -> str:
        tree_json = json.dumps(snapshot.get("tree", []), ensure_ascii=False, indent=2)
        files_block = ""
        files = snapshot.get("files", {})
        file_items = list(files.items())
        if compact_mode:
            file_items = file_items[:8]
        if file_items:
            for rel, content in file_items:
                rendered = content
                if compact_mode and len(rendered) > 4000:
                    rendered = rendered[:4000] + "\n...<truncated>"
                files_block += f"\n### {rel}\n```\n{rendered}\n```\n"
        else:
            files_block = "<empty library>"

        trajectory_steps = outcome.compacted_trajectory
        if compact_mode and len(trajectory_steps) > 8:
            trajectory_steps = trajectory_steps[:2] + trajectory_steps[-6:]
        trajectory_json = json.dumps(
            trajectory_steps,
            ensure_ascii=False,
            indent=2,
        )
        if compact_mode and len(trajectory_json) > 12000:
            trajectory_json = trajectory_json[:12000] + "\n...<truncated>"

        final_message = outcome.final_agent_message or "<none>"
        if compact_mode and len(final_message) > 2000:
            final_message = final_message[:2000] + "\n...<truncated>"

        verifier_feedback = outcome.verifier_feedback or "<none>"
        if compact_mode and len(verifier_feedback) > 6000:
            verifier_feedback = "...<truncated to actionable tail>\n" + verifier_feedback[-6000:]

        exception_info = "None"
        if outcome.exception_type:
            exception_info = f"{outcome.exception_type}: {outcome.exception_message}"

        return self.USER_PROMPT_TEMPLATE.format(
            tree_json=tree_json,
            files_block=files_block,
            task_name=outcome.task_name,
            task_source=outcome.task_source,
            verifier_passed=outcome.verifier_passed,
            reward=outcome.reward,
            exception_info=exception_info,
            failed_tests=json.dumps(outcome.failed_test_names, ensure_ascii=False),
            verifier_feedback=verifier_feedback,
            trajectory_json=trajectory_json,
            final_message=final_message,
        )

    def generate_patch(
        self,
        snapshot: dict[str, Any],
        outcome: TrialOutcome,
        max_parse_retries: int = 3,
    ) -> SkillPatchResult:
        """
        调用 LLM 生成 patch，返回 SkillPatchResult。
        若解析失败，使用相同 prompt 最多额外重试 max_parse_retries 次。
        """
        user_prompt = self._build_user_prompt(snapshot, outcome)
        fallback_prompt = self._build_user_prompt(snapshot, outcome, compact_mode=True)

        use_native_openai_http = self._is_openai_native_endpoint(self.api_base)

        if not use_native_openai_http and LiteLLM is None:
            return SkillPatchResult(
                summary="LiteLLM not available. Please install litellm and ensure libs.terminus_agent is importable.",
                upsert_files={},
                delete_paths=[],
                attempt_count=0,
                attempt_modes=[],
            )

        llm = None
        if not use_native_openai_http:
            llm = LiteLLM(
                model_name=self.model_name,
                temperature=self.temperature,
                api_base=self.api_base,
                api_key=self.api_key,
            )

        message_history: list[dict[str, str]] = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]
        last_content: str | None = None
        last_error: Exception | None = None
        total_attempts = max_parse_retries + 1
        attempt_count = 0
        attempt_modes: list[str] = []

        for _ in range(total_attempts):
            # 调用 LLM；解析失败时直接用相同 prompt 重试
            current_prompt_mode = "full"
            current_attempt_kind = "primary"
            try:
                call_kwargs: dict[str, Any] = {"max_tokens": self.max_tokens}
                if self.extra_headers:
                    call_kwargs["extra_headers"] = self.extra_headers

                attempt_count += 1
                attempt_modes.append(current_prompt_mode)
                if use_native_openai_http:
                    content = self._call_openai_native_http(
                        prompt=user_prompt,
                        message_history=message_history.copy(),
                        max_tokens=call_kwargs["max_tokens"],
                    )
                else:
                    content = llm.call(
                        prompt=user_prompt,
                        message_history=message_history.copy(),
                        **call_kwargs,
                    )
            except Exception as e:
                error_message = str(e)
                last_attempt_obj = getattr(e, "last_attempt", None)
                inner = None
                if last_attempt_obj is not None:
                    try:
                        inner = last_attempt_obj.exception()
                    except Exception:
                        inner = None
                    if inner is not None:
                        error_message = f"{error_message}; inner={inner}"

                lowered = error_message.lower()
                is_connection_like = any(
                    marker in lowered
                    for marker in (
                        "connection error",
                        "internalservererror",
                        "retryerror",
                        "apiconnectionerror",
                        "connection refused",
                        "timed out",
                        "timeout",
                    )
                )
                if is_connection_like:
                    try:
                        time.sleep(2)
                        retry_kwargs: dict[str, Any] = {"max_tokens": self.max_tokens}
                        if self.extra_headers:
                            retry_kwargs["extra_headers"] = self.extra_headers
                        current_prompt_mode = "compact"
                        current_attempt_kind = "fallback"
                        attempt_count += 1
                        attempt_modes.append(current_prompt_mode)
                        if use_native_openai_http:
                            content = self._call_openai_native_http(
                                prompt=fallback_prompt,
                                message_history=message_history.copy(),
                                max_tokens=retry_kwargs["max_tokens"],
                            )
                        else:
                            content = llm.call(
                                prompt=fallback_prompt,
                                message_history=message_history.copy(),
                                **retry_kwargs,
                            )
                    except Exception as retry_exc:
                        retry_error_message = str(retry_exc)
                        retry_attempt = getattr(retry_exc, "last_attempt", None)
                        if retry_attempt is not None:
                            try:
                                retry_inner = retry_attempt.exception()
                            except Exception:
                                retry_inner = None
                            if retry_inner is not None:
                                retry_error_message = f"{retry_error_message}; inner={retry_inner}"
                        return SkillPatchResult(
                            summary=(
                                f"LLM call failed: {error_message}. "
                                f"Fallback retry also failed: {retry_error_message}. "
                                f"Current patch max_tokens={self.max_tokens}; "
                                "if this is an output truncation, try increasing --patch-max-tokens."
                            ),
                            upsert_files={},
                            delete_paths=[],
                            attempt_count=attempt_count,
                            attempt_modes=attempt_modes,
                        )
                else:
                    return SkillPatchResult(
                        summary=(
                            f"LLM call failed: {error_message}. "
                            f"Current patch max_tokens={self.max_tokens}; "
                            "if this is an output truncation, try increasing --patch-max-tokens."
                        ),
                        upsert_files={},
                        delete_paths=[],
                        attempt_count=attempt_count,
                        attempt_modes=attempt_modes,
                    )

            last_content = content

            # 尝试解析 JSON
            try:
                data = self._parse_patch_response(content)
                summary = data.get("summary", "")
                if not isinstance(summary, str):
                    summary = str(summary)

                raw_upsert_files = data.get("upsert_files") or {}
                upsert_files = {}
                if isinstance(raw_upsert_files, dict):
                    upsert_files = {
                        str(path): value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
                        for path, value in raw_upsert_files.items()
                    }

                raw_delete_paths = data.get("delete_paths") or []
                delete_paths = []
                if isinstance(raw_delete_paths, list):
                    delete_paths = [str(path) for path in raw_delete_paths]

                return self._constrain_to_artifact(
                    SkillPatchResult(
                        summary=summary,
                        upsert_files=upsert_files,
                        delete_paths=delete_paths,
                        attempt_count=attempt_count,
                        attempt_modes=attempt_modes,
                        successful_attempt=attempt_count,
                        successful_prompt_mode=current_prompt_mode,
                        successful_attempt_kind=current_attempt_kind,
                    )
                )
            except Exception as e:
                last_error = e

        # 所有重试都失败
        raw_preview = last_content[:500] if last_content else "<no response>"
        return SkillPatchResult(
            summary=f"JSON parse failed after {max_parse_retries} retries: {last_error}\nRaw: {raw_preview}",
            upsert_files={},
            delete_paths=[],
            attempt_count=attempt_count,
            attempt_modes=attempt_modes,
        )

    @staticmethod
    def apply_patch(
        shared_skills_dir: Path,
        patch: SkillPatchResult,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        将 patch 应用到共享技能目录。
        返回操作记录 dict。
        """
        applied: dict[str, Any] = {
            "deleted": [],
            "upserted": [],
            "errors": [],
        }

        if dry_run:
            applied["dry_run"] = True
            return applied

        # 删除
        for rel in patch.delete_paths:
            target = shared_skills_dir / rel
            if target.exists():
                try:
                    if target.is_file():
                        target.unlink()
                    else:
                        shutil.rmtree(target)
                    applied["deleted"].append(rel)
                except Exception as e:
                    applied["errors"].append(f"delete {rel}: {e}")

        # 新增/更新
        for rel, content in patch.upsert_files.items():
            target = shared_skills_dir / rel
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                applied["upserted"].append(rel)
            except Exception as e:
                applied["errors"].append(f"upsert {rel}: {e}")

        return applied
