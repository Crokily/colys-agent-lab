---
name: promo-gif
description: Fully automated product demo GIF recording on macOS. Use when the user wants a promo/demo GIF or video for a product (CLI, TUI, web app, desktop app) for a README, release notes, or social media. Covers scripted choreography, real-environment screen capture, burned-in captions, dead-time cuts, gifski encoding, and feature-asset extraction — with guardrails for the traps that ruin recordings (camera device capture, NO_COLOR inheritance, non-retina displays, synthetic-terminal renderers).
---

# Promo GIF

## Overview

Produce a README-grade demo GIF (plus an MP4 for social) by **recording the real product on a real screen while a deterministic script performs the demo**. The pipeline separates four concerns so each can be iterated independently:

1. **Stage** — launch the product in a dedicated, sanitized window
2. **Act** — a choreography script drives the product and emits timestamped scene marks
3. **Capture** — ffmpeg records a calibrated region of the real screen
4. **Post** — captions are burned per scene, dead time is cut, gifski encodes

The single most important architectural decision: **the acting is code, the recording is dumb.** A choreography script that drives the product through its own automation surface (CLI, socket API, browser automation, AppleScript-able app API) can be re-run identically after every feedback round. Never improvise the demo by hand, and never let pacing be an accident of tool defaults.

## Non-negotiable rules (each one is a scar)

1. **Never use synthetic terminal renderers** (VHS, asciinema+agg) for products with real UI chrome — they re-render in their own headless terminal with their own fonts/colors and the result looks nothing like the real product. Record the real screen. Synthetic renderers are acceptable only for single-command CLI snippets.
2. **Select the ffmpeg capture device by NAME, never by index.** On macOS, `ffmpeg -f avfoundation -list_devices true -i ""` — cameras and screens share the index space and the order varies by machine. Match the name `Capture screen N`. If you guess an index you may record the user's **camera**. Audio spec is always `:none`.
3. **Sanitize the launch environment.** macOS `open` propagates the caller's env to the launched app. Agent shells commonly export `NO_COLOR` — inherited by the app, it silently turns every color-respecting program (lazygit, fzf, delta, most TUIs) monochrome. Launch through `env -u NO_COLOR -u CLICOLOR -u CLICOLOR_FORCE ... open -na App`, plus unset any nesting vars your product cares about (e.g. terminal-multiplexer session sockets).
4. **Add a quality gate to the choreography.** Before the first real scene, programmatically verify the product renders as expected (e.g. read ANSI output and require `38;5;` color codes; for web, screenshot and check a known pixel). Abort loudly instead of producing an hour of gray footage.
5. **Record on the retina/2x display.** Multi-monitor Macs open windows on the display with mouse focus; a 1x external monitor halves your text sharpness. Verify window position via Quartz `CGWindowListCopyWindowInfo`; move it with the AX API if needed (`scripts/move-window.py` — System Events AppleScript often hangs on some apps; the raw AX call does not).
6. **Calibrate the crop, don't assume the scale.** Capture pixels ÷ display points varies (2.0 retina, 1.0 external, 1.5 scaled). Take a 1-frame test capture of the SCREEN device, divide by `CGDisplayBounds`, compute the crop from the window bounds × scale, and crop off the title bar (~28pt × scale). `scripts/calibrate-crop.py` does all of this.
7. **Scene marks are the spine of post-production.** The choreography prints `[scene <epoch.fraction>] <name>` at every beat and the recorder logs its own start epoch. Everything downstream — caption windows, dead-time cuts, feature-asset extraction — is computed from marks, never eyeballed.
8. **Leave no trace.** The pipeline creates its own session/window/workspace/repo and tears all of it down. Never touch, move, resize, or type into pre-existing windows. If a step needs GUI focus, verify the target window first (Quartz bounds or a screenshot).

## Directing: what makes the GIF good

