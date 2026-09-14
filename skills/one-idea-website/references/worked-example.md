# Worked example: one run, three failures, one result

Read this for the method. Do not copy the outcome; it belongs to one person's material and references. The anti-convergence check in `idea-vocabulary.md` exists because of this file.

## The brief

A personal website for an AI agent engineer in Sydney. Job search first, peer credibility and collaboration second. He liked an earlier prototype's modern, bright, restrained finish but not its layout. He wanted colour, sky, full-screen sections with transitions, high-quality motion, and a site that made people remember him.

## Failure 1: the split hero

The first prototype had a headline on the left, a floating product panel on the right, a three-feature strip and a slogan footer. Finish was good. The user called it a corporate landing page. Lesson: quality of finish does not rescue a template structure.

## Failure 2: wallpaper with text

The next version put a generated sky behind the whole page, giant text on top of it, white sheets sliding over for the middle sections, and the same sky again at the end. The user pointed out that the first and last screens were identical and that text on clouds was hard to read. Lesson: scenery needs an edge and a role; the end must differ from the start by a state change, not a copy.

## Failure 3: the dashboard

The assistant, optimising for "work first, no long scroll, many projects", proposed a workspace: a sidebar of projects and three live panes in a glass-card grid. The user called it the least designed version yet, a module rather than a site, and asked whether the assistant had studied his references. It had not. Lesson: never propose before opening the references. A grid of equal cards is an admin panel no matter the material.

## What turned it around

1. **Opening the references.** Details.so, Inspora, Design on X, Code Storage, Exo Ape, Dia, Inori, Yoshik, an airplane-window portfolio, a Polaroid navigation. Written observations for each. The shared principle: one strong idea, type and object as protagonists, no card grids.
2. **Auditing the real material.** Three flagship repositories with README facts, star counts, npm downloads and contributor counts pulled from the GitHub and npm APIs. A community he co-founded. Sixteen agent-related repositories in one year. A statement the facts supported: "I put coding agents where people already work."
3. **Deriving the idea from his material.** His three works each live inside someone else's surface: a chat app, a terminal, a community website. The airplane-window reference suggested a frame; the sky he asked for became a state that changes per project; the name crossing the frame came from Exo Ape. One sentence: "The site is a window that holds a sky and the work; the name crosses its edge."
4. **Correcting the intro.** The assistant first removed the person from the first screen entirely. The user pushed back: he should be there, introduced by highlights rather than by thin text. The first screen became "the person surrounded by proof": giant name, statement, a band of four verified figures and three work thumbnails.
5. **One screen, real HTML, self-reviewed.** The first screen was built as a page in a scratch directory, screenshotted at 1440, 1280 and 390, fixed (clipped name, header over labels, entrance animation overriding scroll state, cramped panels) and then shown with a list of five things to judge. The user approved it in the browser before anything else was built.
6. **Growing the system.** Scenes where the frame takes over the viewport; paper case studies with stylised, labelled demos; an index for the smaller projects; an About on paper; a footer where the frame returns small at night. All v0 tokens. Clouds generated with an SVG turbulence filter so nothing is a blurry bitmap.
7. **Removing inventions.** A "Vol. 13 · No. 178928069482" masthead line and two slogans written for a newspaper panel were deleted when noticed and replaced with README text.

## What to take from it

- The structural diagnosis of each failure, not the fix.
- The order: references, material, idea, one screen, system, validation.
- The gates: no proposal before references, no build before an approved first screen.
- The honesty: verified figures, labelled recreations, deleted inventions.

## What not to take from it

The window, the sky, the name crossing the frame, the proof band, morning-noon-dusk-night. Those were his. Yours will come from your user's material and will look different if you did the work.
