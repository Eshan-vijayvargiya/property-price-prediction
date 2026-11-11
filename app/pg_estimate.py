"""Price estimator: one flat in, a price with an honest range out (design E: terminal + floor plan)."""
import numpy as np
import pandas as pd
import streamlit as st

import art
import core
import style
from features import ZONES

TYPES = ["Studio", "1 BHK", "2 BHK", "3 BHK", "4 BHK", "5 BHK"]
NEW = "New project / not listed"


def bhk_of(t):
    return (1, 1) if t == "Studio" else (int(t[0]), 0)


def pick(label, options, default, key):
    v = st.segmented_control(label, options, default=default, key=key)
    return v if v is not None else default


def inputs(d):
    loc_t = core.locality_table()
    zone = st.selectbox("Zone", ZONES, index=ZONES.index("Central Suburbs"), key="est_zone")
    locs = loc_t[loc_t.Zone == zone].sort_values("listings", ascending=False)
    locs = locs[locs.listings >= 3]
    default_loc = "Powai" if "Powai" in locs.index else locs.index[0]
    loc = st.selectbox("Locality", locs.index, index=list(locs.index).index(default_loc), key=f"est_loc_{zone}",
                       format_func=lambda x: f"{x}  ({int(locs.loc[x, 'listings']):,})")
    projs = d[d.Locality == loc].Project.value_counts()
    projs = projs[projs >= 2]
    proj = st.selectbox("Project (optional)", [NEW] + list(projs.index), key=f"est_proj_{loc}",
                        format_func=lambda x: x if x == NEW else f"{x}  ({projs[x]})",
                        help="Pick a project already on the market, or leave it as a new project. "
                             "A listed project usually gives a tighter estimate.")
    t = pick("Flat type", TYPES, "2 BHK", "est_type")
    bhk, studio = bhk_of(t)
    same = d[(d.Locality == loc) & (d.BHK == bhk) & (d.Studio == studio)]
    typical = int(round(same.Area.median() / 5) * 5) if len(same) >= 3 else {1: 600, 2: 950, 3: 1380, 4: 2200, 5: 3000}[bhk]
    if studio and len(same) < 3:
        typical = 390
    area = st.number_input("Area (sq ft)", 200, 6000, typical, step=25, key=f"est_area_{loc}_{t}",
                           help=f"Typical {t} here: {typical:,} sq ft. Listings mix carpet and built-up area.")
    status = pick("Status", core.STATUS, "Ready to move", "est_status")
    age = pick("New or resale", core.AGES, "New", "est_age")
    return dict(zone=zone, locality=loc, project="" if proj == NEW else proj, bhk=bhk, studio=studio, area=area,
                status=status, age=age, type=t)


def banner(f):
    """The locality, its numbers and its own skyline drawing."""
    t = core.locality_table()
    r = t.loc[f["locality"]]
    level = float(np.clip((np.log(r.median_ppsf) - np.log(4000)) / (np.log(40000) - np.log(4000)), 0, 1))
    style.html(f"""<div class="banner"><div class="txt"><div><div class="k">LOCALITY</div>
    <div class="name">{f['locality']}</div><div class="sub">{r.Zone} · {int(r.listings):,} listings · {int(r.projects)} projects</div></div>
    <div class="stats"><div><div class="k">MEDIAN ₹/SQ FT</div><div>{core.group_in(r.median_ppsf)}</div></div>
    <div><div class="k">MEDIAN PRICE</div><div>{core.inr(r.median_price_lakh * 1e5)}</div></div>
    <div><div class="k">UNDER CONSTR.</div><div>{r.under_construction_pct:.0f}%</div></div>
    <div><div class="k">1 / 2 / 3+ BHK</div><div>{r.share_1bhk:.0f} / {r.share_2bhk:.0f} / {r.share_3bhk_plus:.0f}%</div></div></div></div>
    <div class="art">{art.locality(f['locality'], level)}</div></div>""")


