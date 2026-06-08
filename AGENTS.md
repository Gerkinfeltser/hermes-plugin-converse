# AGENTS.md

This repository contains `hermes-plugin-converse`, a small standalone Python plugin for Hermes Agent. Agents working here MUST preserve the plugin's core purpose: let users scope work in a conversation-only mode, block tools while that mode is active, and hand execution back to Hermes with `/go`.

## Repository Shape

- `__init__.py` is the plugin entry point and contains command handlers, hook handlers, registration, and in-memory session state.
- `plugin.yaml` is the Hermes plugin manifest. It MUST stay aligned with the hooks and commands registered in `__init__.py`.
- `README.md` is user-facing documentation for installation, usage, behavior, and limitations.
- `assets/demo.py` generates the demo terminal recording used by `assets/converse-demo.gif`.
- `assets/*.cast` files are ignored and SHOULD NOT be committed.

## Development Commands

Use Python 3. The repo has no package manager metadata and no third-party runtime dependencies.

```bash
python3 -m py_compile __init__.py assets/demo.py
```

Run this before claiming Python changes are valid. It is the current baseline syntax check.

```bash
python3 assets/demo.py
```

Run this when changing the demo script. It previews the deterministic terminal animation.

```bash
hermes plugins enable converse
```

Use this from an installed plugin environment when manually testing Hermes integration.

## Manual Test Flow

After changing plugin behavior, agents SHOULD verify the intended Hermes flow when the host environment is available:

1. Enable the plugin in Hermes.
2. Start or restart a Hermes CLI session.
3. Run `/converse` and confirm it reports conversation-only mode is on.
4. Send a normal prompt and confirm tool calls are blocked while the mode is on.
5. Run `/converse status` and confirm it reports `ON`.
6. Run `/converse off` and confirm it exits without triggering execution.
7. Run `/converse`, then `/go`, and confirm the plugin injects the execution prompt in CLI mode.

If Hermes is not available, agents MUST state that only static validation was performed.

## Plugin Contracts

- `/converse` MUST enable conversation-only mode for the current session when called with no arguments.
- `/converse on`, `/converse start`, `/converse enable`, `/converse 1`, and `/converse true` MUST enable the mode.
- `/converse off`, `/converse stop`, `/converse disable`, `/converse 0`, `/converse false`, and `/converse cancel` MUST disable the mode without execution.
- `/converse status` and `/converse ?` MUST report whether the current session is enabled.
- `/go` MUST disable converse mode and inject the execution handoff prompt when `PluginContext.inject_message` is available.
- `/go` MUST return a clear manual fallback message when injection is unavailable, especially for gateway sessions.
- `pre_llm_call` MUST inject guidance only for sessions with converse mode enabled.
- `pre_tool_call` MUST block all tools only for sessions with converse mode enabled.
- Session state MUST remain keyed by `session_id`; missing session IDs SHOULD continue to use the `_default` fallback.

## Code Style

- Code MUST remain standard-library-only unless a dependency is clearly justified and documented.
- Python files MUST use `from __future__ import annotations` when type hints rely on postponed evaluation or when matching existing module style.
- Command handlers SHOULD return short, user-facing strings with the existing lowercase `converse:` prefix.
- Hook handlers MUST return `None` when they do not intend to modify Hermes behavior.
- Shared prompt text SHOULD stay in module-level constants with leading underscores.
- Mutable process state MUST stay protected by `_lock`.
- Types SHOULD use precise standard-library annotations such as `Optional[Any]` and `set[str]` rather than broad untyped state.
- Agents SHOULD keep changes small and local; this plugin is intentionally a single-file implementation.

## Behavior Guidelines

- The plugin MUST fail safe. If injection fails, it SHOULD tell the user what happened rather than silently doing nothing.
- Converse mode MUST block tools defensively even if the model ignores the prompt addendum.
- The prompt addendum MUST keep the user in a scoping conversation and MUST ask the model to end with `Plan so far:`.
- `/go` MUST carry forward the prior conversation and any optional user notes.
- Gateway limitations MUST remain documented because `inject_message` is CLI-only.
- Do not add persistent storage unless the README and plugin behavior are updated together.

## Documentation Rules

- README changes MUST stay consistent with `plugin.yaml` and command behavior in `__init__.py`.
- User-facing examples SHOULD use `/converse`, `/go`, and the existing lowercase explanatory voice.
- Limits and comparison sections SHOULD be updated when behavior changes, not left stale.
- If adding commands or hook behavior, update both `README.md` and this file.

## Demo Asset Workflow

`assets/demo.py` is deterministic and seeds `random` so the preview is repeatable. If changing the scripted interaction, preserve that deterministic behavior.

To regenerate the cast and GIF when the required tools are installed:

```bash
asciinema rec assets/demo.cast --command "python3 assets/demo.py" --overwrite
agg assets/demo.cast assets/converse-demo.gif --speed 1.0
```

The generated `assets/demo.cast` SHOULD remain untracked because `.gitignore` excludes `assets/*.cast`. The GIF MAY be updated when the visible workflow changes.

## Safety Notes

- Do not remove the tool-blocking hook unless replacing it with an equivalent hard block.
- Do not make `/go` execute tools directly inside the plugin; it SHOULD inject a user message and let Hermes handle execution.
- Do not broaden state from per-session to global-only behavior.
- Do not introduce network calls, subprocess execution, or file writes in the plugin runtime without an explicit design decision.
