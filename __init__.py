"""converse — conversation-first hermes mode; no tool calls until /go.

Pattern:
  /converse      turn converse mode ON for this session
  ... talk through requirements, scope, decisions ...
  /go [notes]    turn converse OFF and execute the plan we discussed

While ON:
  * pre_llm_call injects a prompt addendum: don't call tools, ask
    clarifying questions, end each reply with a "Plan so far:" recap.
  * pre_tool_call defensively blocks every tool with a clear message,
    so even a model that ignores the addendum cannot run anything.

CLI-only: /go uses PluginContext.inject_message which is unavailable
in gateway sessions (Telegram/Discord/etc.).
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Optional

logger = logging.getLogger(__name__)

_CONVERSE_ADDENDUM = (
    "[CONVERSE MODE is ON]\n"
    "You are scoping a project with the user. Do NOT call any tools this turn. "
    "Your job is to:\n"
    "  1. Ask clarifying questions when requirements are vague.\n"
    "  2. Surface tradeoffs, risks, and edge cases the user may not have considered.\n"
    "  3. Push back honestly. If a requirement seems wrong, say so.\n"
    "  4. Never assume scope. Confirm it.\n\n"
    "End every reply with a section titled 'Plan so far:' containing the current "
    "best-understanding of: GOAL, IN SCOPE, OUT OF SCOPE, OPEN QUESTIONS, and "
    "NEXT STEPS. Update it each turn so the user can see the plan converging.\n\n"
    "The user will type /go when they are ready to execute. Until then, no tools."
)

_BLOCK_MESSAGE = (
    "Converse mode is ON. Tool calls are blocked. Continue the scoping conversation. "
    "The user will type /go when they want execution to start."
)

_GO_PROMPT = (
    "[converse: GO] Converse mode is now off. Execute the plan we converged on above. "
    "Use every requirement, decision, and constraint we discussed. Run all the tools "
    "needed to deliver it. Do not re-ask clarifying questions unless something is "
    "genuinely ambiguous after the conversation above.\n\n"
    "{extra_notes}"
)

_lock = threading.Lock()
_enabled_sessions: set[str] = set()
_gateway_to_agent: dict[str, str] = {}
_ctx_ref: Optional[Any] = None


# ---------------------------------------------------------------------------
# Slash commands
# ---------------------------------------------------------------------------

def _handle_converse(raw_args: str, **kwargs) -> str:
    session_id = kwargs.get("session_id") or "_default"
    arg = (raw_args or "").strip().lower()

    with _lock:
        if arg in {"", "on", "start", "enable", "1", "true"}:
            _enabled_sessions.add(session_id)
            return (
                "converse: ON. i'll discuss only, no tools. "
                "talk through what you want; type /go when ready to execute."
            )
        if arg in {"off", "stop", "disable", "0", "false", "cancel"}:
            _enabled_sessions.discard(session_id)
            agent_sid = _gateway_to_agent.pop(session_id, None)
            if agent_sid:
                _enabled_sessions.discard(agent_sid)
            return "converse: OFF (no execution triggered)"
        if arg in {"status", "?"}:
            on = session_id in _enabled_sessions
            if not on:
                agent_sid = _gateway_to_agent.get(session_id)
                on = agent_sid is not None and agent_sid in _enabled_sessions
            return f"converse: {'ON' if on else 'OFF'}"

    return f"unknown: {arg}\nUsage: /converse [on|off|status]"


def _handle_go(raw_args: str, **kwargs) -> str:
    session_id = kwargs.get("session_id") or "_default"
    extra = (raw_args or "").strip()

    with _lock:
        was_on = session_id in _enabled_sessions
        _enabled_sessions.discard(session_id)
        agent_sid = _gateway_to_agent.pop(session_id, None)
        if agent_sid:
            was_on = was_on or agent_sid in _enabled_sessions
            _enabled_sessions.discard(agent_sid)

    if _ctx_ref is None:
        return "converse: cannot inject (no plugin context). type your execute message manually."

    extra_block = f"Extra instructions from user: {extra}" if extra else ""
    prompt = _GO_PROMPT.format(extra_notes=extra_block).rstrip()

    if _ctx_ref is not None:
        try:
            ok = _ctx_ref.inject_message(prompt, role="user")
            if ok:
                state = "off, executing" if was_on else "wasn't on, executing anyway"
                return f"converse: {state}."
        except Exception as exc:
            logger.warning("converse: inject_message failed: %s", exc)

    state = "off" if was_on else "wasn't on"
    return (
        f"converse: {state}. converse mode is disabled — "
        "tools are unblocked. send your next message to execute."
    )


# ---------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------

def _on_pre_llm_call(*, session_id: str = "", gateway_session_key: str = "", **_: Any):
    sid = session_id or "_default"
    with _lock:
        if sid not in _enabled_sessions:
            if gateway_session_key and gateway_session_key in _enabled_sessions:
                _enabled_sessions.add(sid)
                _gateway_to_agent[gateway_session_key] = sid
            else:
                return None
    return {"context": _CONVERSE_ADDENDUM}


def _on_pre_tool_call(*, tool_name: str = "", session_id: str = "", gateway_session_key: str = "", **_: Any):
    sid = session_id or "_default"
    with _lock:
        if sid not in _enabled_sessions:
            if gateway_session_key and gateway_session_key in _enabled_sessions:
                _enabled_sessions.add(sid)
                _gateway_to_agent[gateway_session_key] = sid
            else:
                return None
    return {"action": "block", "message": _BLOCK_MESSAGE}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    global _ctx_ref
    _ctx_ref = ctx

    ctx.register_hook("pre_llm_call", _on_pre_llm_call)
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
    ctx.register_command(
        "converse",
        handler=_handle_converse,
        description="Converse mode: conversation only, no tool calls until /go.",
        args_hint="on|off|status",
    )
    ctx.register_command(
        "go",
        handler=_handle_go,
        description="Exit converse mode and execute the plan we just discussed.",
        args_hint="[extra notes]",
    )
