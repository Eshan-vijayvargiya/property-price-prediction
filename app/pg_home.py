"""Home: what the app does, the headline numbers and the four findings."""
import altair as alt
import streamlit as st

import core
import style
import ui
from features import ZONES


def render(go):
    d = core.listings()
    ev = core.js("eval")
    dr = core.js("drivers")
    style.hero("What should a flat in Mumbai cost?",
               "A price model, a launch-pricing tool and buyer segments for the Mumbai Metropolitan Region, "
               "built from 54,598 cleaned property listings and tested the way a developer would use it.")
    known = ev["Known project"]["Gradient boosting"]
    new = ev["New project"]["Gradient boosting"]
    style.tiles([
        ("Listings analysed", f"{len(d):,}", "after removing 20,312 duplicates"),
        ("Localities · projects", f"{d.Locality.nunique()} · {d.Project.nunique():,}", "in 7 zones, Colaba to Karjat"),
        ("Typical error, known project", f"±{known['median_error_pct']:.0f}%", f"{known['within_20_pct']:.0f}% of flats within ±20%"),
        ("Typical error, new launch", f"±{new['median_error_pct']:.0f}%", f"{new['within_20_pct']:.0f}% within ±20%, project never seen"),
    ])

    c1, c2 = st.columns([1.25, 1], gap="medium")
    with c1, style.card("zones"):
        style.sec("Price per sq ft by zone", "🏙️", "median asking price")
        z = d.groupby("Zone").agg(ppsf=("ppsf", "median"), listings=("Price", "size"),
                                  price=("price_lakh", "median")).reindex(ZONES).reset_index()
        z["label"] = z.ppsf.map(lambda v: f"₹{v / 1000:.1f}k")
        order = z.sort_values("ppsf", ascending=False).Zone.tolist()
        base = alt.Chart(z).encode(y=alt.Y("Zone:N", sort=order, title=None, axis=alt.Axis(labelLimit=190)))
        bars = base.mark_bar(cornerRadiusEnd=4, height=20).encode(
            x=alt.X("ppsf:Q", title="₹ per sq ft"), color=ui.zone_color(),
            tooltip=[alt.Tooltip("Zone:N"), alt.Tooltip("ppsf:Q", title="₹ per sq ft", format=",.0f"),
                     alt.Tooltip("price:Q", title="Median price (lakh)", format=",.0f"),
                     alt.Tooltip("listings:Q", title="Listings", format=",")])
        text = base.mark_text(align="left", dx=5, color=style.INK, fontSize=11.5).encode(x="ppsf:Q", text="label:N")
        ui.chart(bars + text, 300)
        hi, lo = z.ppsf.max(), z.ppsf.min()
        st.caption(f"The most expensive zone costs {hi / lo:.1f}× the cheapest per sq ft. Location is the biggest "
                   "single driver of price.")
    with c2:
        with style.card("go"):
            style.sec("Try it", "⚡")
            for page, icon, text in [
                ("Price estimator", ":material/calculate:", "Price one flat, with a range and similar listings"),
                ("Launch planner", ":material/apartment:", "Price a new project's unit mix against competitors"),
                ("Buyer segments", ":material/groups:", "Five kinds of home, and who buys them"),
                ("Price drivers", ":material/trending_up:", "What really moves the price"),
            ]:
                if st.button(f"**{page}**  ·  {text}", icon=icon, key=f"home_{page}", width="stretch"):
                    go(page)
                    st.rerun()

    uc = dr["effects"]["Under construction (vs ready to move)"]
    resale = dr["effects"]["Resale (vs new)"]
    seg = d.groupby("Segment").agg(area=("Area", "median"), lakh=("price_lakh", "median"))
    style.sec("Four findings", "💡")
    cols = st.columns(4, gap="small")
    finds = [
        ("Location vs space", f"About ₹{seg.loc['Compact city homes', 'lakh']:.0f}-{seg.loc['Spacious value homes', 'lakh']:.0f} lakh buys "
         f"<b>{seg.loc['Compact city homes', 'area']:,.0f} sq ft</b> in the suburbs or <b>{seg.loc['Spacious value homes', 'area']:,.0f} sq ft</b> "
         "further out. That's the main choice buyers make."),
        ("Bedrooms beat the area figure", "At the same stated area, a 3 BHK lists about <b>33% higher</b> than a 2 BHK. "
         "Listings mix carpet and built-up area, so the bedroom count is the cleaner size signal."),
        ("No discount for waiting", f"Under-construction flats list at <b>{uc['effect_pct']:+.1f}%</b> versus ready ones "
         f"in the same locality; resale flats at <b>{resale['effect_pct']:+.1f}%</b> versus new."),
        ("New launches are harder", f"Knowing the project halves the error vs a simple rule ({ev['Known project'][list(ev['Known project'])[0]]['median_error_pct']:.0f}% → "
         f"{known['median_error_pct']:.0f}%). For a project the model has never seen it's <b>{new['median_error_pct']:.0f}%</b>."),
    ]
    for col, (t, b) in zip(cols, finds):
        with col:
            style.html(f'<div class="glass" style="height:100%"><div class="card-t">{t}</div><div class="card-p">{b}</div></div>')
