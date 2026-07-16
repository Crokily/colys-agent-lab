#!/usr/bin/env python3
"""calibrate-crop.py — compute the exact ffmpeg crop for a window's content area.

Prints W:H:X:Y (pixels) for `-vf crop=...`, cropping off the macOS title bar.
Never assumes the capture scale: it takes a 1-frame test capture of the SCREEN
device and divides by the display's point size (2.0 on retina, 1.0 on most
externals, 1.5 on scaled modes).

Usage:
  calibrate-crop.py <app-name> [--screen-index N] [--titlebar-pt 28]

Picks the newest on-screen window owned by <app-name> (highest window number).
Requires: pyobjc-framework-Quartz, Pillow, ffmpeg. Screen-recording permission
must be granted to the invoking terminal.

Trap this guards against: avfoundation device indices are machine-specific and
cameras share the index space — ALWAYS verify the device NAME is
"Capture screen N" (run `ffmpeg -f avfoundation -list_devices true -i ""`)
before passing --screen-index.
"""
import argparse
import subprocess
import sys
import tempfile

import Quartz
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("app")
    ap.add_argument("--screen-index", type=int, default=None,
                    help="avfoundation device index of 'Capture screen N' (verify the NAME first)")
    ap.add_argument("--titlebar-pt", type=float, default=28.0)
    args = ap.parse_args()

    if args.screen_index is None:
        out = subprocess.run(["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                             capture_output=True, text=True).stderr
        for line in out.splitlines():
            if "Capture screen 0" in line:
                args.screen_index = int(line.split("[")[2].split("]")[0])
                break
        if args.screen_index is None:
            sys.exit("calibrate-crop: no 'Capture screen 0' device found")

    d = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
    with tempfile.NamedTemporaryFile(suffix=".png") as tf:
        subprocess.run(["ffmpeg", "-f", "avfoundation", "-capture_cursor", "0",
                        "-framerate", "30", "-i", f"{args.screen_index}:none",
                        "-frames:v", "1", "-y", tf.name], capture_output=True)
        cw, ch = Image.open(tf.name).size
    sx, sy = cw / d.size.width, ch / d.size.height

    wins = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    cand = sorted([w for w in wins
                   if w.get("kCGWindowOwnerName") == args.app and w.get("kCGWindowLayer") == 0],
                  key=lambda w: -int(w["kCGWindowNumber"]))
    if not cand:
        sys.exit(f"calibrate-crop: no on-screen window owned by {args.app!r}")
    b = cand[0]["kCGWindowBounds"]
    if b["X"] >= d.size.width or b["Y"] >= d.size.height:
        sys.exit(f"calibrate-crop: window is NOT on the main display "
                 f"(at {b['X']},{b['Y']}) — move it first (see move-window.py); "
                 f"recording a 1x external display halves text sharpness")

    x = int(b["X"] * sx)
    y = int((b["Y"] + args.titlebar_pt) * sy)
    w = int(b["Width"] * sx)
    h = int((b["Height"] - args.titlebar_pt) * sy)
    w -= w % 2
    h -= h % 2
    print(f"{w}:{h}:{x}:{y}")


if __name__ == "__main__":
    main()
