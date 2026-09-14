---
name: one-idea-website
description: Turn a brief into a distinctive, memorable website (personal site, portfolio, product or campaign landing page, any page that has to impress) by studying real references first, finding the one idea that fits this person's or product's own material, gating on a real first-screen draft, and building the rest as one system. Use whenever the risk is "a generic AI-looking page". Ships its own reference library for users who have no references. Designed with and works best on Claude Fable 5.1.
---

# One-idea website

A page people remember has one strong idea, executed with consistency: one object or move, one typographic scale, one rhythm. Everything else is discipline. This skill is the discipline.

It is written for engineers who are not designers. It does not require the user to bring taste or references; it brings a curated library and a method for deriving the idea from the user's own material. Different users must end with different sites. If two runs of this skill look alike, the skill was misused. See "Anti-convergence" below.

**Model note:** this method was developed and validated with Claude Fable 5.1, which can carry the whole loop (study references, judge composition from screenshots, write the code, self-review) in one session. It works best there. On smaller models, treat every gate below as mandatory and expect more iterations.

## Scope

In: personal sites, portfolios, product and campaign landing pages, event and launch pages, any single surface whose job is to impress and be remembered.
Out: dashboards, admin tools, data-heavy product UI, multi-step flows, native mobile. For those, use a product-design skill.

## The one rule

Never start from a layout. Start from the person's or product's real material, look at real references, and find **one idea** that the whole page serves. Then build the page as one system around it. A page that "has a hero, a features grid, a testimonials row and a footer" is a template, not a design, whatever colors it wears.

## Anti-convergence

The worked example in `references/worked-example.md` ended with a rounded window holding a generated sky, a giant name crossing the window's edge and a proof band. **Do not reuse that outcome.** It fit one person because of his references and his work. For each new user:

1. Derive candidates from *their* material (see phase 2). If none of the candidates would surprise the user, you have not looked hard enough.
2. Produce three distinct candidates from different families in `references/idea-vocabulary.md` before choosing one.
3. Run the check: "Would this idea still make sense if the user were a different person with different work?" If yes, it is generic. Replace it.
4. If the chosen idea resembles the worked example or any single reference too closely, change the object, the material or the move until it is theirs.

## Process and gates

Do the phases in order. Each gate is a hard stop until satisfied.

### Phase 0 · Look at references before proposing anything

Ask the user for references (sites, screenshots, saved posts). Many engineers have none. Then use `references/reference-library.md`: it lists collection sites and specific pages worth studying, with what each one teaches.

Actually open at least five references. Screenshot each at two or three scroll positions (agent-browser or any headless browser). For each, write one line of **concrete observation**: what is the single object or move, how big is the type, what sits on what surface, how sections transition. Then write the principle they share. Only then talk to the user.

Gate 0: you can cite five references with specific observations, not adjectives.

### Phase 1 · Audit the real material

Collect what is true about this person or product: work, tools, numbers, roles, places, a voice. Verify every figure at its source (GitHub API, npm API, app store, analytics, a document the user provides). Decide which three to five facts carry the most weight and phrase them honestly ("built and co-founded", "past year", "second most commits"). Write one statement with a point of view, under 12 words, that the facts support.

Gate 1: a facts table with sources, and a statement the user agrees with. Nothing invented, not even a slogan.

### Phase 2 · Find the one idea

From the material and the references, list candidate ideas across at least three families from `references/idea-vocabulary.md` (an object, a material, a typographic move, a motion, a world, a document form, a scenery state, a sound or instrument). For each: what it is, where it comes from in the user's material, how it appears on the first screen, how it changes at the end of the page, what it costs to build well.

Present the candidates in words and ASCII sketches, with your recommendation and its reason. Let the user choose or redirect. Keep asking until one idea can be described in a single sentence that names one object or move.

Gate 2: one sentence, one idea, user-approved.

### Phase 3 · One screen decides

Build only the first screen, as real HTML/CSS/JS in a scratch directory, served locally. No mockup tools, no static images of layouts; the user must judge the actual feel, including motion.

Before showing it, screenshot it yourself at a wide desktop size, a small desktop size and a phone size. Fix what you see: clipped type, overlapping fixed elements, cramped panels, low contrast, entrance animations that break later states. Then show it with a short list of three to five things you want the user to judge, and a list of what is not done.

Iterate on this screen until the user approves it. Do not build further before that.

Gate 3: the user approves the first screen in the browser.

### Phase 4 · Grow the system from the approved screen

Every later section must answer "what does the one idea do here?" The object should change state or role, not be pasted again. The end of the page must differ from the start by a state change of the same idea, never by copying it. Reuse the tokens the first screen established; add no new material, radius, or type family without a reason.

Handle depth with structure, not length: a few featured pieces on the home page, the rest in an index. Keep body text on a stable reading surface; only display-size type may sit on imagery.

### Phase 5 · Validate and record

Run `references/quality-checklist.md`. Write a README that lists the idea in one sentence, how to run the site, every figure with its source and check date, what is stylised or a recreation, and what is not final. Say plainly what was not verified.

## How to talk to the user

- Lead with the judgment, then the evidence. Cite references by name and observation.
- When you were wrong, say so in one sentence and move on. Users give better feedback to an honest assistant.
- Show real things quickly. A ten-minute HTML draft beats an hour of prose.
- Before each reveal, list three to five specific things to judge and the known gaps.
- Treat the user's strong reactions ("this looks like an admin panel", "I need to be on the first screen") as design constraints and write them down.

## Honesty rules

- Every number, role and claim on the page traces to a source. Verify with an API or a document, not memory.
- No invented slogans, issue numbers, testimonials, logos or "as seen in".
- Stylised recreations of other products' surfaces (a chat, a terminal, a newspaper) are fine when labelled as stylised and free of brand assets.
- Do not import employer code, private data or credentials into a personal site.

## Files

- `references/reference-library.md`: collection sites, specific pages, how to read them, what to do when the user has no references.
- `references/idea-vocabulary.md`: families of ideas with examples, the derivation worksheet, the anti-convergence check.
- `references/quality-checklist.md`: detail standards, anti-patterns, validation steps.
- `references/worked-example.md`: one full run, three failures and what finally worked. Read for the method, not for the outcome.
