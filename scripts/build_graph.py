"""
full-year contribution heatmap.

rendered from the graphql contributionCalendar, which - when the workflow token
belongs to soham - includes private contribution counts. that is the whole point
of generating this ourselves: the stock profile graph hides ~840 private commits.

falls back to the last cached calendar if the api is unreachable.
"""
from datetime import date, datetime

from common import (ASSETS, USER, cache_read, cache_write, esc, graphql, log,
                    panel, text, titlebar, write_svg)

W = 860
CELL, GAP = 11, 3
STEP = CELL + GAP
PAD_L, PAD_T = 42, 62      # room for day labels / month labels
H = 246

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount weekday }
        }
      }
    }
  }
}
"""

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun",
          "jul", "aug", "sep", "oct", "nov", "dec"]


def fetch():
    data = graphql(QUERY, login=USER)
    try:
        cal = data["user"]["contributionsCollection"]["contributionCalendar"]
        weeks = [
            [(d["date"], d["contributionCount"]) for d in w["contributionDays"]]
            for w in cal["weeks"]
        ]
        payload = {"total": cal["totalContributions"], "weeks": weeks}
        cache_write("calendar", payload)
        return payload
    except Exception as e:  # noqa: BLE001
        log(f"calendar fetch failed ({e}); using cache")
        return cache_read("calendar", {"total": 0, "weeks": []})


def level(count, peak):
    """bucket a day's count into one of 5 heat steps, scaled to this user's peak."""
    if count <= 0:
        return 0
    if peak <= 4:
        return min(4, count)
    q = count / peak
    if q <= 0.25:
        return 1
    if q <= 0.50:
        return 2
    if q <= 0.75:
        return 3
    return 4


def streaks(days):
    """days = [(iso_date, count)] in chronological order."""
    longest = cur = 0
    today = date.today()
    for iso, c in days:
        if c > 0:
            cur += 1
            longest = max(longest, cur)
        else:
            # an empty *today* shouldn't break a streak that is still alive
            if datetime.strptime(iso, "%Y-%m-%d").date() != today:
                cur = 0
    return cur, longest


def build_factory(cal):
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w]
    counts = [c for _, c in days]
    peak = max(counts) if counts else 0
    total = cal["total"]
    cur_streak, best_streak = streaks(days)
    active = sum(1 for c in counts if c > 0)
    last30 = sum(c for _, c in days[-30:])

    def build(t):
        parts = [panel(t, W, H), titlebar(t, W, "contributions.svg — last 12 months")]

        # ---- month labels along the top
        seen = set()
        for wi, week in enumerate(weeks):
            if not week:
                continue
            d = datetime.strptime(week[0][0], "%Y-%m-%d").date()
            key = (d.year, d.month)
            if d.day <= 7 and key not in seen:
                seen.add(key)
                parts.append(
                    text(MONTHS[d.month - 1], PAD_L + wi * STEP, PAD_T - 8, t.dim, 10)
                )

        # ---- weekday labels down the left
        for wd, lbl in ((1, "mon"), (3, "wed"), (5, "fri")):
            parts.append(
                text(lbl, PAD_L - 9, PAD_T + wd * STEP + CELL - 1, t.dim, 10, anchor="end")
            )

        # ---- the grid, revealed as a diagonal wave
        for wi, week in enumerate(weeks):
            for di, (iso, count) in enumerate(week):
                lv = level(count, peak)
                x = PAD_L + wi * STEP
                y = PAD_T + di * STEP
                delay = 0.25 + (wi + di) * 0.012
                plural = "" if count == 1 else "s"
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                    f'fill="{t.levels[lv]}" opacity="0">'
                    f'<animate attributeName="opacity" from="0" to="1" dur="0.35s" '
                    f'begin="{delay:.2f}s" fill="freeze"/>'
                    f"<title>{esc(f'{count} contribution{plural} on {iso}')}</title>"
                    f"</rect>"
                )

        grid_bottom = PAD_T + 7 * STEP + 12

        # ---- stat readout
        # deliberately no "current streak" here - it reads 0 on any ordinary day off
        # and says nothing useful. trailing-30 is the honest momentum number.
        stats = [
            (f"{total:,}", "contributions"),
            (f"{last30:,}", "last 30 days"),
            (f"{best_streak}", "longest streak"),
            (f"{active}", "active days"),
            (f"{peak}", "busiest day"),
        ]
        sx = PAD_L
        for i, (val, lbl) in enumerate(stats):
            parts.append(
                f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" '
                f'dur="0.5s" begin="{1.0 + i * 0.09:.2f}s" fill="freeze"/>'
                + text(val, sx, grid_bottom + 16, t.text, 17, weight="bold")
                + text(lbl, sx, grid_bottom + 31, t.dim, 10)
                + "</g>"
            )
            sx += 132

        # ---- legend, bottom right
        lx = W - 26 - 5 * STEP - 60
        parts.append(text("less", lx - 6, grid_bottom + 24, t.dim, 10, anchor="end"))
        for i in range(5):
            parts.append(
                f'<rect x="{lx + i * STEP}" y="{grid_bottom + 15}" width="{CELL}" '
                f'height="{CELL}" rx="2.5" fill="{t.levels[i]}"/>'
            )
        parts.append(
            text("more", lx + 5 * STEP + 6, grid_bottom + 24, t.dim, 10)
        )
        return "".join(parts)

    return build


if __name__ == "__main__":
    cal = fetch()
    n_weeks = len(cal["weeks"])
    width = max(W, PAD_L + n_weeks * STEP + 26)
    write_svg("graph", build_factory(cal), width, H)
    log(f"graph built · {cal['total']} contributions across {n_weeks} weeks")
