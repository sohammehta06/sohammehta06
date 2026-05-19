"""
rebuilds README dynamic sections from github activity.
runs on a cron via github actions.
"""
import os
import re
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USER = "sohammehta06"
TOKEN = os.environ.get("GH_TOKEN", "")
README = Path("README.md")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": f"{USER}-readme-bot",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def gh(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def relative_time(iso_ts):
    then = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    delta = datetime.now(timezone.utc) - then
    s = int(delta.total_seconds())
    if s < 60:
        return f"{s}s ago"
    if s < 3600:
        return f"{s // 60}m ago"
    if s < 86400:
        return f"{s // 3600}h ago"
    return f"{s // 86400}d ago"


def latest_activity():
    """grab recent public events and format like a terminal log"""
    try:
        events = gh(f"https://api.github.com/users/{USER}/events/public")[:8]
    except Exception:
        return "```\n$ tail -f activity.log\n  (offline - rate limited or no events)\n```"

    lines = []
    for e in events:
        t = relative_time(e["created_at"])
        repo = e["repo"]["name"].split("/")[-1]

        if e["type"] == "PushEvent":
            commits = e["payload"].get("commits", [])
            if not commits:
                continue
            msg = commits[-1]["message"].split("\n")[0][:60]
            lines.append(f"  {t:<8}  push    {repo:<24}  {msg}")
        elif e["type"] == "CreateEvent":
            ref_type = e["payload"].get("ref_type", "")
            ref = e["payload"].get("ref") or ref_type
            lines.append(f"  {t:<8}  create  {repo:<24}  {ref}")
        elif e["type"] == "PullRequestEvent":
            action = e["payload"]["action"]
            title = e["payload"]["pull_request"]["title"][:60]
            lines.append(f"  {t:<8}  pr      {repo:<24}  {action}: {title}")
        elif e["type"] == "IssuesEvent":
            action = e["payload"]["action"]
            title = e["payload"]["issue"]["title"][:60]
            lines.append(f"  {t:<8}  issue   {repo:<24}  {action}: {title}")
        elif e["type"] == "WatchEvent":
            lines.append(f"  {t:<8}  star    {repo:<24}")
        elif e["type"] == "ForkEvent":
            lines.append(f"  {t:<8}  fork    {repo:<24}")
        if len(lines) >= 5:
            break

    if not lines:
        return "```\n$ tail -f activity.log\n  (no recent public activity)\n```"

    body = "\n".join(lines)
    return f"```\n$ tail -f activity.log\n{body}\n```"


def now_block():
    """static-ish 'currently' section - edit NOW.md to update without code change"""
    now_file = Path("NOW.md")
    if now_file.exists():
        content = now_file.read_text().strip()
    else:
        content = (
            "  building  · gooseworks (yc w24)\n"
            "  shipping  · agents for gtm workflows\n"
            "  reading   · papers on multi-agent coordination\n"
            "  open to   · oss collabs in the agent space"
        )
    return f"```\n$ cat now.txt\n{content}\n```"


def replace_section(text, tag, payload):
    pattern = re.compile(
        rf"(<!--START_SECTION:{tag}-->)(.*?)(<!--END_SECTION:{tag}-->)",
        re.DOTALL,
    )
    return pattern.sub(rf"\1\n{payload}\n\3", text)


def replace_build_time(text):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return re.sub(
        r"<!--BUILD_TIME-->.*?<!--/BUILD_TIME-->",
        f"<!--BUILD_TIME-->{ts}<!--/BUILD_TIME-->",
        text,
        flags=re.DOTALL,
    )


def main():
    text = README.read_text()
    text = replace_section(text, "now", now_block())
    text = replace_section(text, "activity", latest_activity())
    text = replace_build_time(text)
    README.write_text(text)
    print("README updated.")


if __name__ == "__main__":
    main()
