"""Price drivers: % effects from the linear model, and what the boosting model relies on."""
import altair as alt
import pandas as pd
import streamlit as st

import core
import style
import ui


def forest(df, height):
    """Dot + 95% interval per row, with a zero line."""
    df = df.copy()
    df["label"] = df.effect_pct.map(lambda v: f"{v:+.1f}%")
    y = alt.Y("name:N", sort=None, title=None, axis=alt.Axis(labelLimit=260))
    rule = alt.Chart(df).mark_rule(color=style.BLUE, strokeWidth=2.5).encode(y=y, x=alt.X("low_pct:Q", title="Effect on price (%)"), x2="high_pct:Q")
    dot = alt.Chart(df).mark_circle(color=style.BLUE, size=110, stroke="#060a1c", strokeWidth=2, opacity=1).encode(
        y=y, x="effect_pct:Q", tooltip=[alt.Tooltip("name:N", title=" "), alt.Tooltip("effect_pct:Q", title="Effect %", format="+.1f"),
                                        alt.Tooltip("low_pct:Q", title="95% low", format="+.1f"),
                                        alt.Tooltip("high_pct:Q", title="95% high", format="+.1f")])
    text = alt.Chart(df).mark_text(align="left", dx=7, color=style.INK, fontSize=11).encode(y=y, x="high_pct:Q", text="label:N")
    zero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=style.SOFT, strokeDash=[4, 4]).encode(x="x:Q")
    ui.chart(zero + rule + dot + text, height)


def render():
    dr = core.js("drivers")
    imp = core.js("importance")
    style.html('<div class="card-t" style="font-size:1.6rem">Price drivers</div>'
               '<div class="card-p" style="margin-bottom:.8rem">What moves the asking price, comparing flats <b>in the same locality</b>. '
               f'From a linear model on log price, fitted on {dr["n"]:,} listings with a separate effect for each locality '
               f'(R² {dr["r2_log"]:.2f}). The bars are 95% intervals; flats in one project aren\'t independent, so the intervals '
               'are clustered by project.</div>')
    c1, c2 = st.columns([1.25, 1], gap="medium")
    with c1, style.card("dr-main"):
        style.sec("Effects on price, same locality", "📈")
        e = pd.DataFrame([{"name": k, **v} for k, v in dr["effects"].items()])
        forest(e, 330)
    with c2:
        uc = dr["effects"]["Under construction (vs ready to move)"]
        rs = dr["effects"]["Resale (vs new)"]
        b3 = dr["effects"]["3 BHK (vs 2 BHK, same area)"]
        a10 = dr["effects"]["10% more area (same BHK, locality)"]
        style.glass("Bedrooms say more about size than the area figure",
                    f'<div class="card-p">10% more area adds only <b>{a10["effect_pct"]:+.1f}%</b>, but a 3 BHK lists '
                    f'<b>{b3["effect_pct"]:+.0f}%</b> above a 2 BHK of the same stated area. Why? Listings mix <b>carpet</b> area '
                    '(what you walk on, required for new projects since RERA) and <b>built-up / super built-up</b> area '
                    '(often 20–40% bigger). The bedroom count isn\'t affected by that, so it carries real size information.</div>',
                    insight=True)
        style.glass("No discount for waiting",
                    f'<div class="card-p">Under-construction flats list at <b>{uc["effect_pct"]:+.1f}%</b> versus ready ones '
                    f'(95%: {uc["low_pct"]:+.1f}% to {uc["high_pct"]:+.1f}%). Newer projects come with newer buildings and '
                    f'amenities, which offsets the wait. Resale flats list <b>{rs["effect_pct"]:+.1f}%</b> below new ones.</div>',
                    insight=True)

    c3, c4 = st.columns(2, gap="medium")
    with c3, style.card("dr-zone"):
        style.sec("The under-construction effect by zone", "🏗️", "one regression per zone")
        z = pd.DataFrame([{"name": k, **v} for k, v in dr["under_construction_by_zone"].items()]).sort_values("effect_pct")
        forest(z, 300)
        st.caption("Only Kalyan-Dombivli is clearly above zero (+6%), where new townships with amenities compete with "
                   "older, basic buildings. Thane and Navi Mumbai lean the same way (+4%) but their intervals touch zero.")
    with c4, style.card("dr-imp"):
        style.sec("What the price model relies on", "🧠", "grouped permutation importance")
        rows = [{"test": t, "group": g, "pts": v} for t, r in imp.items() for g, v in r["increase_pct_points"].items()]
        df = pd.DataFrame(rows)
        order = list(imp["New project"]["increase_pct_points"].keys())
        style.legend([("Known project", style.BLUE), ("New project", style.ORANGE)])
        c = alt.Chart(df).mark_bar(cornerRadiusEnd=3, height=alt.RelativeBandSize(0.8)).encode(
            y=alt.Y("group:N", sort=order, title=None, axis=alt.Axis(labelLimit=200)),
            yOffset=alt.YOffset("test:N", sort=["Known project", "New project"]),
            x=alt.X("pts:Q", title="Error increase when shuffled (% points)"),
            color=alt.Color("test:N", scale=alt.Scale(domain=["Known project", "New project"], range=[style.BLUE, style.ORANGE]),
                            legend=None),
            tooltip=[alt.Tooltip("test:N", title="Test"), alt.Tooltip("group:N", title="Feature group"),
                     alt.Tooltip("pts:Q", title="+ % points", format=".1f")])
        ui.chart(c, 300)
        st.caption("Shuffle one group of features and see how much worse the model gets. For a known project, "
                   "the project's own prices matter most (they carry location too). For a new launch, it's location and size.")
    st.caption("These are associations in asking prices, not causes: the data has no floor, view, amenities or builder, "
               "and any of those can move with the features above.")
