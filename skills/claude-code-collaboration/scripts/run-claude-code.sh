#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: run-claude-code.sh --prompt-file FILE [options]

Run local Claude Code in headless JSON mode while isolating logs.
By default, require subscription login and remove ANTHROPIC_API_KEY from
the Claude child process to avoid silent API-key billing.

Required:
  --prompt-file FILE             Markdown/text prompt to send to Claude Code

Options:
  --cwd DIR                      Working directory for Claude Code (default: current dir)
  --result-file FILE             Extracted final .result text (default: temp file)
  --json-file FILE               Raw JSON stdout from Claude Code (default: temp file)
  --log-file FILE                stderr/debug log (default: temp file)
  --permission-mode MODE         acceptEdits|auto|bypassPermissions|default|dontAsk|plan
  --allowed-tools TOOLS          Tool allowlist, e.g. "Read,Grep,Glob"
  --disallowed-tools TOOLS       Tool denylist, e.g. "Write,Edit,Bash"
  --tools TOOLS                  Available tool list, e.g. "default" or "Read,Edit"
  --model MODEL                  Claude Code model alias or full model name
  --effort LEVEL                 low|medium|high|xhigh|max
  --append-system-prompt TEXT    Extra system prompt text
  --system-prompt TEXT           Replace default system prompt
  --mcp-config FILE_OR_JSON      MCP config path or JSON (repeatable by comma not supported; pass once)
  --resume SESSION_OR_QUERY      Resume a session
  --continue                     Continue most recent session in current directory
  --session-id UUID              Use specific session ID
  --name NAME                    Display name for Claude Code session
  --bare                         Use Claude Code bare mode
  --no-session-persistence       Disable session persistence
  --allow-api-key-billing        Preserve API-key auth/env; use only with explicit user authorization
  --extra-arg ARG                Append one raw CLI arg; can repeat
  -h, --help                     Show this help

The script prints the result/json/log paths to stderr. It returns Claude Code's exit code.
EOF
}

prompt_file=""
cwd="$PWD"
result_file=""
json_file=""
log_file=""
permission_mode=""
allowed_tools=""
disallowed_tools=""
tools=""
model=""
effort=""
append_system_prompt=""
system_prompt=""
mcp_config=""
resume_value=""
continue_flag=0
session_id=""
name=""
bare_flag=0
no_session_persistence=0
allow_api_key_billing=0
extra_args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt-file) prompt_file="${2:-}"; shift 2 ;;
    --cwd) cwd="${2:-}"; shift 2 ;;
    --result-file) result_file="${2:-}"; shift 2 ;;
    --json-file) json_file="${2:-}"; shift 2 ;;
    --log-file) log_file="${2:-}"; shift 2 ;;
    --permission-mode) permission_mode="${2:-}"; shift 2 ;;
    --allowed-tools|--allowedTools) allowed_tools="${2:-}"; shift 2 ;;
    --disallowed-tools|--disallowedTools) disallowed_tools="${2:-}"; shift 2 ;;
    --tools) tools="${2:-}"; shift 2 ;;
    --model) model="${2:-}"; shift 2 ;;
    --effort) effort="${2:-}"; shift 2 ;;
    --append-system-prompt) append_system_prompt="${2:-}"; shift 2 ;;
    --system-prompt) system_prompt="${2:-}"; shift 2 ;;
    --mcp-config) mcp_config="${2:-}"; shift 2 ;;
    --resume|-r) resume_value="${2:-}"; shift 2 ;;
    --continue|-c) continue_flag=1; shift ;;
    --session-id) session_id="${2:-}"; shift 2 ;;
    --name|-n) name="${2:-}"; shift 2 ;;
    --bare) bare_flag=1; shift ;;
    --no-session-persistence) no_session_persistence=1; shift ;;
    --allow-api-key-billing) allow_api_key_billing=1; shift ;;
    --extra-arg) extra_args+=("${2:-}"); shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$prompt_file" ]]; then
  echo "Error: --prompt-file is required" >&2
  usage >&2
  exit 2
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "Error: claude CLI not found in PATH" >&2
  exit 127
fi

if [[ ! -f "$prompt_file" ]]; then
  echo "Error: prompt file not found: $prompt_file" >&2
  exit 2
fi

mkdir -p "$cwd"
cwd="$(cd "$cwd" && pwd)"
prompt_file="$(python3 - <<'PY' "$prompt_file"
import os, sys
print(os.path.abspath(os.path.expanduser(sys.argv[1])))
PY
)"

result_file="${result_file:-$(mktemp /tmp/claude-code-result.XXXXXX.txt)}"
json_file="${json_file:-$(mktemp /tmp/claude-code-result.XXXXXX.json)}"
log_file="${log_file:-$(mktemp /tmp/claude-code-run.XXXXXX.log)}"
mkdir -p "$(dirname "$result_file")" "$(dirname "$json_file")" "$(dirname "$log_file")"
: > "$log_file"

