#!/usr/bin/env python3
"""move-window.py — move an app's newest window to the main (retina) display.

Uses the raw Accessibility API (AXUIElement) instead of System Events
AppleScript, which hangs indefinitely on some apps (observed with Ghostty).
Matches the AX window against the CGWindow bounds so exactly the intended
window moves — never "front window" guessing. Verifies the result via Quartz.

Usage: move-window.py <app-name> [x] [y]     (default target: 40 60)
Requires: pyobjc-framework-Quartz, pyobjc-framework-ApplicationServices,
and Accessibility permission for the invoking terminal.
"""
import re
import sys
import time

import Quartz
from ApplicationServices import (AXUIElementCreateApplication,
                                 AXUIElementCopyAttributeValue,
                                 AXUIElementSetAttributeValue,
                                 AXValueCreate, kAXValueCGPointType)


def newest_window(app):
    wins = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    cand = sorted([w for w in wins
                   if w.get("kCGWindowOwnerName") == app and w.get("kCGWindowLayer") == 0],
                  key=lambda w: -int(w["kCGWindowNumber"]))
    if not cand:
        sys.exit(f"move-window: no on-screen window owned by {app!r}")
    return cand[0]


def main():
    app = sys.argv[1]
    tx = float(sys.argv[2]) if len(sys.argv) > 2 else 40.0
    ty = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0

    target = newest_window(app)
    tb = target["kCGWindowBounds"]
    ax = AXUIElementCreateApplication(int(target["kCGWindowOwnerPID"]))
    err, windows = AXUIElementCopyAttributeValue(ax, "AXWindows", None)
    if err != 0:
        sys.exit(f"move-window: AX error {err} — grant Accessibility permission")

    for w in windows:
        e, pos = AXUIElementCopyAttributeValue(w, "AXPosition", None)
        if e:
            continue
        m = re.search(r"x:([-\d.]+) y:([-\d.]+)", repr(pos))
        if m and abs(float(m.group(1)) - tb["X"]) < 5 and abs(float(m.group(2)) - tb["Y"]) < 5:
            AXUIElementSetAttributeValue(
                w, "AXPosition", AXValueCreate(kAXValueCGPointType, Quartz.CGPoint(tx, ty)))
            break
    else:
        sys.exit("move-window: could not match the CG window to an AX window")

    time.sleep(0.5)
    b = newest_window(app)["kCGWindowBounds"]
    ok = abs(b["X"] - tx) < 5 and abs(b["Y"] - ty) < 5
    print(f"now at ({b['X']:.0f},{b['Y']:.0f}) — {'OK' if ok else 'FAILED'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