@st.cache_data(show_spinner=False)
def error_hist(zone, model):
    """Share of cross-validated errors in 5%-wide bins, for this zone and model (real data, not a drawing)."""
    o = core.oof_sample()
    col = "known_lakh" if model == "Known project" else "new_lakh"
    s = o[o.Zone == zone]
    err = 100 * (s.actual_lakh / s[col] - 1)
    counts, edges = np.histogram(err.clip(-49.9, 59.9), bins=np.arange(-50, 65, 5))
    return counts / counts.max(), edges


def estimate(f, r, loc_ppsf):
    ppsf = r.price / f["area"]
    diff = 100 * (ppsf / loc_ppsf - 1)
    seg = core.segment_of(f["area"], ppsf)
    lo_pct, hi_pct = 100 * (r.low / r.price - 1), 100 * (r.high / r.price - 1)
    h, edges = error_hist(f["zone"], r.model)
    bars = "".join(
        f'<div style="height:{max(4, 100 * v):.0f}%;background:{style.ACCENT if lo_pct <= (a + b) / 2 <= hi_pct else "#3a4552"}"></div>'
        for v, a, b in zip(h, edges[:-1], edges[1:]))
    model = "Known project: uses this project's other listings" if r.model == "Known project" else \
        "New project: location, size and status only"
    style.html(f"""<div class="est"><div class="l">03 · ESTIMATED ASKING PRICE</div>
    <div class="big">{core.inr(r.price).replace(' Cr', '<span> Cr</span>').replace(' L', '<span> L</span>')}</div>
    <div class="rng">80% RANGE <b>{core.inr(r.low)} — {core.inr(r.high)}</b></div>
    <div class="hist" style="grid-template-columns:repeat({len(h)},minmax(0,1fr))">{bars}</div>
    <div class="hist-x"><span>−50%</span><span>PAST ERRORS</span><span>+60%</span></div>
    <div class="tiles" style="margin-top:1rem;grid-template-columns:repeat(3,minmax(0,1fr))"><div class="tile"><div class="l">₹ / sq ft</div><div class="v">{core.group_in(ppsf)}</div></div>
    <div class="tile"><div class="l">vs {f['locality'][:14]}</div><div class="v" style="color:{style.UP if diff >= 0 else style.DOWN}">{diff:+.1f}%</div></div>
    <div class="tile"><div class="l">Segment</div><div class="v" style="font-family:'IBM Plex Sans',Arial,sans-serif;font-size:14px;white-space:normal">{seg}</div></div></div>
    <div class="note">{model}. Bars: how far this model's past estimates in {f['zone']} were from the real asking price;
    amber bars fall inside the 80% range.</div></div>""")


def what_if(f, r):
    d = core.listings()
    other_status = core.STATUS[1 - core.STATUS.index(f["status"])]
    other_age = "Resale" if f["age"] != "Resale" else "New"
    up = min(f["bhk"] + 1, 5)
    sel = (d.Locality == f["locality"]) & (d.BHK == up)
    up_area = int(d[sel].Area.median()) if sel.sum() >= 3 else int(f["area"] * 1.45)
    cases = [("area +10%", dict(f, area=int(f["area"] * 1.1))),
             ("under constr." if other_status == "Under construction" else "ready to move", dict(f, status=other_status)),
             (other_age.lower(), dict(f, age=other_age)),
             (f"{up}bhk @{up_area:,}", dict(f, bhk=up, studio=0, area=up_area))]
    rows = pd.DataFrame([{"Zone": c["zone"], "Locality": c["locality"], "Project": c["project"], "BHK": c["bhk"],
                          "Area": c["area"], "Studio": c["studio"], "Status": c["status"], "Age": c["age"]} for _, c in cases])
    p = core.predict(rows)
    body = "".join(f'<tr><td>{name}</td><td class="r">{core.inr(v)}</td>'
                   f'<td class="r {"up" if v >= r.price else "down"}">{100 * (v / r.price - 1):+.1f}%</td></tr>'
                   for (name, _), v in zip(cases, p.price))
    style.html(f'<table class="mtab"><tr><th>CHANGE</th><th class="r">PRICE</th><th class="r">Δ</th></tr>{body}</table>')
    st.caption("One input changed at a time. The model lets effects differ by locality, so these can differ "
               "from the Mumbai-wide averages on Price drivers.")


