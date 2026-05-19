# setup

quick guide to ship this. takes ~10 minutes.

## 1. create the repo

your github profile readme lives in a repo named exactly the same as your username:

```
https://github.com/sohammehta06/sohammehta06
```

create it. mark it public. add a readme on creation, then we overwrite.

## 2. drop these files in

push everything in this folder to that repo. structure:

```
sohammehta06/
├── README.md
├── NOW.md
├── .github/workflows/
│   ├── rebuild.yml
│   └── snake.yml
├── scripts/
│   ├── update_readme.py
│   └── build_graph.py
└── assets/
    ├── graph-light.svg
    └── graph-dark.svg
```

## 3. add a personal access token

the rebuild action needs a token to read private contribution counts and your activity. otherwise it falls back to public-only.

- go to https://github.com/settings/tokens?type=beta
- generate a fine-grained token
- repository access: only `sohammehta06/sohammehta06`
- permissions needed:
  - **account**: `read:user` (contribution data)
  - **repository**: `contents: read/write` (to commit the rebuilt readme)
- copy the token
- in the repo, go to settings → secrets and variables → actions → new repository secret
- name it `GH_TOKEN`, paste the token

## 4. enable actions

settings → actions → general → allow all actions. also under workflow permissions, pick "read and write."

## 5. trigger first build

go to actions tab → rebuild readme → run workflow. watch it commit a fresh build.

snake action runs daily on its own. you can also trigger it manually the first time.

## customising

- edit `NOW.md` to change the "currently" section without code
- the principles block, contact block, whoami block are all in `README.md` - hand-edit
- if you want the activity log to show private repos too, the token covers that already
- contribution count counts last 180 days. change the timedelta in `build_graph.py` if you want a year

## bumping the look later

things you could add when you have spare cycles:

- a weekly metrics svg (lines added/deleted, top language, longest streak)
- a "currently reading" block that pulls from a goodreads/readwise rss
- a writeup-of-the-week section pulled from your blog rss
- a tiny terminal-style "ask me anything" widget linking to a tally form

keep the bar high. anything you add should look like it belongs.
