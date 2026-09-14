# Quality checklist

Run this before every reveal to the user and once more before calling the work done. It is not a style guide; it is the list of things that made generic pages look generic and finished pages look finished.

## System

- One set of tokens: paper or base colour, ink, one accent, one muted, one hairline. Additions need a reason.
- Two type families at most: one for display and text, one monospace for labels. Display type has a real scale: eyebrow, body, lead, headline, display.
- One radius scale, one hairline weight, one shadow recipe, one easing curve. Reuse them everywhere.
- Inherit an existing approved system when there is one. New idea, old tokens.

## Composition

- The first screen shows the idea, the person or product, and proof, in that order of size. A visitor must know who this is and why it matters without scrolling.
- Display type may cross imagery or objects. Body text sits on a stable reading surface. Never body text on clouds, photos or gradients.
- Proof is set as typography (figures with mono captions, a fact row with hairlines), not as badge or logo rows.
- The end of the page differs from the beginning by a state change of the same idea. Never a copy of the hero.
- Depth is handled by structure: a few featured pieces on the home page, the rest in an index with hover previews. Not by making the page longer.
- Each section answers "what does the one idea do here?" If the answer is "nothing", cut or merge it.

## Motion

- Motion is the idea changing state: a frame growing, an object moving, a surface sliding over another. Not decoration.
- Entrance animations must not fight later states. Animations with `forwards` fill override inline styles; hand control over on `animationend`.
- Native scrolling. No hijacked wheel, no forced snapping.
- `prefers-reduced-motion` disables takeovers and entrances and the page still reads top to bottom.

## Generated visuals

- Prefer resolution-independent generation (SVG filters, CSS gradients, shaders) over AI-generated bitmaps. A 1600-pixel image is blurry on a large display and cannot change state.
- Clouds, textures and noise: `feTurbulence` plus a colour matrix into alpha, masked by a gradient, tinted with a multiply layer per state.
- Stylised recreations of other products' surfaces (chat, terminal, newspaper) must be brand-free and labelled as stylised.

## Content honesty

- Every number, role and claim has a source and a check date in the README.
- No invented slogans, issue numbers, testimonials, press logos or "as seen in".
- Descriptions of work come from the work's own README or documentation.
- Personal copy comes from the user or from copy they have already approved.

## Anti-patterns (each of these was tried and rejected on the way to this skill)

- Split hero: headline left, product panel right, three-feature strip, slogan footer. Reads as a SaaS landing page.
- Wallpaper: a fixed background image with large text pasted on it, identical at the top and the bottom of the page.
- Dashboard: sidebar plus a grid of equal glass cards. Reads as an admin tool.
- Mixed visual systems: modern components next to stickers, magnets or pixel fonts without a unifying idea.
- Rough 3D kept because it was already written.
- Giant name alone as the first screen.
- Blurred colour blobs as "clouds" or "atmosphere".
- Badge rows for proof.
- Fake mastheads, volume numbers or slogans invented to fill a layout.

## Validation steps

1. `node --check` or the stack's equivalent on every script; the local server starts.
2. HTTP 200 for every local reference in the HTML (stylesheets, scripts, fonts, media). No duplicate IDs.
3. Screenshots at a wide desktop (1440×900 or larger), a small desktop (1280×720) and a phone (390×844) at the top and at every section boundary. Look at each one. Fix clipped type, overlapping fixed elements, cramped panels, low contrast, cut-off content.
4. `document.documentElement.scrollWidth` equals the viewport width on the phone size.
5. Scroll-driven states checked at their start, middle and end.
6. Reduced motion checked once.
7. Keyboard: focus visible on links and buttons; skip link present.
8. README written with the idea, run instructions, sources for figures, what is stylised, what is not final, what was not verified.

## Before the reveal

List three to five things you want the user to judge. List the known gaps. Never present a state you have not looked at yourself.