def across(f):
    loc_t = core.locality_table()
    big = loc_t.sort_values("listings", ascending=False).head(9).index.tolist()
    names = list(dict.fromkeys([f["locality"]] + big))[:10]
    rows = pd.DataFrame([{"Zone": loc_t.loc[n, "Zone"], "Locality": n, "Project": "", "BHK": f["bhk"], "Area": f["area"],
                          "Studio": f["studio"], "Status": f["status"], "Age": f["age"]} for n in names])
    rows["price"] = core.predict(rows).price.values
    rows = rows.sort_values("price", ascending=False)
    top = rows.price.max()
    body = "".join(f'<div class="row{" me" if n == f["locality"] else ""}"><div>{n}</div><div class="track">'
                   f'<div class="fill" style="width:{100 * v / top:.1f}%"></div></div><div class="v">{core.inr(v)}</div></div>'
                   for n, v in zip(rows.Locality, rows.price))
    style.html(f'<div class="hbars">{body}</div>')


def similar(f):
    d = core.listings()
    s = d[(d.Locality == f["locality"]) & (d.BHK == f["bhk"])]
    if f["project"]:
        sp = s[s.Project == f["project"]]
        s = sp if len(sp) >= 3 else s
    if s.empty:
        st.info("No listings of this size here.")
        return
    s = s.assign(gap=(np.log(s.Area) - np.log(f["area"])).abs()).sort_values("gap").head(7)
    body = "".join(f'<tr><td>{p[:26]}<div class="dim" style="font-size:11px">{"under constr." if st_ == "Under construction" else "ready"}'
                   f' · {ag.lower()}</div></td><td class="r">{a:,}</td><td class="r">{core.inr(v)}</td>'
                   f'<td class="r">{core.group_in(q)}</td></tr>'
                   for p, a, v, q, st_, ag in zip(s.Project, s.Area, s.Price, s.ppsf, s.Status, s.Age))
    style.html(f'<div style="overflow-x:auto"><table class="mtab"><tr><th>PROJECT</th><th class="r">SQ FT</th><th class="r">PRICE</th>'
               f'<th class="r">₹/SQFT</th></tr>{body}</table></div>')


def render():
    d = core.listings()
    top = st.container()  # the locality banner goes first on the page, but needs the inputs below
    left, mid, right = st.columns([1, 1.05, 1.3], gap="small")
    with left, style.card("inputs"):
        style.sec("INPUTS", num=1)
        f = inputs(d)
    r = core.one(f["zone"], f["locality"], f["project"], f["bhk"], f["area"], f["status"], f["age"], f["studio"])
    loc_ppsf = core.locality_table().loc[f["locality"], "median_ppsf"]
    with mid, style.card("plan"):
        style.sec("THE FLAT", num=2)
        style.html(art.floor_plan(f["bhk"], f["studio"], f["area"]))
    with right, style.card("estimate"):
        estimate(f, r, loc_ppsf)
    with top:
        banner(f)
    c1, c2, c3 = st.columns([1.1, 1.2, 1.45], gap="small")
    with c1, style.card("whatif"):
        style.sec("SENSITIVITY", num=4)
        what_if(f, r)
    with c2, style.card("across"):
        style.sec(f"SAME FLAT · {f['type']} · {f['area']:,} SQ FT", num=5, sub="new-project model, like for like")
        across(f)
    with c3, style.card("similar"):
        style.sec(f"COMPARABLES · {f['locality'].upper()} {f['type'].replace(' ', '')}", num=6, sub="closest in size")
        similar(f)
