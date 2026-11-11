"""Line drawings used across the app: the city skyline, a locality skyline and a floor plan.

All drawn here as SVG/HTML strings in one style: light grey outlines, amber lights, dark background.
No photos, so nothing to license or download.
"""
import hashlib

AMBER, LINE, DIM, PANEL, BG = "#f5a524", "#c9d1d9", "#2a323d", "#12161c", "#0b0d10"

PATTERNS = f"""<defs>
<pattern id="{{p}}a" width="14" height="18" patternUnits="userSpaceOnUse"><rect x="3" y="4" width="4" height="6" fill="{AMBER}"/><rect x="9" y="4" width="3" height="6" fill="{DIM}"/><rect x="3" y="12" width="4" height="5" fill="{DIM}"/><rect x="9" y="12" width="3" height="5" fill="{DIM}"/></pattern>
<pattern id="{{p}}b" width="12" height="16" patternUnits="userSpaceOnUse"><rect x="2" y="3" width="3" height="5" fill="{DIM}"/><rect x="7" y="3" width="3" height="5" fill="{DIM}"/><rect x="2" y="10" width="3" height="5" fill="{DIM}"/><rect x="7" y="10" width="3" height="5" fill="{AMBER}"/></pattern>
<pattern id="{{p}}c" width="16" height="14" patternUnits="userSpaceOnUse"><rect x="3" y="3" width="10" height="3" fill="{DIM}"/><rect x="3" y="9" width="10" height="3" fill="{AMBER}" opacity="0.8"/></pattern>
</defs>"""


def _towers(p, towers):
    """towers: (x, top, width, base, pattern, roof) tuples -> outline + window fill."""
    out = []
    for x, top, w, base, pat, roof in towers:
        out.append(f'<rect x="{x}" y="{top}" width="{w}" height="{base - top}" fill="{PANEL}" stroke="{LINE}" stroke-width="1.5"/>')
        out.append(f'<rect x="{x + 5}" y="{top + 6}" width="{w - 10}" height="{base - top - 10}" fill="url(#{p}{pat})"/>')
        if roof == "spire":
            out.append(f'<path d="M{x + w / 2} {top} L{x + w / 2} {top - 30}" stroke="{AMBER}" stroke-width="1.5"/>')
        elif roof == "crown":
            out.append(f'<path d="M{x} {top} L{x + w / 2} {top - 20} L{x + w} {top}" fill="none" stroke="{LINE}" stroke-width="1.5"/>')
    return "".join(out)


def city(height=360):
    """The Mumbai skyline at night with a cable-stayed sea bridge (front page and home page)."""
    p = "city"
    towers = [(30, 200, 52, 320, "b", ""), (92, 140, 46, 320, "a", ""), (148, 92, 58, 320, "c", "spire"),
              (216, 172, 42, 320, "b", ""), (268, 62, 64, 320, "a", "crown"), (342, 122, 50, 320, "b", ""),
              (402, 196, 72, 320, "c", "")]
    stars = "".join(f'<circle cx="{x}" cy="{y}" r="1.1" fill="#9aa7b4"/>' for x, y in
                    [(60, 40), (180, 22), (330, 30), (420, 60), (520, 28), (720, 50), (470, 110), (250, 70)])
    cables = "".join(f'<path d="M616 {a} L{b} 300"/>' for a, b in [(176, 500), (182, 532), (190, 566), (176, 732),
                                                                     (182, 700), (190, 666)])
    glints = "".join(f'<path d="M{a} {y} L{b} {y}"/>' for a, b, y in [(100, 118, 336), (162, 190, 346), (282, 312, 338),
                                                                      (290, 306, 356), (410, 432, 344), (560, 590, 334),
                                                                      (640, 668, 350)])
    return (f'<svg viewBox="0 0 760 400" style="width:100%;height:auto;max-height:{height}px;display:block" role="img" '
            f'aria-label="Line drawing of the Mumbai skyline at night with lit windows and a sea bridge">'
            f'{PATTERNS.format(p=p)}{stars}'
            f'<circle cx="650" cy="78" r="24" fill="none" stroke="{AMBER}" stroke-width="1.5"/>'
            f'<circle cx="661" cy="70" r="22" fill="{BG}"/>'
            f'{_towers(p, towers)}'
            f'<g fill="#151a21" stroke="#3a4552"><rect x="492" y="248" width="34" height="58"/>'
            f'<rect x="536" y="232" width="26" height="74"/><rect x="700" y="244" width="40" height="62"/></g>'
            f'<path d="M484 300 L760 300" stroke="{LINE}" stroke-width="2.5"/>'
            f'<path d="M604 300 L616 168 L628 300" fill="none" stroke="{LINE}" stroke-width="2"/>'
            f'<path d="M609 246 L623 246" stroke="{LINE}" stroke-width="2"/>'
            f'<g stroke="{AMBER}" stroke-width="1" opacity="0.8">{cables}</g>'
            f'<path d="M0 320 L760 320" stroke="#3a4552" stroke-width="1.5"/>'
            f'<g stroke="{AMBER}" stroke-width="2" opacity="0.45">{glints}</g>'
            f'<g stroke="{DIM}" stroke-width="1.5"><path d="M20 372 L120 372"/><path d="M200 384 L330 384"/>'
            f'<path d="M420 368 L520 368"/><path d="M600 388 L720 388"/></g></svg>')


