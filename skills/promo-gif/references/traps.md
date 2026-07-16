# Field-tested traps

Every entry here ruined at least one real recording session before making it
into the rules. Read this before your first take, and again when something
looks inexplicably wrong.

## Capture layer

- **Camera instead of screen.** avfoundation device indices are per-machine and
  cameras share the index space with screens (`[0] MacBook Air Camera`,
  `[1] Desk View Camera`, `[2] Capture screen 0` on one machine — different on
  the next). One guessed index recorded the user's webcam. Match the device
  NAME, and delete any accidental camera captures immediately.
- **The "screen test" that lied.** A 1-frame test capture that returns
  1920×1440 might be the desk-view camera, not a display. Sanity-check the
  test frame content (a screen capture contains your desktop, not a room).
- **Wrong display = blurry text.** Windows open on the display that has mouse
  focus. A 1x external monitor gives half the pixel density of the retina
  panel; the GIF's downscale then averages nothing and text looks chunky.
  Check `CGWindowListCopyWindowInfo` bounds against the main display before
  recording; move with the AX API if needed.
- **Scale is not always 2.0.** Compute capture-px ÷ display-pt fresh every
  session (external monitors: 1.0; scaled modes: 1.5).

## Environment layer

- **`NO_COLOR` inheritance through `open`.** macOS `open` passes the caller's
  environment to the launched app. Agent shells export `NO_COLOR`/`CLICOLOR`;
  the recorded app renders monochrome while the shell prompt (which ignores
  those vars) stays colored — which is exactly why the symptom is confusing.
  Diagnose by comparing which programs lost color: if color-respecting tools
  (lazygit, fzf, delta, bat-without-flags) are gray but the prompt is colored,
  it's the environment, not the capture. Fix at launch (`env -u NO_COLOR ...`)
  and add a color gate to the choreography so it can never happen silently.
- **Nested-session variables.** If the product is itself a terminal
  multiplexer/session manager, launching from inside one leaks
  session/socket/pane vars and the new instance may refuse to start or attach
  to the wrong session. Unset them all at launch.
- **Fresh sessions are empty.** A dedicated recording session/profile does not
  have your plugins/extensions/config. Provision it explicitly (link the
  plugin, install the extension) as part of staging, and verify before acting.

## GUI-automation layer

- **System Events AppleScript can hang forever** enumerating some apps'
  windows (observed: Ghostty). The raw AX API (`AXUIElementCopyAttributeValue`
  via pyobjc) does not. Always pair a move with a Quartz read-back to verify
  the RIGHT window moved.
- **Never type into a window you haven't verified.** Blind `keystroke` lands
  in whatever has focus — possibly the user's work. Prefer driving the product
  through its own automation surface (socket/CLI/browser protocol) so focus
  doesn't matter; when GUI input is unavoidable, verify the frontmost window
  first and drive with per-step verification.
- **`open -na App --args` flags are best-effort.** Window position/size args
  may be ignored or applied relative to the wrong display. Verify, don't
  trust.

## Post-production layer

- **Homebrew ffmpeg often lacks `drawtext`.** Don't fight it: render caption
  bars as PNGs with PIL and burn with `overlay` (a core filter that always
  exists).
- **Burn captions before trimming.** Caption enable-windows are expressed in
  raw-timeline seconds; cutting first would shift every window. Burned pixels
  ride through cuts for free.
- **Trimmed-off color loss is invisible in stills you don't take.** Verify
  color survives each stage (master → trimmed → GIF) by counting saturated
  pixels in extracted frames, not by memory.
- **gifski quality beats ffmpeg's GIF encoder** by a wide margin at the same
  size. 12fps / quality 90 / lanczos downscale to ~1100px is the sweet spot;
  degrade in the order quality → width → fps.

## Process layer

- **Concurrent edits during a delegated run.** If a sub-agent works in the
  same repo while you edit files, its git operations can clobber your
  working-tree changes. Sequence repo access; one writer at a time.
- **Scene marks with 1-second granularity cause caption jitter.** Print marks
  with sub-second precision (`time.time():.2f`).
- **The spinner is honest, the wait is boring.** Keep ~2.5s head + ~1s tail of
  any real wait; splice out the middle. Total dead time cut should be visible
  in the scene table you keep for the trim.
