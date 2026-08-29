"""
animated terminal header.

types each line out character-by-character using a discrete clip-width animation,
which is the only technique that survives github's <img> sandbox (no js, no css
keyframes needed - pure smil). a block cursor tracks the caret and blinks on the
last line forever.
"""
from common import FONT, esc, fade_in, log, panel, text, titlebar, write_svg

W, H = 860, 300
CW = 8.4          # advance width of one char at font-size 14 in ui-monospace
FS = 14
X0 = 26           # left gutter
Y0 = 66           # first baseline
LH = 27           # line height
CPS = 95.0        # chars per second - fast enough to finish before anyone scrolls past
GAP = 0.13        # pause between lines

# (kind, content) - kind drives the colour.
#   prompt = "$ " + command, out = program output, ok = success line, blank = spacer
SCRIPT = [
    ("prompt", "whoami"),
    ("out", "soham mehta — growth @ jitsu (yc s20)"),
    ("blank", ""),
    ("prompt", "cat bio.txt"),
    ("out", "the open-source collection layer. before: gooseworks (yc w23), lyzr ai."),
    ("out", "bootstrapped my own saas to $120k arr, profitable from day one."),
    ("blank", ""),
    ("prompt", ""),
]


def build(t):
    parts = [panel(t, W, H), titlebar(t, W, "soham@jitsu — zsh — 86×12")]
    clock = 0.45  # let the frame settle before typing starts

    for i, (kind, content) in enumerate(SCRIPT):
        y = Y0 + i * LH
        if kind == "blank":
            clock += 0.12
            continue

        prefix = "$ " if kind == "prompt" else ""
        line = prefix + content
        n = len(line)
        dur = max(n / CPS, 0.05)
        width = n * CW
        cid = f"c{i}"

        # discrete clip reveal = one character per step, a real typewriter cadence
        steps = ";".join(f"{round(k * CW, 2)}" for k in range(n + 1))
        parts.append(
            f'<clipPath id="{cid}"><rect x="{X0}" y="{y - FS}" height="{FS + 8}" width="0">'
            f'<animate attributeName="width" values="{steps}" calcMode="discrete" '
            f'dur="{dur:.2f}s" begin="{clock:.2f}s" fill="freeze"/>'
            f"</rect></clipPath>"
        )

        colour = t.text if kind == "prompt" else t.dim
        body = (
            f'<g clip-path="url(#{cid})">'
            f'<text x="{X0}" y="{y}" font-size="{FS}" fill="{colour}" '
            f'textLength="{width:.1f}" lengthAdjust="spacing" xml:space="preserve">'
        )
        if kind == "prompt":
            body += f'<tspan fill="{t.accent}" font-weight="bold">$ </tspan>'
            body += f"<tspan>{esc(content)}</tspan>"
        else:
            body += esc(content)
        body += "</text></g>"
        parts.append(body)

        clock += dur + GAP

    # caret parks after the final command and blinks indefinitely
    last_i = len(SCRIPT) - 1
    caret_x = X0 + (len(SCRIPT[last_i][1]) + 2) * CW + 2
    caret_y = Y0 + last_i * LH
    parts.append(
        f'<rect x="{caret_x:.1f}" y="{caret_y - FS + 2}" width="{CW:.1f}" height="{FS + 2}" '
        f'fill="{t.accent}" opacity="0">'
        f'<animate attributeName="opacity" values="0;1" dur="0.01s" '
        f'begin="{clock:.2f}s" fill="freeze"/>'
        f'<animate attributeName="opacity" values="1;1;0;0" dur="1.06s" '
        f'begin="{clock + 0.05:.2f}s" repeatCount="indefinite"/>'
        f"</rect>"
    )

    # a quiet status strip along the bottom edge
    strip_y = H - 16
    parts.append(
        f'<g opacity="0">{fade_in(clock + 0.3, 0.6)}'
        + text("● live", X0, strip_y, t.accent, 10)
        + text(
            "rebuilt every 6h from the github api · every widget below is generated, not embedded",
            W - 26,
            strip_y,
            t.dim,
            10,
            anchor="end",
        )
        + "</g>"
    )
    return "".join(parts)


if __name__ == "__main__":
    write_svg("header", build, W, H)
    log("header built")