claude_cmd=(claude)
if [[ "$allow_api_key_billing" -ne 1 ]]; then
  if [[ "$bare_flag" -eq 1 ]]; then
    echo "Error: --bare does not use Claude subscription OAuth/keychain auth." >&2
    echo "Remove --bare, or pass --allow-api-key-billing only after explicit user authorization." >&2
    echo "log_file=$log_file" >&2
    exit 2
  fi

  set +e
  auth_status="$(cd "$cwd" && env -u ANTHROPIC_API_KEY claude auth status 2>> "$log_file")"
  auth_exit=$?
  set -e
  if [[ "$auth_exit" -ne 0 ]]; then
    echo "Error: Claude subscription login unavailable; ask the user to run: claude auth login" >&2
    echo "log_file=$log_file" >&2
    exit 125
  fi

  if ! printf '%s' "$auth_status" | python3 -c '
import json
import sys

raw = sys.stdin.read()
try:
    data = json.loads(raw)
except Exception:
    print("Claude auth status did not return JSON; cannot verify subscription login.", file=sys.stderr)
    sys.exit(1)

logged_in = data.get("loggedIn") is True
auth_method = str(data.get("authMethod") or "").lower()
api_provider = str(data.get("apiProvider") or "").lower()
subscription = str(data.get("subscriptionType") or "")

uses_api_key = "api" in auth_method or auth_method in {"apikey", "api-key"}
wrong_provider = bool(api_provider) and api_provider != "firstparty"
has_subscription_auth = auth_method in {"claude.ai", "oauth"} or bool(subscription)

if not logged_in or uses_api_key or wrong_provider or not has_subscription_auth:
    print("Claude subscription login unavailable or API-key auth detected.", file=sys.stderr)
    sys.exit(1)
' >> "$log_file" 2>&1; then
    echo "Error: Claude subscription login unavailable or API-key auth detected." >&2
    echo "Run 'claude auth login' for subscription auth, or explicitly authorize API-key billing." >&2
    echo "log_file=$log_file" >&2
    exit 125
  fi

  claude_cmd=(env -u ANTHROPIC_API_KEY claude)
fi

prompt_content="$(cat "$prompt_file")"
args=(--print "$prompt_content" --output-format json)

[[ "$bare_flag" -eq 1 ]] && args+=(--bare)
[[ "$continue_flag" -eq 1 ]] && args+=(--continue)
[[ -n "$resume_value" ]] && args+=(--resume "$resume_value")
[[ -n "$session_id" ]] && args+=(--session-id "$session_id")
[[ -n "$name" ]] && args+=(--name "$name")
[[ -n "$permission_mode" ]] && args+=(--permission-mode "$permission_mode")
[[ "$permission_mode" == "bypassPermissions" ]] && args+=(--dangerously-skip-permissions)
[[ -n "$allowed_tools" ]] && args+=(--allowed-tools "$allowed_tools")
[[ -n "$disallowed_tools" ]] && args+=(--disallowed-tools "$disallowed_tools")
[[ -n "$tools" ]] && args+=(--tools "$tools")
[[ -n "$model" ]] && args+=(--model "$model")
[[ -n "$effort" ]] && args+=(--effort "$effort")
[[ -n "$append_system_prompt" ]] && args+=(--append-system-prompt "$append_system_prompt")
[[ -n "$system_prompt" ]] && args+=(--system-prompt "$system_prompt")
[[ -n "$mcp_config" ]] && args+=(--mcp-config "$mcp_config")
[[ "$no_session_persistence" -eq 1 ]] && args+=(--no-session-persistence)
if [[ ${#extra_args[@]} -gt 0 ]]; then
  args+=("${extra_args[@]}")
fi

set +e
(
  cd "$cwd" && "${claude_cmd[@]}" "${args[@]}"
) > "$json_file" 2>> "$log_file"
exit_code=$?
set -e

python3 - <<'PY' "$json_file" "$result_file"
import json, sys
json_path, result_path = sys.argv[1], sys.argv[2]
try:
    raw = open(json_path, 'r', encoding='utf-8', errors='replace').read()
except FileNotFoundError:
    raw = ''
text = ''
if raw.strip():
    try:
        data = json.loads(raw)
        text = data.get('result') or data.get('message') or ''
        if not text and isinstance(data.get('content'), list):
            parts = []
            for item in data['content']:
                if isinstance(item, dict) and item.get('text'):
                    parts.append(item['text'])
            text = '\n'.join(parts)
    except Exception:
        text = raw
with open(result_path, 'w', encoding='utf-8') as f:
    f.write(text)
    if text and not text.endswith('\n'):
        f.write('\n')
PY

echo "claude_exit=$exit_code" >&2
echo "result_file=$result_file" >&2
echo "json_file=$json_file" >&2
echo "log_file=$log_file" >&2

exit "$exit_code"
