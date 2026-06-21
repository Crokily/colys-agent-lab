---
name: codex-collaboration
description: "Delegate coding, review, debugging, refactoring, tests, and repository analysis to local Codex CLI using non-interactive, result-only execution with subscription-login billing guardrails. Use when offloading software engineering work to Codex while avoiding silent API-key fallback."
---

# Codex Collaboration Guide (Result-Only, Non-Interactive)

## Mission

Codex is the primary executor for coding tasks. The main agent should:
1. Detect coding work early
2. Package context clearly
3. Delegate with `codex exec` (non-interactive)
4. Read only final outputs after Codex exits
5. Enforce subscription-login-only billing guardrails before every run

---

## Mandatory Rules

### 0) Authentication and billing guardrail (highest priority)
Use Codex through the user's ChatGPT/subscription login by default. Codex CLI also supports API-key auth, but API-key billing must be an explicit, current-user-authorized choice, never a silent fallback.

Strict requirements:
- Before every delegated run, check `codex login status` (or `codex doctor --summary`) without sending a model prompt.
- Continue only when status confirms a valid subscription/ChatGPT login. If it reports no login, expired auth, unauthorized auth, subscription unavailable, quota/billing problems, API-key auth, or asks for an API key: stop immediately and tell the user to restore subscription login with `codex login`.
- Never run `codex login --with-api-key`, pass API keys via stdin/flags/config, or recommend setting an API key unless the user explicitly requests and authorizes API-key billing for the current run. Normal delegation remains subscription-only.
- Strip API-key environment variables from the Codex process with process-local `env -u ...` unsets (do not mutate the user's shell globally).
- If `codex exec` fails with auth/login/subscription/quota/API-key related errors, treat it as a hard stop; do not retry with API keys, alternate paid providers, or hidden credentials.

### 1) Always use non-interactive mode
Use `codex exec` (or `codex e`) for all delegated coding tasks.

### 2) Use bypass mode only in hardened environments
Use `--dangerously-bypass-approvals-and-sandbox` to avoid approval pauses when the runner is externally hardened.

> Safety note (from Codex CLI reference): this flag bypasses approvals and sandboxing. Use only in externally hardened/isolated runners.

### 3) Never stream Codex run output into current session context
**Critical:** Do not let Codex progress logs/tool chatter pollute this agent context.

Enforce all of the following:
- Use `--output-last-message <file>` to capture Codex final answer
- Redirect stdout/stderr to a log file (`>log 2>&1`)
- Only read the final message file after process exits
- Only inspect log file on failure, and summarize briefly

### 4) Avoid interactive `codex` TUI in normal delegation
Default to non-interactive `codex exec`.

Exception: if an explicit slash-command workflow is requested (for example `/review`), run it in an isolated Codex session and only return the final summary.

---

## Canonical Execution Pattern

**Model selection rule:** use the actual model name with `-m/--model` (for example `gpt-5.4`).
For higher reasoning, pass a config override such as `-c 'model_reasoning_effort="xhigh"'` or set `model_reasoning_effort` in config.
Current `codex exec --help` does not show a direct `--reasoning-effort` flag. Do not use synthetic model names like `gpt-5.4-xhigh`.

```bash
# 1) Prepare files
PROMPT_FILE=$(mktemp /tmp/codex-prompt.XXXXXX.md)
RESULT_FILE=$(mktemp /tmp/codex-result.XXXXXX.txt)
LOG_FILE=$(mktemp /tmp/codex-run.XXXXXX.log)
AUTH_LOG=$(mktemp /tmp/codex-auth.XXXXXX.log)

# 2) Preflight auth without sending a model prompt.
# Must report subscription/ChatGPT login. If it reports API-key auth,
# no login, expired auth, subscription unavailable, quota/billing errors,
# or any prompt to use an API key: STOP and ask the user to run `codex login`.
if ! env -u OPENAI_API_KEY -u CODEX_API_KEY -u AZURE_OPENAI_API_KEY \
  -u ANTHROPIC_API_KEY -u GOOGLE_API_KEY -u GEMINI_API_KEY \
  codex login status > "$AUTH_LOG" 2>&1; then
  echo "Codex subscription login unavailable; stop and ask user to run: codex login" >&2
  exit 125
fi
# MUST inspect $AUTH_LOG minimally for the conditions above before continuing.

# 3) Write prompt content into $PROMPT_FILE (requirements, files, constraints)

# 4) Run Codex non-interactively, no streaming into current context, and no API-key env fallback
env -u OPENAI_API_KEY -u CODEX_API_KEY -u AZURE_OPENAI_API_KEY \
  -u ANTHROPIC_API_KEY -u GOOGLE_API_KEY -u GEMINI_API_KEY \
  codex exec \
  -m gpt-5.4 \
  -c 'model_reasoning_effort="xhigh"' \
  --dangerously-bypass-approvals-and-sandbox \
  --output-last-message "$RESULT_FILE" \
  - < "$PROMPT_FILE" > "$LOG_FILE" 2>&1
CODEX_EXIT=$?

# 5) Post-run handling
# - If CODEX_EXIT=0: consume ONLY $RESULT_FILE
# - If CODEX_EXIT!=0: inspect $LOG_FILE minimally and report concise failure summary
# - If failure is auth/subscription/API-key related: STOP; ask user to restore subscription login; do not retry with API keys
```

Optional for automation/CI logging (after the same subscription-login preflight):
```bash
env -u OPENAI_API_KEY -u CODEX_API_KEY -u AZURE_OPENAI_API_KEY \
  -u ANTHROPIC_API_KEY -u GOOGLE_API_KEY -u GEMINI_API_KEY \
  codex exec -m gpt-5.4 -c 'model_reasoning_effort="xhigh"' --dangerously-bypass-approvals-and-sandbox --json --output-last-message "$RESULT_FILE" - \
  < "$PROMPT_FILE" > "$LOG_FILE" 2>&1
```
`--json` emits JSONL events, but they must stay in log files, not in chat context.

If you prefer config-based defaults, use:
```toml
model = "gpt-5.4"
model_reasoning_effort = "xhigh"
```
Config defaults are allowed only when they still use subscription login. Do not store API-key auth or paid-provider fallback in config for this skill.

---

## Delegation Workflow

### Step 1: Identify coding tasks (delegate immediately)
Delegate tasks like implementation, refactor, debugging, tests, architecture, performance tuning, migrations, config/code review.

### Step 2: Prepare complete prompt context
Include:
- Task objective
- Relevant files/paths
- Constraints and non-goals
- Expected output format
- Validation/test expectations

### Step 3: Execute with result isolation
Run the subscription-login preflight first, then use the canonical pattern above (`codex exec + --dangerously-bypass-approvals-and-sandbox + --output-last-message + stdout/stderr redirection + API-key env stripping`).

### Step 4: Read only final result
- Success: read and use `RESULT_FILE` only
- Failure: read minimal log snippets and summarize; do not dump full logs
- Auth/subscription/API-key failure: stop, tell the user to restore Codex subscription login, and do not retry with API keys

### Step 5: Integrate and verify
Run tests/checks, verify changed files, then present concise summary to user.

---

## Review Tasks (Working Tree Review)

When the user asks for a code review, treat it as a first-class Codex delegation scenario.

### Preferred path (still non-interactive, result-only)
Run the same subscription-login preflight, then use `codex exec` with a review-focused prompt and keep output isolated:

```bash
PROMPT_FILE=$(mktemp /tmp/codex-review-prompt.XXXXXX.md)
RESULT_FILE=$(mktemp /tmp/codex-review-result.XXXXXX.txt)
LOG_FILE=$(mktemp /tmp/codex-review-run.XXXXXX.log)
AUTH_LOG=$(mktemp /tmp/codex-review-auth.XXXXXX.log)

if ! env -u OPENAI_API_KEY -u CODEX_API_KEY -u AZURE_OPENAI_API_KEY \
  -u ANTHROPIC_API_KEY -u GOOGLE_API_KEY -u GEMINI_API_KEY \
  codex login status > "$AUTH_LOG" 2>&1; then
  echo "Codex subscription login unavailable; stop and ask user to run: codex login" >&2
  exit 125
fi
# MUST confirm $AUTH_LOG reports subscription/ChatGPT login, not API-key auth, before continuing.

cat > "$PROMPT_FILE" <<'EOF'
Review the current Git working tree.
Focus on:
1) behavior changes and regressions
2) correctness and edge cases
3) missing/insufficient tests
4) security/performance risks

Output format:
- Findings (severity: high/medium/low)
- Evidence (file + rationale)
- Recommended fixes
- Test gaps
EOF

env -u OPENAI_API_KEY -u CODEX_API_KEY -u AZURE_OPENAI_API_KEY \
  -u ANTHROPIC_API_KEY -u GOOGLE_API_KEY -u GEMINI_API_KEY \
  codex exec -m gpt-5.4 -c 'model_reasoning_effort="xhigh"' --dangerously-bypass-approvals-and-sandbox --output-last-message "$RESULT_FILE" - \
  < "$PROMPT_FILE" > "$LOG_FILE" 2>&1
```

### CLI slash command reference (`/review`)
From Codex CLI slash-commands docs:
- `/review`: ask Codex to review the current working tree
- `/diff`: optionally inspect exact file changes after review
- Expected behavior: emphasizes behavior changes and missing tests
- Model behavior: uses current session model, unless `review_model` is set in `config.toml`

### Policy for using `/review` with this skill
`/review` is an interactive slash command. If you use it:
- run it in an isolated Codex session
- do **not** stream or paste in-flight transcript into this chat
- only bring back the final review summary

---

## Prompt Template for Codex

Use this structure in `PROMPT_FILE`:

```text
Task:
[clear description]

Repository context:
- Working directory: [path]
- Relevant files:
  - [file1]
  - [file2]

Requirements:
1. ...
2. ...

Constraints:
- ...

Validation:
- Run: [test/lint/build commands]
- Expect: [expected outcomes]

Deliverables:
- Modified files list
- What changed and why
- Any tradeoffs / follow-ups
```

---

## Communication Policy

### Before running Codex
"这是编码任务，我将先检查 Codex 订阅登录状态，然后以非交互模式执行；如果登录失效会停止并提醒你登录，不会改用 API key。"

### After success
- Provide concise summary based on final result file
- List modified files and validation status
- Offer follow-up edits

### After failure
- Report failure briefly (exit status + high-level reason)
- Include minimal diagnostic summary from log
- If the reason is auth/subscription/API-key related, say: "Codex 订阅登录不可用/已失效，我已停止任务。请先运行 `codex login` 恢复订阅登录；我不会改用 API key，以避免产生额外费用。"
- Propose retry plan only when it does not involve API keys or alternate paid-provider fallback

---

## Anti-Patterns (Forbidden)

- Running interactive `codex` TUI by default (or without isolation/final-result-only handling)
- Posting Codex streaming output directly into current conversation
- Parsing partial in-flight output as final result
- Using bypass mode casually (follow CLI safety guidance)
- Using stale invocation style (for example direct `--reasoning-effort` when current help requires `-c 'model_reasoning_effort="xhigh"'`)
- Falling back to API-key auth when subscription login fails
- Running `codex login --with-api-key` or passing API keys via stdin/flags/config without explicit user authorization
- Letting `OPENAI_API_KEY`, `CODEX_API_KEY`, or other paid-provider API-key env vars leak into the Codex process

---

## Operational Notes from CLI Reference

- Put flags after subcommand for subcommand runs (e.g., `codex exec --model ...`)
- `-m/--model` takes the model id only (e.g., `gpt-5.4`)
- Use `-c 'model_reasoning_effort="xhigh"'` when you want higher reasoning effort; do not append effort to the model name
- Current `codex exec --help` supports `--json`, `--output-last-message`, and `--dangerously-bypass-approvals-and-sandbox`; it does not show direct `--reasoning-effort`
- `codex exec` is the supported path for non-interactive/CI-style work
- Use `codex login status` (or `codex doctor --summary`) as auth preflight before any model prompt
- `codex login --with-api-key` exists but is forbidden for this skill; subscription login only
- `--output-last-message` is the key primitive for clean, post-run ingestion
- Pair `--json` with `--output-last-message` when machine-readable logs are needed

---

## Quick Checklist

Before run:
- [ ] Coding task identified
- [ ] Prompt file prepared with full context
- [ ] `codex login status` checked and confirms valid subscription/ChatGPT login (not API-key auth)
- [ ] API-key env vars stripped from the Codex process with `env -u ...`
- [ ] Using `codex exec`
- [ ] Using `--dangerously-bypass-approvals-and-sandbox` only when the environment is hardened
- [ ] Using `--output-last-message`
- [ ] Redirecting stdout/stderr to log file

After run:
- [ ] Exit code checked
- [ ] Only final message file consumed on success
- [ ] Logs consulted only if needed
- [ ] User receives concise final summary

---

**Core principle:** Delegate coding to Codex, but ingest only post-run final output. Keep process noise out of the main agent context.
