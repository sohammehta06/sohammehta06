"""
two side-by-side cards: a stats readout and a language breakdown.

both are computed from the graphql api over *all* owned repos, private included,
so the language split reflects what soham actually writes rather than only what
happens to be public. forks are excluded - they aren't his code.
"""
from common import (USER, cache_read, cache_write, graphql, log, panel, text,
                    titlebar, write_svg)

CW, CH = 424, 252   # two of these sit side by side under the 860px header

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar { totalContributions }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""

# languages that inflate the numbers without saying anything about the work
IGNORE = {"HTML", "CSS", "SCSS", "Shell", "Dockerfile", "Makefile", "Procfile"}


def fetch():
    data = graphql(QUERY, login=USER)
    try:
        u = data["user"]
        c = u["contributionsCollection"]
        repos = u["repositories"]["nodes"]

        # naive byte-summing is worthless here: jitsu-lab alone carries ~200mb of
        # generated render output and a vendored venv, which would drown out every
        # hand-written repo. so each repo is normalised to its own language mix,
        # then weighted by log(bytes) - a big project still counts for more than a
        # scratch repo, but no single repo can define the whole profile.
        import math

        by_lang = {}
        stars = 0
        for r in repos:
            stars += r["stargazerCount"]
            edges = [e for e in (r["languages"]["edges"] or [])
                     if e["node"]["name"] not in IGNORE]
            repo_total = sum(e["size"] for e in edges)
            if not repo_total:
                continue
            weight = math.log10(repo_total)
            for e in edges:
                nm = e["node"]["name"]
                slot = by_lang.setdefault(nm, {"size": 0.0, "color": e["node"]["color"]})
                slot["size"] += (e["size"] / repo_total) * weight

        payload = {
            # restrictedContributionsCount is every contribution in a private repo -
            # commits, prs, issues, reviews - so it gets its own honest row rather
            # than being folded into a "commits" total it would overstate.
            "stats": [
                ("contributions", c["contributionCalendar"]["totalContributions"]),
                ("public commits", c["totalCommitContributions"]),
                ("private contributions", c["restrictedContributionsCount"]),
                ("pull requests", c["totalPullRequestContributions"]),
                ("issues opened", c["totalIssueContributions"]),
                ("repositories", u["repositories"]["totalCount"]),
            ],
            # drop anything under half a percent - a legend row reading "0.0%"
            # is noise, not information
            "langs": [
                row for row in sorted(
                    ([k, v["size"], v["color"] or "#8b949e"] for k, v in by_lang.items()),
                    key=lambda r: -r[1],
                )[:6]
                if by_lang and row[1] / sum(v["size"] for v in by_lang.values()) >= 0.005
            ],
            "repo_count": len([r for r in repos if r["languages"]["edges"]]),
        }
        cache_write("stats", payload)
        return payload
    except Exception as e:  # noqa: BLE001
        log(f"stats fetch failed ({e}); using cache")
        return cache_read("stats", {"stats": [], "langs": [], "repo_count": 0})


# ------------------------------------------------------------------ card 1

def stats_factory(rows):
    peak = max((v for _, v in rows), default=1) or 1

    def build(t):
        parts = [panel(t, CW, CH), titlebar(t, CW, "stats.json")]
        y = 62
        for i, (label, value) in enumerate(rows):
            delay = 0.3 + i * 0.08
            # a hairline bar behind each row, scaled log-ish so small values stay visible
            frac = (value / peak) ** 0.55 if peak else 0
            bw = max(2, frac * 128)
            parts.append(
                f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" '
                f'dur="0.45s" begin="{delay:.2f}s" fill="freeze"/>'
                + text(label, 22, y, t.dim, 12)
                + f'<rect x="{CW - 218}" y="{y - 8}" width="128" height="6" rx="3" '
                  f'fill="{t.levels[0]}"/>'
                + f'<rect x="{CW - 218}" y="{y - 8}" width="0" height="6" rx="3" '
                  f'fill="{t.accent}">'
                  f'<animate attributeName="width" from="0" to="{bw:.1f}" dur="0.7s" '
                  f'begin="{delay + 0.1:.2f}s" fill="freeze" '
                  f'calcMode="spline" keySplines="0.2 0.8 0.2 1"/></rect>'
                + text(f"{value:,}", CW - 22, y, t.text, 13, anchor="end", weight="bold")
                + "</g>"
            )
            y += 26
        return "".join(parts)

    return build


# ------------------------------------------------------------------ card 2

def langs_factory(langs, repo_count):
    total = sum(s for _, s, _ in langs) or 1

    def build(t):
        parts = [panel(t, CW, CH), titlebar(t, CW, "languages — normalised per repo")]

        # stacked bar
        bx, by, bw, bh = 22, 58, CW - 44, 14
        parts.append(
            f'<clipPath id="lb{t.name}"><rect x="{bx}" y="{by}" width="{bw}" '
            f'height="{bh}" rx="7"/></clipPath>'
        )
        parts.append(f'<g clip-path="url(#lb{t.name})">')
        parts.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{t.levels[0]}"/>')
        off = 0.0
        for i, (name, size, color) in enumerate(langs):
            seg = size / total * bw
            parts.append(
                f'<rect x="{bx + off:.1f}" y="{by}" width="0" height="{bh}" fill="{color}">'
                f'<animate attributeName="width" from="0" to="{seg:.1f}" dur="0.6s" '
                f'begin="{0.35 + i * 0.1:.2f}s" fill="freeze" '
                f'calcMode="spline" keySplines="0.2 0.8 0.2 1"/></rect>'
            )
            off += seg
        parts.append("</g>")

        # two-column legend
        y = 108
        for i, (name, size, color) in enumerate(langs):
            col = i % 2
            row = i // 2
            x = 22 + col * (bw / 2)
            yy = y + row * 30
            pct = size / total * 100
            parts.append(
                f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" '
                f'dur="0.45s" begin="{0.7 + i * 0.07:.2f}s" fill="freeze"/>'
                + f'<circle cx="{x + 5}" cy="{yy - 4}" r="5" fill="{color}"/>'
                + text(name, x + 17, yy, t.text, 12)
                + text(f"{pct:.1f}%", x + bw / 2 - 24, yy, t.dim, 11, anchor="end")
                + "</g>"
            )

        parts.append(
            text(f"across {repo_count} repos · weighted so no single repo skews the mix",
                 22, CH - 18, t.dim, 10)
        )
        return "".join(parts)

    return build


if __name__ == "__main__":
    d = fetch()
    if d["stats"]:
        write_svg("stats", stats_factory(d["stats"]), CW, CH)
    if d["langs"]:
        write_svg("langs", langs_factory(d["langs"], d.get("repo_count", 0)), CW, CH)
    log("stats + langs built")
