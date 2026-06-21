# Agent Session Formats

Use this as a compact map for the bundled `scripts/search_sessions.py` parser. Treat paths as defaults, not as a promise: users can override roots or config dirs.

## Claude Code

Source: <https://code.claude.com/docs/en/sessions>

- Default transcript storage: `~/.claude/projects/<project>/<session-id>.jsonl`.
- Override config root with `CLAUDE_CONFIG_DIR`.
- Full transcripts are JSONL lines for messages, tool use, and metadata.
- Resume commands:
  - `claude --continue` resumes the most recent session in the current directory.
  - `claude --resume` opens the picker.
  - `claude --resume <session-id-or-name>` resumes a specific session. Run it from the original project directory when possible.
- Useful fields seen in project JSONL: `sessionId`, `timestamp`, `cwd`, top-level `type`, `customTitle`, `agentName`, and `message.role/content`.
- `~/.claude/history.jsonl` is command/prompt history. It can help find a `sessionId` but is less complete than the project transcript.

## OpenAI Codex CLI

Sources:

- <https://developers.openai.com/codex/cli/reference>
- Local `codex resume --help` and `codex exec resume --help` from Codex CLI 0.141.0.
- OpenAI Codex repository issues/discussions often mention the implementation path: <https://github.com/openai/codex>

Facts to rely on:

- Default config root is `$CODEX_HOME`, or `~/.codex` when unset.
- Official CLI reference lists `codex resume` as the stable command for continuing previous interactive sessions.
- Current CLI help accepts `codex resume [SESSION_ID] [PROMPT]`, `codex resume --last`, `codex resume --all`, and `codex exec resume [SESSION_ID] [PROMPT]`.
- Current local session files are JSONL rollouts under `$CODEX_HOME/sessions/YYYY/MM/DD/rollout-*.jsonl`.
- `$CODEX_HOME/history.jsonl` stores prompt history keyed by `session_id`.
- Useful rollout fields: `type=session_meta` with `payload.id/cwd/timestamp`, `type=turn_context` with `payload.cwd`, `type=response_item` with `payload.role/content`, and `type=event_msg` with `payload.user_message` or `payload.agent_message`.
- Resume command: prefer `cd <cwd> && codex resume <session-id>` for interactive sessions.

## Pi Coding Agent

Sources:

- <https://pi.dev/docs/latest/sessions>
- <https://pi.dev/docs/latest/session-format>

Facts to rely on:

- Default session storage: `~/.pi/agent/sessions/--<path>--/<timestamp>_<uuid>.jsonl`.
- Override config root with `PI_CODING_AGENT_DIR`; override session root with `PI_CODING_AGENT_SESSION_DIR` or `pi --session-dir`.
- Sessions are JSONL. The first line is a session header with `type=session`, `version`, `id`, `timestamp`, and `cwd`.
- Entries form a tree with `id` and `parentId`.
- Resume commands:
  - `pi -c` continues the most recent session.
  - `pi -r` opens the session picker.
  - `pi --session <path|id>` opens a specific session file or partial ID.
  - `pi --fork <path|id>` forks a previous session.
- Useful message fields: `type=message`, `message.role`, `message.content`, and timestamp fields on both entries and messages.

## Generic JSONL Fallback

For unknown agents or exported folders, scan `*.jsonl`, `session.jsonl`, and `history.jsonl` files and infer sessions from common keys: `session_id`, `sessionId`, `thread_id`, `id`, `cwd`, `project`, `timestamp`, `ts`, `role`, `content`, `message`, and `text`.