def locality(name, level):
    """A small skyline drawn for one locality. Same name -> same drawing. `level` 0-1 = how pricey
    the locality is, so expensive places get taller towers."""
    seed = int(hashlib.md5(name.encode()).hexdigest(), 16)

    def rnd(i, lo, hi):
        return lo + (seed >> (i * 7) & 127) / 127 * (hi - lo)

    p = "loc" + str(seed % 10000)
    towers, x = [], 200 + rnd(0, 0, 20)
    tallest = 70 + 70 * level
    for i in range(6):
        w = rnd(i + 1, 36, 60)
        h = tallest * rnd(i + 8, 0.45, 1.0)
        roof = "spire" if i == int(rnd(20, 0, 5.99)) else ("crown" if i == int(rnd(21, 0, 5.99)) else "")
        towers.append((round(x), round(168 - h), round(w), 170, "abc"[int(rnd(i + 14, 0, 2.99))], roof))
        x += w + rnd(i + 2, 6, 14)
        if x > 520:
            break
    water = (f'<path d="M0 130 C 60 112 120 108 180 116" fill="none" stroke="#3a4552" stroke-width="1.5"/>'
             f'<path d="M10 140 C 70 130 130 128 190 134" fill="none" stroke="{DIM}" stroke-width="1.5"/>'
             f'<path d="M30 150 L80 150" stroke="{AMBER}" stroke-width="2" opacity="0.45"/>'
             f'<path d="M110 156 L150 156" stroke="{AMBER}" stroke-width="2" opacity="0.35"/>')
    tree = (f'<g stroke="#3a4552" stroke-width="1.5" fill="none"><path d="M150 170 C 160 150 172 150 182 170"/>'
            f'<path d="M168 170 L168 150"/><path d="M160 156 C 164 146 172 146 176 156"/></g>')
    return (f'<svg viewBox="0 0 560 170" preserveAspectRatio="xMidYMax slice" style="width:100%;height:170px;display:block" '
            f'role="img" aria-label="Line drawing of towers in {name}">{PATTERNS.format(p=p)}{water}{tree}'
            f'{_towers(p, towers)}</svg>')


# floor-plan room boxes: (label, left %, top %, width %, height %, is_bedroom)
PLANS = {
    "studio": [("LIVING + SLEEPING", 0, 0, 68, 100, True), ("KITCHENETTE", 68, 0, 32, 50, False), ("BATH", 68, 50, 32, 50, False)],
    1: [("LIVING", 0, 0, 56, 60, False), ("KITCHEN", 0, 60, 30, 40, False), ("BATH", 30, 60, 26, 40, False),
        ("BEDROOM", 56, 0, 44, 100, True)],
    2: [("LIVING / DINING", 0, 0, 56, 60, False), ("KITCHEN", 0, 60, 30, 40, False), ("BATH", 30, 60, 26, 40, False),
        ("BEDROOM 1", 56, 0, 44, 50, True), ("BEDROOM 2", 56, 50, 44, 50, True)],
    3: [("LIVING / DINING", 0, 0, 50, 56, False), ("KITCHEN", 0, 56, 25, 44, False), ("BATH", 25, 56, 25, 44, False),
        ("BEDROOM 1", 50, 0, 50, 34, True), ("BEDROOM 2", 50, 34, 50, 33, True), ("BEDROOM 3", 50, 67, 50, 33, True)],
    4: [("LIVING", 0, 0, 40, 55, False), ("KITCHEN", 0, 55, 20, 45, False), ("BATH", 20, 55, 20, 45, False),
        ("BED 1", 40, 0, 30, 50, True), ("BED 2", 70, 0, 30, 50, True), ("BED 3", 40, 50, 30, 50, True),
        ("BED 4", 70, 50, 30, 50, True)],
    5: [("LIVING", 0, 0, 40, 55, False), ("KITCHEN", 0, 55, 20, 45, False), ("BATH", 20, 55, 20, 45, False),
        ("BED 1", 40, 0, 20, 50, True), ("BED 2", 60, 0, 20, 50, True), ("BED 3", 80, 0, 20, 50, True),
        ("BED 4", 40, 50, 30, 50, True), ("BED 5", 70, 50, 30, 50, True)],
}


def floor_plan(bhk, studio, area):
    """An illustrative layout that redraws with the flat type, with the area as a dimension line."""
    rooms = PLANS["studio"] if studio else PLANS[min(max(int(bhk), 1), 5)]
    boxes = "".join(
        f'<div class="room{" bed" if bed else ""}" style="left:{l}%;top:{t}%;width:{w}%;height:{h}%">{label}</div>'
        for label, l, t, w, h, bed in rooms)
    beds = sum(r[5] for r in rooms)
    per = f"~{round(area / max(beds, 1) / 10) * 10:,} SQ FT PER BEDROOM" if not studio else "ONE OPEN ROOM"
    kind = "STUDIO" if studio else f"{bhk} BEDROOM{'S' if bhk > 1 else ''}"
    return (f'<div class="plan-wrap"><div class="dim"><i></i><b></b><span>{area:,} SQ FT</span><b></b><i></i></div>'
            f'<div class="plan">{boxes}</div></div>'
            f'<div class="plan-legend"><span><em>■</em> {kind}</span><span>{per}</span><span>ILLUSTRATIVE LAYOUT</span></div>')
