"""Buyer segments: K-Means on size and price per sq ft, with who each segment suits."""
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import core
import style
import ui
from features import ZONES

WHO = {
    "Budget starter homes": ("First-time buyers",
                             "Young couples moving out of rented homes, on a tight budget, ready to commute far."),
    "Spacious value homes": ("Growing families",
                             "Want a second bedroom and space for the price; accept a longer commute."),
    "Compact city homes": ("Young professionals",
                           "Pay for a short commute to Andheri, BKC or Powai and accept a small flat."),
    "Premium family homes": ("Established professionals",
                             "Upgrading within the suburbs: a bigger 2 BHK near work, schools and malls."),
    "Large luxury homes": ("Senior executives, business owners",
                           "3 BHK and bigger in prime areas, where space and address both count."),
}


def render():
    d = core.listings()
    s = core.segmenter()
    style.html('<div class="card-t" style="font-size:1.6rem">Buyer segments</div>'
               '<div class="card-p" style="margin-bottom:.8rem">K-Means clustering on two things every buyer trades off: '
               '<b>how big</b> the flat is and <b>how premium the location</b> is (price per sq ft). Five segments came out, '
               'each a different kind of buyer.</div>')
    g = d.groupby("Segment")
    prof = pd.DataFrame({"n": g.size(), "p25": g.Price.quantile(0.25), "p75": g.Price.quantile(0.75),
                         "area": g.Area.median(), "ppsf": g.ppsf.median(), "bhk": g.BHK.agg(lambda x: x.mode()[0]),
                         "uc": g.Status.agg(lambda x: 100 * (x == "Under construction").mean()),
                         "zones": g.Zone.agg(lambda x: ", ".join(x.value_counts().head(2).index))}).reindex(ui.SEGMENTS)
    # the localities where each segment is most concentrated (share of the locality's listings), not just the biggest
    big = d.Locality.value_counts()
    share = pd.crosstab(d.Locality, d.Segment, normalize="index").loc[big[big >= 100].index]
    prof["locs"] = [", ".join(share[n].sort_values(ascending=False).head(3).index) for n in prof.index]
    cols = st.columns(5, gap="small")
    for col, (name, r), color in zip(cols, prof.iterrows(), ui.SEG_COLORS):
        who, why = WHO[name]
        with col:
            style.html(f"""<div class="seg" style="--c:{color}"><h4>{name}</h4><div class="who">{who}</div>
            <p><span class="num">{core.inr(r.p25)} – {core.inr(r.p75)}</span><br>{int(r.area):,} sq ft · {r.bhk} BHK typical<br>
            {core.psf(r.ppsf)}</p><p>{why}</p>
            <p style="color:#8f98c4">Mostly {r.zones}<br>Most typical in {r.locs}<br>{100 * r.n / len(d):.0f}% of listings · {r.uc:.0f}% under construction</p></div>""")

    c1, c2 = st.columns([1.3, 1], gap="medium")
    with c1, style.card("seg-map"):
        style.sec("The map of the market", "🧭", "4,000 listings, both axes on a log scale")
        m = d.sample(4000, random_state=1)
        pts = alt.Chart(m).mark_circle(size=26, opacity=0.6, stroke="#060a1c", strokeWidth=0.4).encode(
            x=alt.X("Area:Q", scale=alt.Scale(type="log", domain=[250, 5000], nice=False),
                    axis=alt.Axis(title="Area (sq ft)", values=[300, 500, 700, 1000, 1500, 2000, 3000, 5000])),
            y=alt.Y("ppsf:Q", scale=alt.Scale(type="log", domain=[2500, 60000], nice=False),
                    axis=alt.Axis(title="₹ per sq ft", values=[3000, 5000, 7000, 10000, 15000, 20000, 30000, 50000])),
            color=alt.Color("Segment:N", scale=ui.SEG_SCALE, legend=None),
            tooltip=[alt.Tooltip("Segment:N"), alt.Tooltip("Locality:N"), alt.Tooltip("Project:N"),
                     alt.Tooltip("Area:Q", format=","), alt.Tooltip("ppsf:Q", title="₹/sq ft", format=",.0f"),
                     alt.Tooltip("price_lakh:Q", title="Price (lakh)", format=",.1f")])
        cent = pd.DataFrame(np.exp(s["scaler"].inverse_transform(s["kmeans"].cluster_centers_)), columns=["Area", "ppsf"])
        cent["Segment"] = [s["names"][i] for i in range(len(cent))]
        nudge = {"Premium family homes": 1.42, "Large luxury homes": 0.72, "Budget starter homes": 0.86}
        cent["ppsf"] = cent.ppsf * cent.Segment.map(nudge).fillna(1.0)  # keep the two premium labels apart
        lab = alt.Chart(cent).mark_text(fontSize=12, fontWeight=700, color="#ffffff", dy=-2).encode(
            x="Area:Q", y="ppsf:Q", text="Segment:N")
        halo = alt.Chart(cent).mark_text(fontSize=12, fontWeight=700, stroke="#060a1c", strokeWidth=4, dy=-2).encode(
            x="Area:Q", y="ppsf:Q", text="Segment:N")
        ui.chart(pts + halo + lab, 420)
        st.caption("Same budget, different homes: a compact city flat and a spacious value flat cost about the same. "
                   "The buyer chooses between location and space.")
    with c2, style.card("seg-zone"):
        style.sec("Where each segment lives", "📍", "share of each zone's listings")
        mix = d.groupby(["Zone", "Segment"]).size().rename("n").reset_index()
        mix["share"] = mix.n / mix.groupby("Zone").n.transform("sum")
        mix["o"] = mix.Segment.map({n: i for i, n in enumerate(ui.SEGMENTS)})
        style.legend(list(zip(ui.SEGMENTS, ui.SEG_COLORS)))
        c = alt.Chart(mix).mark_bar(height=18, stroke="#060a1c", strokeWidth=2).encode(
            y=alt.Y("Zone:N", sort=ZONES, title=None, axis=alt.Axis(labelLimit=170)),
            x=alt.X("share:Q", stack="normalize", title=None, axis=alt.Axis(format="%")),
            color=alt.Color("Segment:N", scale=ui.SEG_SCALE, legend=None),
            order=alt.Order("o:Q"),
            tooltip=[alt.Tooltip("Zone:N"), alt.Tooltip("Segment:N"), alt.Tooltip("share:Q", format=".0%"),
                     alt.Tooltip("n:Q", title="Listings", format=",")])
        ui.chart(c, 360)

    with style.card("seg-method"):
        style.sec("How the segments were made, and how solid they are", "🔬")
        a, b = st.columns([1, 1.2], gap="medium")
        with a:
            curve = pd.DataFrame(s["curve"])
            line = alt.Chart(curve).mark_line(color=style.BLUE, strokeWidth=2, point=alt.OverlayMarkDef(size=60, filled=True)).encode(
                x=alt.X("k:O", title="Number of segments (k)", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("silhouette:Q", title="Silhouette score", scale=alt.Scale(domain=[0, 0.6])),
                tooltip=["k", "silhouette", "inertia_per_row"])
            rule = alt.Chart(pd.DataFrame({"k": [5]})).mark_rule(color="#9b7dff", strokeDash=[4, 4]).encode(x="k:O")
            ui.chart(line + rule, 230)
        with b:
            ari = s["stability_ari"]
            style.html(f"""<div class="card-p"><b>Features:</b> log area and log price per sq ft, both standardised. Log scale
            because a ₹10k jump means more at ₹8k/sq ft than at ₹30k.<br>
            <b>Choosing k:</b> the silhouette score is flat from 3 to 7 (0.35–0.38). Mumbai's market is a smooth spread, not
            separate islands, so no k is "correct". I chose <b>5</b> because each segment is a buyer you can name and market to.<br>
            <b>Stability:</b> rerunning with 5 other random starts gives the same segments (adjusted Rand index
            {min(ari):.2f}–{max(ari):.2f}).<br>
            <b>Honest limit:</b> the data has homes, not buyers. The buyer labels are my reading of who each kind of home suits.</div>""")
