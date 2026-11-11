"""Price estimator: one flat in, a price with an honest range out."""
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import core
import style
import ui
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
                       format_func=lambda x: f"{x}  ·  {int(locs.loc[x, 'listings']):,} listings")
    projs = d[d.Locality == loc].Project.value_counts()
    projs = projs[projs >= 2]
    proj = st.selectbox("Project (optional)", [NEW] + list(projs.index), key=f"est_proj_{loc}",
                        format_func=lambda x: x if x == NEW else f"{x}  ·  {projs[x]} listings",
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


def price_card(f, r, loc_ppsf):
    span = r.high - r.low
    pos = 100 * (r.price - r.low) / span
    ppsf = r.price / f["area"]
    diff = 100 * (ppsf / loc_ppsf - 1)
    seg = core.segment_of(f["area"], ppsf)
    model = ("Known project model (uses this project's other listings)" if r.model == "Known project"
             else "New project model (location, size and status only)")
    style.html(f"""<div class="price-card"><div class="l">Estimated asking price · {f['type']} · {f['area']:,} sq ft</div>
    <div class="price-big">{core.inr(r.price)}</div>
    <div class="r">Likely range <b>{core.inr(r.low)} – {core.inr(r.high)}</b> <span style="color:#aeb5e0">(8 in 10 similar flats)</span></div>
    <div class="range"><span style="left:0;right:0"></span><i style="left:calc({pos:.0f}% - 2px)"></i></div>
    <div class="meta">{core.psf(ppsf)} · locality median {core.psf(loc_ppsf)} ({diff:+.0f}%)</div>
    <div style="margin-top:.6rem"><span class="chip">{seg}</span><span class="chip blue">{r.model}</span></div>
    <div class="meta" style="margin-top:.2rem">{model}</div></div>""")


def across(f):
    loc_t = core.locality_table()
    big = loc_t.sort_values("listings", ascending=False).head(14).index.tolist()
    names = list(dict.fromkeys([f["locality"]] + big))[:15]
    rows = pd.DataFrame([{"Zone": loc_t.loc[n, "Zone"], "Locality": n, "Project": "", "BHK": f["bhk"], "Area": f["area"],
                          "Studio": f["studio"], "Status": f["status"], "Age": f["age"]} for n in names])
    p = core.predict(rows)
    rows["lakh"] = p.price.values / 1e5
    rows["low"], rows["high"] = p.low.values / 1e5, p.high.values / 1e5
    rows["label"] = [core.inr(v * 1e5) for v in rows.lakh]
    rows["this"] = np.where(rows.Locality == f["locality"], "Your choice", "Other")
    order = rows.sort_values("lakh", ascending=False).Locality.tolist()
    base = alt.Chart(rows).encode(y=alt.Y("Locality:N", sort=order, title=None, axis=alt.Axis(labelLimit=150, labelOverlap=False)))
    bars = base.mark_bar(cornerRadiusEnd=4, height=14).encode(
        x=alt.X("lakh:Q", axis=ui.lakh_axis("Estimated price")),
        color=alt.Color("this:N", scale=alt.Scale(domain=["Your choice", "Other"], range=["#9b7dff", style.BLUE]),
                        legend=None),
        tooltip=[alt.Tooltip("Locality:N"), alt.Tooltip("Zone:N"), alt.Tooltip("label:N", title="Estimate"),
                 alt.Tooltip("low:Q", title="Low (lakh)", format=",.0f"), alt.Tooltip("high:Q", title="High (lakh)", format=",.0f")])
    text = base.mark_text(align="left", dx=4, color=style.INK, fontSize=11).encode(x="lakh:Q", text="label:N")
    ui.chart(bars + text, 380)


def what_if(f, r):
    d = core.listings()
    bigger = dict(f, area=int(f["area"] * 1.1))
    other_status = core.STATUS[1 - core.STATUS.index(f["status"])]
    other_age = "Resale" if f["age"] != "Resale" else "New"
    up = min(f["bhk"] + 1, 5)
    up_area = int(d[(d.Locality == f["locality"]) & (d.BHK == up)].Area.median()) if (
        (d.Locality == f["locality"]) & (d.BHK == up)).sum() >= 3 else int(f["area"] * 1.45)
    cases = [("10% more area", bigger), (other_status, dict(f, status=other_status)),
             (other_age, dict(f, age=other_age)),
             (f"{up} BHK at a typical {up_area:,} sq ft", dict(f, bhk=up, studio=0, area=up_area))]
    rows = pd.DataFrame([{"Zone": c["zone"], "Locality": c["locality"], "Project": c["project"], "BHK": c["bhk"],
                          "Area": c["area"], "Studio": c["studio"], "Status": c["status"], "Age": c["age"]} for _, c in cases])
    p = core.predict(rows)
    body = "".join(f"<tr><td>{name}</td><td>{core.inr(v)}</td><td style='color:{'#34d399' if v >= r.price else '#f87171'}'>"
                   f"{100 * (v / r.price - 1):+.1f}%</td></tr>" for (name, _), v in zip(cases, p.price))
    style.html(f'<table class="mtab"><tr><th>If instead…</th><th>Estimate</th><th>Change</th></tr>{body}</table>')
    st.caption("Same model, one thing changed at a time. The model lets effects differ by place, so these can "
               "differ from the Mumbai-wide averages on Price drivers.")


def similar(f):
    d = core.listings()
    s = d[(d.Locality == f["locality"]) & (d.BHK == f["bhk"])]
    if f["project"]:
        sp = s[s.Project == f["project"]]
        s = sp if len(sp) >= 3 else s
    if s.empty:
        st.info("No listings of this size here.")
        return
    s = s.assign(gap=(np.log(s.Area) - np.log(f["area"])).abs()).sort_values("gap").head(8)
    show = pd.DataFrame({"Project": s.Project, "Sq ft": s.Area,
                         "Price": [core.inr(v) for v in s.Price], "₹/sq ft": [core.group_in(v) for v in s.ppsf],
                         "Status": s.Status.str.replace("Under construction", "Under constr."), "Age": s.Age})
    st.dataframe(show, hide_index=True, width="stretch")


def render():
    d = core.listings()
    style.html('<div class="card-t" style="font-size:1.6rem">Price estimator</div>'
               '<div class="card-p" style="margin-bottom:.8rem">Describe a flat. The model returns an asking price, '
               'a range that holds for 8 in 10 similar flats, and how it compares across Mumbai.</div>')
    left, right = st.columns([1, 1.35], gap="medium")
    with left, style.card("inputs"):
        style.sec("The flat", "🏠")
        f = inputs(d)
    r = core.one(f["zone"], f["locality"], f["project"], f["bhk"], f["area"], f["status"], f["age"], f["studio"])
    loc_ppsf = core.locality_table().loc[f["locality"], "median_ppsf"]
    with right:
        price_card(f, r, loc_ppsf)
        with style.card("whatif"):
            style.sec("What if…", "🔁")
            what_if(f, r)
    c1, c2 = st.columns([1, 1.15], gap="medium")
    with c1, style.card("across"):
        style.sec("The same flat across Mumbai", "🗺️", "new-project model, like for like")
        across(f)
    with c2, style.card("similar"):
        style.sec("Similar listings", "📋", f"{f['type']} in {f['locality']}, closest in size")
        similar(f)
