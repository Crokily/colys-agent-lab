---
name: search-sessions
description: Search and summarize local JSONL session history for coding agents such as Claude Code, OpenAI Codex CLI, and Pi. Use when a user wants to find a past agent conversation, inspect session.jsonl/history.jsonl files, filter noisy system/thinking/tool output, group results by session, or generate commands to resume a matching session.
---

# Search Sessions

## Overview

Use this skill to locate useful past agent sessions without loading huge transcripts into context. Prefer the bundled scanner because it streams JSONL, filters common noise, aggregates by session, and prints resume commands.

## Quick Start

Run the scanner from the skill directory:

```bash
python3 scripts/search_sessions.py "auth refactor"
```

Common options:

```bash
python3 scripts/search_sessions.py --agents claude,codex --limit 10 "migration"
python3 scripts/search_sessions.py --root /path/to/export --no-default-roots "bug"
python3 scripts/search_sessions.py --json "database schema"
```

When there is no query, the script lists recent sessions. It reports the agent, time, cwd, snippets, source file, and a resume command when the agent supports direct resume.

## Workflow

1. Run `scripts/search_sessions.py` with the user's query. Use `--no-default-roots --root <dir>` when the user points at an exported folder or when you must avoid scanning the home directories.
2. Read the top few snippets and resume command. Do not paste whole transcript content back to the user unless they explicitly ask for it.
3. If the parser misses a newer agent format, read `references/agent-session-formats.md`, inspect a few JSONL lines, then patch the script's extractor for that agent.

## Noise Policy

The scanner intentionally excludes system/developer messages, thinking blocks, tool result bodies, shell output, images, and common injected context such as AGENTS.md/environment blocks. It may keep short command names or user/assistant text because those often identify the task.

## References

Read `references/agent-session-formats.md` when you need the current path conventions, resume commands, or supported JSONL fields for Claude Code, Codex CLI, and Pi.
