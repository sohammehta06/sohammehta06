"""
shared helpers: github api access, theme palettes, svg primitives.

every builder in this folder emits two svgs (dark + light) so the readme can
switch with <picture media="(prefers-color-scheme: dark)">.

nothing in here is allowed to raise. if the api is down or the token expired,
builders fall back to cached data and the workflow still goes green.
"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

USER = "sohammehta06"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
ASSETS = Path("assets")
CACHE = Path("assets/.cache")

FONT = "ui-monospace,'SF Mono',SFMono-Regular,'JetBrains Mono',Menlo,Consolas,monospace"


# ---------------------------------------------------------------- palettes

class Theme:
    def __init__(self, name, bg, panel, border, text, dim, accent, accent2, levels):
        self.name = name
        self.bg = bg
        self.panel = panel
        self.border = border
        self.text = text
        self.dim = dim
        self.accent = accent
        self.accent2 = accent2
        self.levels = levels  # 5 heatmap steps, index 0 = empty


DARK = Theme(
    name="dark",
    bg="#0d1117",
    panel="#0d1117",
    border="#30363d",
    text="#e6edf3",
    dim="#7d8590",
    accent="#3fb950",
    accent2="#58a6ff",
    levels=["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
)

LIGHT = Theme(
    name="light",
    bg="#ffffff",
    panel="#ffffff",
    border="#d1d9e0",
    text="#1f2328",
    dim="#59636e",
    accent="#1a7f37",
    accent2="#0969da",
    levels=["#eff2f5", "#aceebb", "#4ac26b", "#2da44e", "#116329"],
)

THEMES = (DARK, LIGHT)


# ---------------------------------------------------------------- api

def _request(url, data=None, headers=None):
    hdrs = {"User-Agent": f"{USER}-readme", "Accept": "application/vnd.github+json"}
    if TOKEN:
        hdrs["Authorization"] = f"Bearer {TOKEN}"
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def rest(path):
    """GET a REST endpoint. returns None on any failure."""
    try:
        return _request(f"https://api.github.com{path}")
    except Exception as e:  # noqa: BLE001 - never fail the build
        log(f"rest {path} failed: {e}")
        return None


def graphql(query, **variables):
    """POST a graphql query. returns the `data` object, or None on failure."""
    if not TOKEN:
        log("graphql skipped: no token")
        return None
    body = json.dumps({"query": query, "variables": variables}).encode()
    try:
        out = _request(
            "https://api.github.com/graphql",
            data=body,
            headers={"Content-Type": "application/json"},
        )
    except Exception as e:  # noqa: BLE001
        log(f"graphql failed: {e}")
        return None
    if out.get("errors"):
        log(f"graphql errors: {out['errors']}")
    return out.get("data")


# ---------------------------------------------------------------- cache

def cache_write(name, obj):
    """persist the last good payload so a failed run still renders real data."""
    try:
        CACHE.mkdir(parents=True, exist_ok=True)
        (CACHE / f"{name}.json").write_text(json.dumps(obj))
    except Exception as e:  # noqa: BLE001
        log(f"cache write {name} failed: {e}")


def cache_read(name, default=None):
    try:
        p = CACHE / f"{name}.json"
        if p.exists():
            return json.loads(p.read_text())
    except Exception as e:  # noqa: BLE001
        log(f"cache read {name} failed: {e}")
    return default


def log(msg):
    print(f"  · {msg}", flush=True)


# ---------------------------------------------------------------- svg

def esc(s):
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_svg(basename, body_fn, width, height):
    """
    render `body_fn(theme) -> str` once per theme and write
    assets/<basename>-dark.svg and assets/<basename>-light.svg
    """
    ASSETS.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" '
            f'font-family="{FONT}" role="img">'
            f"{body_fn(theme)}"
            f"</svg>"
        )
        (ASSETS / f"{basename}-{theme.name}.svg").write_text(svg, encoding="utf-8")
    log(f"wrote {basename}-{{dark,light}}.svg  ({width}x{height})")


def panel(t, w, h, x=0, y=0, r=6):
    """the rounded terminal frame every card sits in."""
    return (
        f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{w - 1}" height="{h - 1}" '
        f'rx="{r}" fill="{t.panel}" stroke="{t.border}"/>'
    )


def titlebar(t, w, label, x=0, y=0):
    """mac-style traffic lights + a filename, drawn at the top of a panel."""
    dots = "".join(
        f'<circle cx="{x + 18 + i * 15}" cy="{y + 17}" r="4.5" fill="{c}" opacity="0.9"/>'
        for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840"))
    )
    return (
        dots
        + f'<text x="{x + w / 2}" y="{y + 21}" fill="{t.dim}" font-size="11" '
        f'text-anchor="middle">{esc(label)}</text>'
        + f'<line x1="{x}" y1="{y + 34}" x2="{x + w}" y2="{y + 34}" stroke="{t.border}"/>'
    )


def text(s, x, y, fill, size=12, anchor="start", weight="normal", opacity=None, extra=""):
    op = f' opacity="{opacity}"' if opacity is not None else ""
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
        f'text-anchor="{anchor}" font-weight="{weight}"{op}{extra}>{esc(s)}</text>'
    )


def fade_in(delay, dur=0.5):
    """a reusable css-free fade, safe inside <img>-embedded svg on github."""
    return (
        f'<animate attributeName="opacity" from="0" to="1" '
        f'dur="{dur}s" begin="{delay}s" fill="freeze"/>'
    )
