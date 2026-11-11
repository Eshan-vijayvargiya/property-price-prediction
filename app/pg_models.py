"""Model lab: four models under three honest tests, the price ranges and their real coverage."""
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import core
import style
import ui

TESTS = ["Known project", "New project", "New locality"]
TEST_COLORS = [style.BLUE, style.ORANGE, style.AQUA]
TEXT = {
    "Known project": "Random 5-fold split. A new listing in a project that's already on the market.",
    "New project": "Whole projects held out together. Pricing a launch the model has never seen. <b>The developer's case.</b>",
    "New locality": "Whole localities held out. Only the zone is known. A stress test of how far the model travels.",
}


def render():
    ev = core.js("eval")
    iv = core.js("intervals")
    style.html('<div class="card-t" style="font-size:1.6rem">Model lab</div>'
               '<div class="card-p" style="margin-bottom:.8rem">Four models, three tests. A random split is the usual way, but '
               'it flatters the model: flats from the same project end up on both sides. So each model is also tested on '
               'projects and localities it has never seen.</div>')
    cols = st.columns(3, gap="small")
    for col, t, c in zip(cols, TESTS, TEST_COLORS):
        with col:
            best = min((m for m in ev[t] if not m.startswith("_")), key=lambda m: ev[t][m]["median_error_pct"])
            style.html(f'<div class="seg" style="--c:{c}"><h4>{t}</h4><p>{TEXT[t]}</p>'
                       f'<p>Best: <span class="num">{best}</span>, typical error <span class="num">±{ev[t][best]["median_error_pct"]:.1f}%</span></p></div>')
    st.write("")

    rows = [{"test": t, "model": m, **ev[t][m]} for t in TESTS for m in ev[t] if not m.startswith("_")]
    df = pd.DataFrame(rows)
    models = list(dict.fromkeys(df.model))
    c1, c2 = st.columns([1.15, 1], gap="medium")
    with c1, style.card("ml-compare"):
        style.sec("Typical error by model and test", "🏁", "median % error, lower is better")
        style.legend(list(zip(TESTS, TEST_COLORS)))
        c = alt.Chart(df).mark_bar(cornerRadiusEnd=3, height=alt.RelativeBandSize(0.85)).encode(
            y=alt.Y("model:N", sort=models, title=None, axis=alt.Axis(labelLimit=230)),
            yOffset=alt.YOffset("test:N", sort=TESTS),
            x=alt.X("median_error_pct:Q", title="Median error (%)"),
            color=alt.Color("test:N", scale=alt.Scale(domain=TESTS, range=TEST_COLORS), legend=None),
            tooltip=[alt.Tooltip("model:N"), alt.Tooltip("test:N"), alt.Tooltip("median_error_pct:Q", title="Median error %"),
                     alt.Tooltip("within_10_pct:Q", title="Within ±10% (%)"), alt.Tooltip("within_20_pct:Q", title="Within ±20% (%)"),
                     alt.Tooltip("r2_log:Q", title="R² (log)")])
        ui.chart(c, 360)
    with c2, style.card("ml-table"):
        style.sec("All the numbers", "🧾")
        t = st.segmented_control("Test", TESTS, default="New project", key="ml_test") or "New project"
        s = df[df.test == t]
        best = s.median_error_pct.idxmin()
        body = "".join(f'<tr class="{"best" if i == best else ""}"><td>{r.model}</td><td>±{r.median_error_pct:.1f}%</td>'
                       f'<td>{r.within_10_pct:.0f}%</td><td>{r.within_20_pct:.0f}%</td><td>{r.r2_log:.3f}</td></tr>'
                       for i, r in s.iterrows())
        style.html(f'<table class="mtab"><tr><th>Model</th><th>Median error</th><th>Within ±10%</th><th>Within ±20%</th>'
                   f'<th>R² (log)</th></tr>{body}</table>')
        g = {t: ev[t]["Random forest"]["median_error_pct"] - ev[t]["Gradient boosting"]["median_error_pct"] for t in TESTS}
        lin_gap = ev["New locality"]["Linear regression"]["median_error_pct"] - min(
            ev["New locality"][m]["median_error_pct"] for m in ("Random forest", "Gradient boosting"))
        style.html(f"""<div class="card-p" style="margin-top:.7rem"><b>What the tests show.</b> Knowing the project matters most:
        the error nearly halves against the simple rule. For a new project, location and size take every model to about
        ±12-14%; the rest is builder, floor and view, which the data doesn't have. For a new locality everything struggles,
        and the plain linear model is within {lin_gap:.1f} points of the best tree.<br>
        <b>Deployed: gradient boosting</b>, with one rule built in: price can only rise with area, so a bigger flat is never
        estimated cheaper (that cost about 0.2 points). The random forest was {-g['Known project']:.1f} points better on known
        projects and {-g['New project']:.1f} on new ones, but its file is 98 MB against under 2 MB, too big for a free web app.</div>""")

    c3, c4 = st.columns(2, gap="medium")
    o = core.oof_sample()
    with c3, style.card("ml-scatter"):
        style.sec("Predicted vs actual", "🎯", "4,000 cross-validated predictions")
        which = st.segmented_control("Test ", ["Known project", "New project"], default="New project", key="ml_sc") or "New project"
        col = "known_lakh" if which == "Known project" else "new_lakh"
        line = pd.DataFrame({"x": [15, 2500], "y": [15, 2500]})
        pts = alt.Chart(o).mark_circle(size=18, opacity=0.45, color=style.BLUE).encode(
            x=alt.X("actual_lakh:Q", scale=alt.Scale(type="log", domain=[15, 2500], nice=False), axis=ui.log_lakh_axis("Actual asking price")),
            y=alt.Y(f"{col}:Q", scale=alt.Scale(type="log", domain=[15, 2500], nice=False), axis=ui.log_lakh_axis("Predicted")),
            tooltip=[alt.Tooltip("Zone:N"), alt.Tooltip("BHK:Q"), alt.Tooltip("actual_lakh:Q", title="Actual (lakh)", format=",.1f"),
                     alt.Tooltip(f"{col}:Q", title="Predicted (lakh)", format=",.1f")])
        diag = alt.Chart(line).mark_line(color="#9b7dff", strokeDash=[5, 4]).encode(x="x:Q", y="y:Q")
        ui.chart(pts + diag, 330)
    with c4, style.card("ml-zone"):
        style.sec("Error by zone", "🗺️", "gradient boosting")
        style.legend([("Known project", style.BLUE), ("New project", style.ORANGE)])
        z = pd.DataFrame([{"Zone": zn, "test": t, "err": v["median_error_pct"]}
                          for t in ["Known project", "New project"] for zn, v in ev[t]["_by_zone_gbm"].items()])
        c = alt.Chart(z).mark_bar(cornerRadiusEnd=3, height=alt.RelativeBandSize(0.8)).encode(
            y=alt.Y("Zone:N", sort=alt.EncodingSortField("err", op="max", order="descending"), title=None,
                    axis=alt.Axis(labelLimit=190)),
            yOffset=alt.YOffset("test:N", sort=["Known project", "New project"]),
            x=alt.X("err:Q", title="Median error (%)"),
            color=alt.Color("test:N", scale=alt.Scale(domain=["Known project", "New project"], range=[style.BLUE, style.ORANGE]),
                            legend=None),
            tooltip=["Zone", "test", alt.Tooltip("err:Q", title="Median error %")])
        ui.chart(c, 330)
        st.caption("South Mumbai and Thane are hardest: a sea view or a lake-facing tower changes the price, "
                   "and the data can't see either.")

    with style.card("ml-ranges"):
        style.sec("Are the price ranges honest?", "📏", "cross-conformal check")
        a, b = st.columns([1, 1.3], gap="medium")
        with a:
            k8, n8 = iv["Known project"]["0.8"], iv["New project"]["0.8"]
            sz = n8["by_zone"]
            style.tiles([("Known project, 80% range", f"{k8['coverage_pct']:.0f}%", "of held-out flats fell inside"),
                         ("New project, 80% range", f"{n8['coverage_pct']:.0f}%", "of held-out flats fell inside")])
            style.html(f"""<div class="card-p">Each range comes from the model's own cross-validated errors: the middle 80%
            of them. The limits are set on 4 folds and checked on the 5th. <b>One width per zone</b>: a single width for all
            of Mumbai covered 80% overall, but only {n8['coverage_by_zone_one_width']['South Mumbai']:.0f}% of new-project
            flats in South Mumbai and {n8['coverage_by_zone_one_width']['Mira Road & Vasai-Virar']:.0f}% in Mira Road.
            New-project range in South Mumbai: {100 * (np.exp(sz['South Mumbai']['lo']) - 1):+.0f}% to
            {100 * (np.exp(sz['South Mumbai']['hi']) - 1):+.0f}%; in Mira Road: {100 * (np.exp(sz['Mira Road & Vasai-Virar']['lo']) - 1):+.0f}%
            to {100 * (np.exp(sz['Mira Road & Vasai-Virar']['hi']) - 1):+.0f}%.</div>""")
        with b:
            cz = pd.DataFrame({"One width (new)": n8["coverage_by_zone_one_width"],
                               "Per zone (new)": n8["coverage_by_zone"],
                               "Per zone (known)": k8["coverage_by_zone"]})
            cz = cz.map(lambda v: f"{v:.0f}%")
            cz.index.name = "Zone"
            st.dataframe(cz, width="stretch")
            st.caption("Target: 80% in every zone.")
