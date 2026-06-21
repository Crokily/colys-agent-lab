# Collaboration Skills Audit — 2026-06-21

This note records the pre-publication audit for the two collaboration skills in `skills/`.

## Skills reviewed

- `skills/codex-collaboration`
- `skills/claude-code-collaboration`

## Skill-creator validation

Initial findings before improvement:

- `claude-code-collaboration` passed `quick_validate.py`.
- `codex-collaboration` failed `quick_validate.py` because its YAML frontmatter description contained an unquoted colon.

After improvement:

- `search-sessions` passed `quick_validate.py`.
- `codex-collaboration` passed `quick_validate.py`.
- `claude-code-collaboration` passed `quick_validate.py`.
- `claude-code-collaboration/scripts/run-claude-code.sh` passed `bash -n`.

## Documentation checks

Claude Code docs checked:

- Claude Code supports non-interactive/headless execution with `-p` / `--print`.
- `--output-format json` is supported for structured output.
- `claude auth status` reports authentication status.
- `ANTHROPIC_API_KEY`, when set, is used instead of Claude Pro/Max/Team/Enterprise subscription auth in non-interactive mode. The skill therefore strips it by default and requires explicit user authorization for API-key billing.

Codex CLI docs and local CLI help checked:

- Codex supports ChatGPT subscription login and API-key auth.
- `codex exec` is the non-interactive execution mode.
- Current local `codex exec --help` supports `-m/--model`, `--output-last-message`, `--json`, and `--dangerously-bypass-approvals-and-sandbox`.
- Current local `codex exec --help` does not show a direct `--reasoning-effort` flag, so examples now use `-c 'model_reasoning_effort="xhigh"'`.
- `codex login status` is available for authentication preflight.

## Session-history checks

I searched local Pi, Codex, and Claude session history for collaboration-skill usage.

Observed:

- `codex-collaboration` has been used repeatedly in Pi-led coding workflows.
- Prior sessions already discussed the cost/billing concern for Codex and added subscription-only guidance.
- `claude-code-collaboration` was previously created for Pi to call Claude Code through `claude --print` / `claude -p` in headless mode.
- A prior Pi session discussed that `claude -p` usage may have billing implications, which supports adding an explicit subscription/auth guardrail.
- I saw one older Claude API 401/authentication error in `pi-discord-gateway` related history, but not evidence of the improved wrapper failing because it did not exist yet.

## Changes made before publishing

`codex-collaboration`:

- Fixed YAML frontmatter.
- Updated current Codex CLI examples.
- Kept subscription-login-first policy.
- Explicitly forbids silent API-key fallback unless the user authorizes API-key billing for the current run.

`claude-code-collaboration`:

- Added subscription-login-first policy.
- Added `claude auth status` preflight.
- Documented that `ANTHROPIC_API_KEY` overrides subscription auth in non-interactive mode.
- Updated wrapper to strip `ANTHROPIC_API_KEY` by default.
- Added `--allow-api-key-billing` for explicit user-authorized API-key usage.
- Blocks `--bare` in subscription-only mode because it does not use OAuth/keychain subscription auth.

## Result

Both collaboration skills are suitable for publication as reusable skills after the above improvements.
