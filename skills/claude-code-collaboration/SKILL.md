---
name: claude-code-collaboration
description: "Delegate coding, review, debugging, refactoring, test generation, and repository analysis from Pi to local Claude Code CLI in headless/non-interactive mode with final-result-only logs and subscription-login billing guardrails. Use when Pi should offload software engineering work to Claude Code or compare results without leaking process logs into context."
---

# Claude Code Collaboration Guide

## Mission

Use the local `claude` CLI as a subordinate coding agent. Pi should package the task, run Claude Code in headless mode, then consume only Claude Code's final answer.

## Mandatory Rules

1. **Use subscription login by default**: prefer the user's Claude Pro/Max/Team/Enterprise login (`claude.ai`). In non-interactive mode, `ANTHROPIC_API_KEY` overrides subscription auth, so strip it from the Claude child process unless the user explicitly authorizes API-key billing for the current run.
2. **Preflight auth without a model prompt**: run `env -u ANTHROPIC_API_KEY claude auth status` before delegation. Continue only when it reports subscription/`claude.ai` auth. If login is missing, invalid, API-key based, or requires API-key billing, stop and ask the user to run `claude auth login`.
3. **Use headless mode**: run `claude -p` / `claude --print`; do not open the interactive Claude Code TUI for normal delegation. Do not use `--bare` for subscription-only delegation because it does not read OAuth/keychain subscription auth.
4. **Keep context clean**: redirect Claude Code stdout/stderr to files. Do not paste streaming logs or tool chatter into Pi's conversation.
5. **Prefer JSON output**: use `--output-format json` and extract `.result` as the final response.
6. **Set explicit permissions**:
   - Read-only analysis/review: restrict tools with `--allowedTools "Read,Grep,Glob"` when appropriate.
   - Code-changing tasks: start with `--permission-mode acceptEdits`.
   - Use `--permission-mode bypassPermissions` only in isolated/hardened workspaces.
7. **Verify after delegation**: run relevant tests/lints/builds in Pi after Claude Code finishes; do not trust final text alone.

## Canonical Execution Pattern

Prefer the bundled wrapper because it captures raw JSON, stderr logs, and final text separately:

```bash
SKILL_DIR="$HOME/.pi/agent/skills/claude-code-collaboration"
PROMPT_FILE=$(mktemp /tmp/claude-code-prompt.XXXXXX.md)
RESULT_FILE=$(mktemp /tmp/claude-code-result.XXXXXX.txt)
JSON_FILE=$(mktemp /tmp/claude-code-result.XXXXXX.json)
LOG_FILE=$(mktemp /tmp/claude-code-run.XXXXXX.log)

cat > "$PROMPT_FILE" <<'EOF'
Task:
[clear objective]

Repository context:
- Working directory: [absolute path]
- Relevant files: [paths]

Requirements:
1. ...

Validation:
- Run: [test/lint/build commands]

Deliverables:
- Modified files list
- Summary of changes
- Validation results
EOF

"$SKILL_DIR/scripts/run-claude-code.sh" \
  --cwd "$PWD" \
  --prompt-file "$PROMPT_FILE" \
  --result-file "$RESULT_FILE" \
  --json-file "$JSON_FILE" \
  --log-file "$LOG_FILE" \
  --permission-mode acceptEdits

# The wrapper strips ANTHROPIC_API_KEY and checks subscription auth by default.
# On success, read only $RESULT_FILE. Inspect $LOG_FILE only on failure.
```

Direct CLI fallback:

```bash
AUTH_LOG=$(mktemp /tmp/claude-code-auth.XXXXXX.log)
if ! env -u ANTHROPIC_API_KEY claude auth status > "$AUTH_LOG" 2>&1; then
  echo "Claude subscription login unavailable; ask user to run: claude auth login" >&2
  exit 125
fi
# Confirm $AUTH_LOG reports subscription/claude.ai auth, not API-key auth.

env -u ANTHROPIC_API_KEY claude -p "$(cat "$PROMPT_FILE")" \
  --output-format json \
  --permission-mode acceptEdits \
  > "$JSON_FILE" 2> "$LOG_FILE"
python3 - <<'PY' "$JSON_FILE" > "$RESULT_FILE"
import json, sys
print(json.load(open(sys.argv[1])).get('result', ''))
PY
```

## Delegation Workflow

1. **Identify suitable work**: implementation, refactoring, bug fixing, test writing, repository review, architecture analysis, migration planning.
2. **Write a complete prompt file** with objective, relevant paths, constraints, expected output, and validation commands.
3. **Run Claude Code headlessly** with the wrapper; it performs the subscription preflight and strips `ANTHROPIC_API_KEY` unless the user explicitly authorized API-key billing.
4. **Consume only the final result file** on success. On failure, summarize the exit code and a small diagnostic snippet from the log.
5. **Integrate and verify in Pi**: inspect changed files, run tests/lints, fix issues directly or delegate a follow-up prompt.

## Common Modes

### Read-only review

```bash
"$SKILL_DIR/scripts/run-claude-code.sh" \
  --cwd "$PWD" \
  --prompt-file "$PROMPT_FILE" \
  --result-file "$RESULT_FILE" \
  --log-file "$LOG_FILE" \
  --allowed-tools "Read,Grep,Glob"
```

### Code-changing task

```bash
"$SKILL_DIR/scripts/run-claude-code.sh" \
  --cwd "$PWD" \
  --prompt-file "$PROMPT_FILE" \
  --result-file "$RESULT_FILE" \
  --log-file "$LOG_FILE" \
  --permission-mode acceptEdits
```

### Isolated sandbox / disposable runner

```bash
"$SKILL_DIR/scripts/run-claude-code.sh" \
  --cwd "$PWD" \
  --prompt-file "$PROMPT_FILE" \
  --result-file "$RESULT_FILE" \
  --log-file "$LOG_FILE" \
  --permission-mode bypassPermissions
```

### Explicit API-key billing

Only when the user explicitly authorizes API-key billing for the current run, pass `--allow-api-key-billing` to the wrapper. Do not suggest this as a fallback when subscription login fails.

## Prompt Template

```text
Task:
[one clear goal]

Repository context:
- Working directory: /absolute/path
- Relevant files/directories:
  - path/a
  - path/b

Requirements:
1. ...
2. ...

Constraints:
- Do not ...
- Preserve ...

Validation:
- Run: npm test / pytest / go test ./... / etc.
- Expected: ...

Deliverables:
- Files changed
- What changed and why
- Validation commands and outcomes
- Any risks or follow-ups
```

## Communication Policy

Before delegation, say briefly: "我会先检查 Claude 订阅登录状态，然后用本地 Claude Code 的 headless 模式执行，并只读取最终结果；不会自动改用 API key。"

After success, report:
- Claude Code's concise final summary
- files changed
- validation status
- any follow-up needed

After failure, report:
- exit code
- short log excerpt or high-level cause
- subscription/auth problem if detected; ask the user to run `claude auth login` and do not retry with API keys
- retry plan

## Anti-Patterns

- Running interactive `claude` TUI for normal Pi delegation
- Streaming Claude Code logs directly into Pi context
- Using `bypassPermissions` outside an isolated workspace
- Using `--bare` for subscription-login delegation
- Letting `ANTHROPIC_API_KEY` silently override the user's subscription login
- Suggesting API-key billing as a fallback when subscription login fails
- Treating Claude Code's final text as verification without running tests
- Delegating without giving exact repository paths and constraints
