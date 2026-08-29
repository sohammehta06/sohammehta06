"""
refreshes the text sections of the readme: the live activity log and the
now block. runs after the svg builders.

the previous version of this script raised on a 401 and took the whole workflow
red for eleven days straight. nothing here raises: every section falls back to
whatever was rendered last time, and the build stays green.
"""
import re
from datetime import datetime, timezone
from pathlib import Path

from common import USER, cache_read, cache_write, log, rest

README = Path("README.md")
NOW = Path("NOW.md")

VERB = {
    "PushEvent": "push",
    "CreateEvent": "create",
    "PullRequestEvent": "pr",
    "IssuesEvent": "issue",
    "WatchEvent": "star",
    "ForkEvent": "fork",
    "ReleaseEvent": "release",
    "PublicEvent": "public",
}


def relative(iso):
    then = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    s = int((datetime.now(timezone.utc) - then).total_seconds())
    if s < 3600:
        return f"{max(s // 60, 1)}m ago"
    if s < 86400:
        return f"{s // 3600}h ago"
    if s < 2592000:
        return f"{s // 86400}d ago"
    return f"{s // 2592000}mo ago"


def describe(e):
    """one terminal-log line per event, or None to skip it."""
    kind = e.get("type")
    repo = e.get("repo", {}).get("name", "").split("/")[-1]
    payload = e.get("payload", {})

    if kind == "PushEvent":
        commits = payload.get("commits") or []
        if not commits:
            return None
        return commits[-1]["message"].split("\n")[0][:58]
    if kind == "PullRequestEvent":
        pr = payload.get("pull_request") or {}
        return f"{payload.get('action', '')} #{pr.get('number', '')} {pr.get('title') or ''}"[:58]
    if kind == "IssuesEvent":
        iss = payload.get("issue") or {}
        return f"{payload.get('action', '')} #{iss.get('number', '')} {iss.get('title') or ''}"[:58]
    if kind == "ReleaseEvent":
        return (payload.get("release") or {}).get("tag_name", "release")
    # CreateEvent / ForkEvent / WatchEvent are deliberately dropped: branch
    # creations and forks bury the actual work under three lines of bookkeeping.
    return None


def activity_block():
    events = rest(f"/users/{USER}/events/public")
    lines = []
    if events:
        for e in events:
            desc = describe(e)
            if not desc:
                continue
            repo = e["repo"]["name"].split("/")[-1]
            verb = VERB.get(e["type"], e["type"].replace("Event", "").lower())
            lines.append(
                f"  {relative(e['created_at']):<9} {verb:<8} {repo:<26} {desc}".rstrip()
            )
            if len(lines) == 7:
                break
        if lines:
            cache_write("activity", lines)

    if not lines:
        lines = cache_read("activity", [])
    if not lines:
        lines = ["  (github api unreachable this run — showing nothing rather than guessing)"]

    return "```\n$ tail -n 7 ~/.activity.log\n" + "\n".join(lines) + "\n```"


def now_block():
    body = NOW.read_text().rstrip() if NOW.exists() else "  (nothing set)"
    return "```\n$ cat NOW.md\n" + body + "\n```"


def splice(text, tag, content):
    pattern = re.compile(
        rf"(<!--START_SECTION:{tag}-->).*?(<!--END_SECTION:{tag}-->)", re.S
    )
    if not pattern.search(text):
        log(f"marker for '{tag}' not found — skipping")
        return text
    return pattern.sub(lambda m: f"{m.group(1)}\n{content}\n{m.group(2)}", text)


def main():
    text = README.read_text()
    text = splice(text, "activity", activity_block())
    text = splice(text, "now", now_block())

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    text = re.sub(
        r"(<!--BUILD_TIME-->).*?(<!--/BUILD_TIME-->)",
        lambda m: f"{m.group(1)}{stamp}{m.group(2)}",
        text,
        flags=re.S,
    )

    README.write_text(text)
    log(f"readme spliced · {stamp}")


if __name__ == "__main__":
    main()
