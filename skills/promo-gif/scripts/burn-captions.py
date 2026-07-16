#!/usr/bin/env python3
"""burn-captions.py — burn per-scene caption bars into a recording.

Reads scene marks from a log ("rec-start <epoch>" line + "[scene <epoch>] <name>"
lines) and a caption spec, renders full-width bars with PIL (accent-colored key
token + white text on black@0.55), and burns them with chained ffmpeg `overlay`
filters. Uses PIL+overlay instead of drawtext because Homebrew ffmpeg builds
frequently ship WITHOUT the drawtext filter.

Burn onto the RAW (untrimmed) recording: caption windows are expressed in raw
time, so later cuts (spinner dead time) never desynchronize them.

Usage:
  burn-captions.py <master.mp4> <scenes.log> <captions.tsv> <out.mp4>

captions.tsv — tab-separated, one caption per line:
  from_mark  from_offset  to_mark(or "-" = video end)  to_offset  key(or "")  text
Example:
  sidebar-open  0.8  stage-files  0  prefix+g  one key opens a git sidebar
"""
import os
import re
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/Menlo.ttc"
BAR_FRAC = 0.066   # bar height as a fraction of video height
ACCENT = (255, 214, 90, 255)
WHITE = (240, 240, 240, 255)


def main():
    master, scenes_log, captions_tsv, out = sys.argv[1:5]

    log = open(scenes_log).read()
    rs = float(re.search(r"rec-start ([\d.]+)", log).group(1))
    marks = {m.group(2): float(m.group(1)) - rs
             for m in re.finditer(r"\[scene ([\d.]+)\] (\S+)", log)}

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=width,height:format=duration",
         "-of", "csv=p=0", master], capture_output=True, text=True).stdout.split()
    W, H = map(int, probe[0].split(",")[:2])
    dur = float(probe[-1])
    bar_h = int(H * BAR_FRAC) // 2 * 2
    fsize = int(bar_h * 0.46)
    font = ImageFont.truetype(FONT, fsize, index=0)
    fontb = ImageFont.truetype(FONT, fsize, index=1)

    tmpdir = tempfile.mkdtemp(prefix="captions.")
    inputs, chains = [], []
    rows = [l.rstrip("\n").split("\t") for l in open(captions_tsv) if l.strip()]
    for i, (m1, o1, m2, o2, key, text) in enumerate(rows):
        a = marks[m1] + float(o1)
        b = dur if m2 == "-" else marks[m2] + float(o2)
        im = Image.new("RGBA", (W, bar_h), (0, 0, 0, 150))
        d = ImageDraw.Draw(im)
        ktxt = f"[{key}]  " if key else ""
        kw = d.textlength(ktxt, font=fontb)
        tw = d.textlength(text, font=font)
        x = (W - kw - tw) / 2
        y = (bar_h - fsize) / 2 - 2
        if ktxt:
            d.text((x, y), ktxt, font=fontb, fill=ACCENT)
        d.text((x + kw, y), text, font=font, fill=WHITE)
        p = os.path.join(tmpdir, f"{i:02d}.png")
        im.save(p)
        inputs += ["-i", p]
        src = "[base]" if i == 0 else f"[v{i-1}]"
        chains.append(f"{src}[{i+1}:v]overlay=0:H-{bar_h}:"
                      f"enable='between(t,{a:.2f},{b:.2f})'[v{i}]")

    fc = "[0:v]null[base];" + ";".join(chains)
    r = subprocess.run(["ffmpeg", "-y", "-i", master] + inputs +
                       ["-filter_complex", fc, "-map", f"[v{len(rows)-1}]",
                        "-pix_fmt", "yuv420p", out],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr.splitlines()[-1])
    print(out)


if __name__ == "__main__":
    main()
