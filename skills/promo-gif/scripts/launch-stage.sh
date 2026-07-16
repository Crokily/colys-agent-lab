#!/usr/bin/env bash
# launch-stage.sh — open a dedicated app window for demo recording, with a
# sanitized environment.
#
# macOS `open` propagates the caller's environment to the launched app. Agent
# shells commonly export NO_COLOR/CLICOLOR, which silently renders every
# color-respecting TUI monochrome (see references/traps.md). Strip those plus
# any nesting vars your product cares about before launching.
#
# Template usage (adapt the app and the command):
#   launch-stage.sh "Ghostty" "herdr --session gifdemo"
set -euo pipefail

app="${1:?usage: launch-stage.sh <App> [command]}"
cmd="${2:-}"

args=()
[ -n "$cmd" ] && args=(--args -e $cmd)
env -u NO_COLOR -u CLICOLOR -u CLICOLOR_FORCE \
  open -na "$app.app" "${args[@]}"

# Verify the window appeared; then (caller) run calibrate-crop.py and, if the
# window is not on the main display, move-window.py.
sleep 3
python3 - "$app" <<'PY'
import sys, Quartz
app = sys.argv[1]
wins = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
cand = [w for w in wins if w.get('kCGWindowOwnerName')==app and w.get('kCGWindowLayer')==0]
if not cand:
    sys.exit(f"launch-stage: no window appeared for {app}")
b = sorted(cand, key=lambda w:-int(w['kCGWindowNumber']))[0]['kCGWindowBounds']
print(f"window at ({b['X']:.0f},{b['Y']:.0f}) {b['Width']:.0f}x{b['Height']:.0f}")
PY