- **Narrative order = product thesis.** Order scenes to argue the design, not to enumerate features. Example: show the compact mode completing a full daily workflow FIRST (thesis: "compact is enough"), and only then the expanded mode ("depth when you want it"). Leave a visible loose end before a transition (one unstaged file remaining) so the next scene feels motivated.
- **Captions do double duty** — narration and feature documentation in one line each: a highlighted key token plus a short clause (`[U]  need a closer look? expand into full lazygit`). One thesis line with no key at the story's turning point. Final caption = the install command.
- **Directed pacing.** Every end-state holds ≥2s (read time), wow-moments 3–4s. Real waits (spinners) stay in for honesty but are cut to head+tail in post (~2.5s + ~1s).
- **Demo data is part of the set design.** Generate a small, realistic, deterministic repo/dataset (`scripts/` pattern: a make-demo-repo script) so every retake is pixel-identical and nothing private can leak into frame.
- **45–75s master, trimmed to <60s.** README GIF at 1000–1200px wide, 12fps, gifski quality 90, target <10MB (fallback order: quality 80 → width 960 → 10fps). Derive an H.264 MP4 from the same master for social.

## Pipeline (macOS)

Concrete scripts in `scripts/` are templates from a shipped project — adapt names/paths:

1. `make-demo-repo.sh <dir>` — deterministic demo content.
2. `launch-stage.sh <session>` — env-sanitized dedicated window (rule 3); verify it landed on the retina display (rule 5, `move-window.py` if not).
3. `calibrate-crop.py` — returns `W:H:X:Y` for ffmpeg (rule 6).
4. Record: `ffmpeg -f avfoundation -capture_cursor 0 -framerate 30 -i "<SCREEN_IDX>:none" -vf "crop=W:H:X:Y" -pix_fmt yuv420p master-raw.mp4 &` — log the start epoch, then run the choreography, then SIGINT ffmpeg ~2s after it exits.
5. `choreography.sh` — the acting: scene marks (rule 7), quality gate (rule 4), directed pauses. Drive via the product's automation surface; for web products use browser automation (agent-browser/playwright) instead of key injection.
6. Captions: render full-width bar PNGs with PIL (key token in accent color + white text, black@0.55 bar) and burn with chained `overlay=0:H-<bar>:enable='between(t,a,b)'` — **ffmpeg's drawtext filter is often missing from Homebrew builds; the PIL+overlay path always works.** Burn onto the RAW timeline BEFORE trimming so caption windows survive cuts.
7. Trim: splice out spinner middles and dead time via scene-mark arithmetic (`trim=start=A:end=B,setpts=PTS-STARTPTS` + `concat`).
8. Encode: `ffmpeg -i demo.mp4 -vf "fps=12,scale=1100:-1:flags=lanczos" frames/%04d.png && gifski --fps 12 --quality 90 -o demo.gif frames/*.png`.
9. Feature assets: cut per-feature stills and mini-GIFs from the **captioned** master at scene marks — they inherit their explanations for free. Embed hero GIF after the README intro, feature assets in their sections.
10. Teardown: sessions, windows, temp repos; keep only the output dir (gitignore raw outputs; commit final assets under `docs/media/`).

## Review loop

Extract 6–8 evenly spaced keyframes and inspect them (colors present? end-states readable? nothing private in frame?) before showing the user. Compare saturated-pixel counts between master/trimmed/GIF frames to catch silent color loss (`scripts/check-colors.py`). Iterate by editing the choreography and re-running — the whole pipeline is one command per stage.

## Adapting beyond terminal products

- **Web app**: stage = a fresh browser profile window at fixed size (no bookmarks/extensions in frame); act = playwright/agent-browser script with the same scene-mark pattern; capture/post identical. Prefer capturing the real browser window over headless-rendered video for font/scrollbar fidelity, unless the app is pixel-identical headless.
- **Desktop app**: act = the app's scripting surface (AppleScript/CLI/URL schemes) or computer-use with per-step visual verification; everything else identical.
- **Pure CLI**: the one case where a synthetic renderer (VHS) is acceptable — no window chrome to lose. Still apply scene pacing and captions.
