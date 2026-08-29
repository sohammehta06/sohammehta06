# setup

this repo renders my github profile. everything visible on the profile is an svg
generated from the github api by `scripts/` and committed by a workflow. there are
no third-party badge services in the readme — nothing to rate-limit, nothing to
break when someone else's free tier runs out.

## layout

```
scripts/
  common.py          api client, colour palettes, svg primitives. nothing here raises.
  build_header.py    animated terminal header (smil typewriter)
  build_graph.py     full-year contribution heatmap + streak maths
  build_stats.py     stats readout + language breakdown
  update_readme.py   splices the activity log and NOW.md into README.md
assets/
  *-dark.svg         emitted per theme; readme picks with <picture>
  .cache/*.json      last good api payload, so a failed run still renders real data
```

each builder writes a `-dark` and a `-light` variant. the readme selects between
them with `prefers-color-scheme`, so it looks right in both github themes.

## the token

`GH_TOKEN` is a fine-grained PAT. it is what lets the graph include **private**
contributions — without it the profile shows only the ~30% of the work that
happens in public repos.

> **fine-grained tokens expire, and github does not warn you.**
> this is exactly what happened before: the token expired on ~17 aug, every
> scheduled run failed with a 401 for eleven days, and the profile silently froze
> with a stale build date and an empty activity log.

two guards are now in place:

1. the workflow pings the api before building and writes a `::warning::` into the
   run summary if the token is rejected — so it shows up on the actions page
   instead of hiding inside a stack trace.
2. no script raises. on a 401 they fall back to `GITHUB_TOKEN`, then to
   `assets/.cache/`, and the build still goes green with the last good data.

### regenerating it

- https://github.com/settings/tokens?type=beta
- repository access: only `sohammehta06/sohammehta06`
- permissions: **account → read:user**, **repository → contents: read/write**
- set the longest expiry offered, put a reminder in the calendar for a week before
- repo → settings → secrets and variables → actions → update `GH_TOKEN`

## running it locally

```bash
export GH_TOKEN=$(gh auth token)
python scripts/build_header.py
python scripts/build_graph.py
python scripts/build_stats.py
python scripts/update_readme.py
open preview.html          # renders all widgets in both themes
```

`preview.html` is a local harness only — it is not part of the published profile.

## editing content

- **NOW.md** — the "currently" block. edit this file; the workflow splices it in.
- the `~/work`, `principles.txt` and `contact` blocks are hand-written in `README.md`.
- typing speed / lines of the header are the `SCRIPT` list in `build_header.py`.
- colours live in `DARK` / `LIGHT` in `common.py` and nowhere else.

## one gotcha worth remembering

the language card does **not** sum raw bytes. `jitsu-lab` alone carries ~200 mb of
generated html and a vendored venv, which would otherwise make the profile claim
soham writes 96% html. instead each repo is normalised to its own language mix and
weighted by `log10(bytes)`, so a big project still counts for more than a scratch
repo but no single repo can define the profile. see the comment in `build_stats.py`.
