"""
the profile's only graphic.

deliberately a ledger, not a bio. no adjectives, no self-description, no badges -
just institutions and outcomes stacked densely enough that the reader draws their
own conclusion. exactly one thing is emphasised in accent colour; everything else
is the same weight, which is what keeps it from reading as a flex.

one typed line ($ whoami) justifies the terminal frame, then the ledger fades in
as its output. the whole sequence is done in ~1.4s - fast enough that nobody
watches it happen, slow enough to register as craft.
"""
from common import esc, log, panel, text, titlebar, write_svg

W, H = 860, 272
CW, FS = 8.4, 14
X0 = 26

CMD = "whoami"

NAME = "soham mehta"
SUB = "growth @ jitsu (yc s20) · the open-source collection layer"

# (label, value, detail, emphasise_detail)
# every string below traces to something soham said directly. do not infer a
# role, a title or an outcome from a repo, an email domain or a company's
# reputation - if it was not stated, it does not go on the profile.
LEDGER = [
    ("now",    "jitsu (yc s20)",      "growth · open-source event pipeline", False),
    ("before", "gooseworks (yc w23)", "founders' office", False),
    ("",       "lyzr ai",             "founders' office · product + gtm", False),
    ("own",    "bootstrapped saas",   "$120k arr · profitable from day one", True),
]

COL_LABEL, COL_VALUE, COL_DETAIL = X0, 104, 330
ROW_Y, ROW_STEP = 178, 22


def build(t):
    p = [panel(t, W, H), titlebar(t, W, "soham@jitsu — zsh")]

    # --- the one typed line
    line = f"$ {CMD}"
    n = len(line)
    dur = n / 46.0
    steps = ";".join(str(round(k * CW, 2)) for k in range(n + 1))
    p.append(
        f'<clipPath id="cmd{t.name}"><rect x="{X0}" y="{70 - FS}" height="{FS + 8}" width="0">'
        f'<animate attributeName="width" values="{steps}" calcMode="discrete" '
        f'dur="{dur:.2f}s" begin="0.25s" fill="freeze"/></rect></clipPath>'
        f'<g clip-path="url(#cmd{t.name})">'
        f'<text x="{X0}" y="70" font-size="{FS}" fill="{t.text}" '
        f'textLength="{n * CW:.1f}" lengthAdjust="spacing" xml:space="preserve">'
        f'<tspan fill="{t.accent}" font-weight="bold">$ </tspan>{esc(CMD)}</text></g>'
    )

    after = 0.25 + dur + 0.12

    def reveal(delay, inner):
        return (f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" '
                f'dur="0.45s" begin="{delay:.2f}s" fill="freeze"/>{inner}</g>')

    # --- identity
    p.append(reveal(after, text(NAME, X0, 108, t.text, 19, weight="600")))
    p.append(reveal(after + 0.08, text(SUB, X0, 130, t.dim, 12.5)))
    p.append(reveal(
        after + 0.14,
        f'<line x1="{X0}" y1="150" x2="{W - X0}" y2="150" stroke="{t.border}"/>'
    ))

    # --- the ledger
    for i, (label, value, detail, emph) in enumerate(LEDGER):
        y = ROW_Y + i * ROW_STEP
        inner = (
            text(label, COL_LABEL, y, t.dim, 11)
            + text(value, COL_VALUE, y, t.text, 13)
            + text(detail, COL_DETAIL, y, t.accent if emph else t.dim, 12.5)
        )
        p.append(reveal(after + 0.22 + i * 0.08, inner))

    # --- caret, the single wink at the terminal conceit
    end = after + 0.22 + len(LEDGER) * 0.08
    p.append(
        f'<rect x="{X0 + (len(CMD) + 2) * CW + 2:.1f}" y="{70 - FS + 2}" '
        f'width="{CW:.1f}" height="{FS + 2}" fill="{t.accent}" opacity="0">'
        f'<animate attributeName="opacity" values="1;1;0;0" dur="1.06s" '
        f'begin="{end:.2f}s" repeatCount="indefinite"/></rect>'
    )
    return "".join(p)


if __name__ == "__main__":
    write_svg("header", build, W, H)
    log("header built")
