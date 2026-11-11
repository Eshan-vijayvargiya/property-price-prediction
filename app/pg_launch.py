"""Launch planner: price a new project's unit mix and see where it sits against nearby projects."""
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import core
import style
import ui
from features import ZONES

TYPES = ["Studio", "1 BHK", "2 BHK", "3 BHK", "4 BHK", "5 BHK"]


def typical_area(d, loc, t):
    bhk, studio = (1, 1) if t == "Studio" else (int(t[0]), 0)
    s = d[(d.Locality == loc) & (d.BHK == bhk) & (d.Studio == studio)].Area
    if len(s) >= 3:
        return int(round(s.median() / 5) * 5)
    return {"Studio": 390, "1 BHK": 610, "2 BHK": 950, "3 BHK": 1380, "4 BHK": 2200, "5 BHK": 3000}[t]


def render():
    d = core.listings()
    loc_t = core.locality_table()
    style.html('<div class="card-t" style="font-size:1.6rem">Launch planner</div>'
               '<div class="card-p" style="margin-bottom:.8rem">For a developer: price a <b>new project</b> unit by unit, '
               'then check it against the projects already selling in that locality. Uses the model that was tested '
               'on projects it had never seen.</div>')
    left, right = st.columns([1, 1.4], gap="medium")
    with left, style.card("launch-in"):
        style.sec("The project", "🏗️")
        zone = st.selectbox("Zone", ZONES, index=ZONES.index("Thane"), key="ln_zone")
        locs = loc_t[(loc_t.Zone == zone) & (loc_t.listings >= 20)].sort_values("listings", ascending=False)
        loc = st.selectbox("Locality", locs.index, key=f"ln_loc_{zone}",
                           format_func=lambda x: f"{x}  ·  {int(locs.loc[x, 'projects'])} projects")
        status = st.segmented_control("Status at launch", core.STATUS, default="Under construction", key="ln_status") \
            or "Under construction"
        st.caption("A new project, so every flat is priced as **New**.")
        st.markdown("**Unit mix** · edit sizes and counts")
        mix = pd.DataFrame({"Type": ["1 BHK", "2 BHK", "3 BHK"],
                            "Area (sq ft)": [typical_area(d, loc, t) for t in ["1 BHK", "2 BHK", "3 BHK"]],
                            "Units": [60, 100, 40]})
        mix = st.data_editor(mix, key=f"ln_mix_{loc}", num_rows="dynamic", hide_index=True, width="stretch",
                             column_config={
                                 "Type": st.column_config.SelectboxColumn(options=TYPES, required=True),
                                 "Area (sq ft)": st.column_config.NumberColumn(min_value=200, max_value=6000, step=10, required=True),
                                 "Units": st.column_config.NumberColumn(min_value=1, max_value=2000, step=1, required=True)})
    mix = mix.dropna()
    mix = mix[(mix["Area (sq ft)"] >= 200) & (mix["Units"] >= 1)]
    if mix.empty:
        right.info("Add at least one unit type.")
        return
    rows = pd.DataFrame({"Zone": zone, "Locality": loc, "Project": "",
                         "BHK": [1 if t == "Studio" else int(t[0]) for t in mix.Type],
                         "Studio": [int(t == "Studio") for t in mix.Type], "Area": mix["Area (sq ft)"].astype(int).values,
                         "Status": status, "Age": "New"})
    p = core.predict(rows)
    units = mix.Units.astype(int).values
    total, lo, hi = (p.price.values * units).sum(), (p.low.values * units).sum(), (p.high.values * units).sum()
    area_total = (rows.Area.values * units).sum()
    ppsf = total / area_total
    comp = d[d.Locality == loc].groupby("Project").agg(listings=("Price", "size"), ppsf=("ppsf", "median"),
                                                       uc=("Status", lambda s: 100 * (s == "Under construction").mean()),
                                                       bhk=("BHK", lambda s: s.mode()[0]), area=("Area", "median"))
    comp = comp[comp.listings >= 3].sort_values("listings", ascending=False)
    rank = 100 * (comp.ppsf < ppsf).mean() if len(comp) else np.nan

    with right:
        style.tiles([
            ("Estimated sales value", core.inr(total), f"range {core.inr(lo)} – {core.inr(hi)}"),
            ("Average ₹ per sq ft", f"₹{core.group_in(ppsf)}", f"{units.sum():,} units · {core.group_in(area_total)} sq ft"),
            ("Pricier than", f"{rank:.0f}%" if not np.isnan(rank) else "–",
             f"of {len(comp)} nearby projects (3+ listings)" if len(comp) else "no projects with 3+ listings"),
        ])
        with style.card("launch-units"):
            style.sec("Price per unit type", "🏷️", "8 in 10 similar flats fall in the range")
            t = pd.DataFrame({"Type": [f"{a} · {b:,} sq ft" for a, b in zip(mix.Type.values, rows.Area.values)],
                              "Price per unit": [core.inr(v) for v in p.price],
                              "Range": [f"{core.inr(a)} – {core.inr(b)}" for a, b in zip(p.low, p.high)],
                              "₹/sq ft": [core.group_in(v) for v in p.price.values / rows.Area.values],
                              "Sales value": [core.inr(v) for v in p.price.values * units]})
            st.dataframe(t, hide_index=True, width="stretch")
            st.caption("The total range adds up the unit ranges: errors within one project move together "
                       "(same builder, amenities and finish), so they don't cancel out.")

    with style.card("launch-comp"):
        style.sec(f"Where this launch sits in {loc}", "📊", "median asking ₹/sq ft of projects with 3+ listings")
        if comp.empty:
            st.info("Not enough projects here to compare.")
            return
        top = comp.head(18).reset_index()
        top = pd.concat([top, pd.DataFrame([{"Project": "▶ Your launch", "listings": units.sum(), "ppsf": ppsf,
                                             "uc": 100.0 if status == "Under construction" else 0.0, "bhk": 0, "area": 0}])])
        top["who"] = np.where(top.Project == "▶ Your launch", "Your launch", "Existing project")
        top["label"] = top.ppsf.map(lambda v: f"₹{v / 1000:.1f}k")
        order = top.sort_values("ppsf", ascending=False).Project.tolist()
        base = alt.Chart(top).encode(y=alt.Y("Project:N", sort=order, title=None,
                                             axis=alt.Axis(labelLimit=260, labelOverlap=False)))
        bars = base.mark_bar(cornerRadiusEnd=4, height=13).encode(
            x=alt.X("ppsf:Q", title="₹ per sq ft (median asking)"),
            color=alt.Color("who:N", scale=alt.Scale(domain=["Your launch", "Existing project"], range=[style.ACCENT, style.SLATE]),
                            legend=None),
            tooltip=[alt.Tooltip("Project:N"), alt.Tooltip("ppsf:Q", title="₹/sq ft", format=",.0f"),
                     alt.Tooltip("listings:Q", title="Listings"), alt.Tooltip("uc:Q", title="% under construction", format=".0f")])
        text = base.mark_text(align="left", dx=4, color=style.INK, fontSize=10.5).encode(x="ppsf:Q", text="label:N")
        med = alt.Chart(pd.DataFrame({"x": [loc_t.loc[loc, "median_ppsf"]]})).mark_rule(
            color=style.SOFT, strokeDash=[4, 4]).encode(x="x:Q")
        ui.chart(bars + text + med, max(260, 26 * len(top)))
        st.caption(f"Dashed line: {loc} median {core.psf(loc_t.loc[loc, 'median_ppsf'])}. "
                   "Projects differ by builder, amenities and exact site, which this data doesn't record; "
                   "that's most of the gap between a project and the model.")
