# Reference library

Users who are engineers often have no design references. This library exists so the skill can still look at good work before proposing anything. Availability and content of external sites change; verify before citing, and never claim to have seen something you did not open.

## How to read a reference

For each site or entry:

1. Open it in a browser you control (agent-browser, Playwright, or the user's browser via a screenshot). Take screenshots at the top and at two scroll positions. Static gallery frames prove less than a live page; say which you saw.
2. Write one line each for: the single object or move; type scale and where the biggest type sits; what surface the body text sits on; how sections hand over to each other; what changes between the start and the end of the page.
3. After five or more, write the principle they share in one or two sentences. That principle, not any single site, is what you carry into the design.

Commands that work with agent-browser:

```sh
agent-browser --session ref open <url>
agent-browser --session ref set viewport 1440 900
agent-browser --session ref wait --load networkidle
agent-browser --session ref screenshot ref-top.png
agent-browser --session ref eval "window.scrollTo(0, 900)"
agent-browser --session ref screenshot ref-mid.png
agent-browser --session ref close
```

## Collection sites (start here when the user has no references)

| Site | What it is good for | Notes |
| --- | --- | --- |
| Details.so Inspo, https://www.details.so/inspo | Real websites tagged by element: hero, footer, navigation, scroll animations, page and section transitions. Filter by the problem you are solving. | Some entries are video-only; open the live site when the entry links to it. |
| Inspora, https://www.inspora.design/ | Motion and interaction clips curated from X: menus, 3D cards, transitions. | Clips are demos, not full sites. Credit authors if you mention one. |
| Design on X / Northlight, https://design-on-x.com/ | Portfolio and motion posts curated from X, with a portfolios filter. | Mix of concepts and shipped sites; check which. |
| Awwwards, https://www.awwwards.com/ | Long-running showcase of high-craft sites. Sort by "sites of the day". | Trend-heavy; use for craft, not for copying. |
| Godly, https://godly.website/ | Curated modern landing pages, quick to scan. | Verify availability. |
| Land-book, https://land-book.com/ | Landing pages by category and style. | Broad; useful for product pages. |
| Siteinspire, https://www.siteinspire.com/ | Editorial and typographic sites, filter by style and type. | Good for type-led ideas. |
| Minimal Gallery, https://minimal.gallery/ | Restraint, whitespace, editorial rhythm. | Good antidote to clutter. |

## Specific pages studied while building this skill

These were actually opened and screenshotted in September 2026. Each teaches one thing; none is a template.

| Reference | What was observed | What it teaches |
| --- | --- | --- |
| Code Storage, https://code.storage/ | One voice: monospace text like a README, chrome 3D objects hanging on a dotted line down the page, ASCII tables for limits. Not a single card. | Content, object and typography can be one language. The object is the identity. |
| Exo Ape, https://www.exoape.com/ | Full-bleed photography, giant sans type crossing the image edge, dark blocks that take over sections, long case narratives. | One idea per screen. Display type may cross imagery. Section takeover as the transition. |
| Dia browser, https://www.diabrowser.com/ | Dark portrait hero, then bright paper, large serif headlines, a product frame that holds painterly art as content. | Imagery belongs inside a frame; body text belongs on paper. |
| Artem portfolio (Details entry) | Black canvas, bold rounded type, green hand-drawn lines animating around the words. | Personality from one drawing style, applied everywhere. |
| Inori, https://lnkiai.com/ | Warm paper, one featured card with a "GitHub Trending #1" proof line, timeline, links. | Proof as a typographic element. Clear hierarchy in a small page. Also shows the limit: it reads as a profile page, not a world. |
| Yoshik, https://yoshik-pc.vercel.app/ | A "Click start" screen, BIOS sequence, then a 3D room. | A world you enter is memorable, and each step costs the visitor. Use with care. |
| Mike Barton airplane-window portfolio (Northlight entry) | A minimal page with a single airplane window; sky inside; light and dark modes shift through it. | One familiar object can carry a whole identity. |
| Polaroid navigation by Matthias Oel (Northlight entry) | A compact nav that expands into a moving row of work previews. | Let people see the work before scrolling. |
| Airtable Airspace (user screenshot) | Sky as a continuous field; white geometric page blocks cut into it from above; big type and small bright shapes organise the section. | Scenery needs an edge and a role; it is not wallpaper. |
| Dia pricing (user screenshot) | Continuous painted sky; three white cards with consistent radius and spacing; text lives on the cards. | Reading layer stays stable while the background carries mood. |

## What the good ones share

One strong idea, executed with consistency. The object, the type and the rhythm are the protagonists; cards and panels are supporting cast. None of them is a grid of equal cards. Most have a clear beginning and an ending that differs from the beginning.

## When the user does have references

Ask for the links or screenshots, open them, and read them with the same protocol. Ask one question only: "What in this one do you like: the object, the type, the motion, the mood?" Do not ask a taste questionnaire. Their references outrank this library.
