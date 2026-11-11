"""Market explorer: a locality price index, zone profiles and a deep-dive on any locality."""
import altair as alt
import pandas as pd
import streamlit as st

import core
import style
import ui
from features import ZONES

BHK_ORDER = ["1 BHK", "2 BHK", "3 BHK", "4+ BHK"]
BHK_COLORS = [style.AQUA, style.BLUE, style.VIOLET, style.MAGENTA]


def index_tab():
    t = core.localities()
    c1, c2 = st.columns([2, 1])
    with c1:
        zones = st.multiselect("Zones", ZONES, default=ZONES, key="mk_zones")
    with c2:
        min_n = st.slider("Minimum listings", 10, 500, 50, 10, key="mk_min",
                          help="Localities with few listings have shaky estimates.")
    s = t[t.Zone.isin(zones) & (t.listings >= min_n)].copy()
    if s.empty:
        st.info("No localities match. Lower the minimum listings.")
        return
    s["label"] = s.standard_flat_lakh.map(lambda v: core.inr(v * 1e5))
    ui.zone_legend(zones)
    order = s.sort_values("standard_flat_lakh", ascending=False).Locality.tolist()
    base = alt.Chart(s).encode(y=alt.Y("Locality:N", sort=order, title=None, axis=alt.Axis(labelLimit=170, labelOverlap=False)))
    bars = base.mark_bar(cornerRadiusEnd=3, height=alt.RelativeBandSize(0.72)).encode(
        x=alt.X("standard_flat_lakh:Q", axis=ui.lakh_axis("Standard 2 BHK, 950 sq ft, ready, new")),
        color=ui.zone_color(),
        tooltip=[alt.Tooltip("Locality:N"), alt.Tooltip("Zone:N"), alt.Tooltip("label:N", title="Standard flat"),
                 alt.Tooltip("median_ppsf:Q", title="Median ₹/sq ft", format=",.0f"),
                 alt.Tooltip("listings:Q", title="Listings", format=","), alt.Tooltip("projects:Q", title="Projects"),
                 alt.Tooltip("under_construction_pct:Q", title="% under construction", format=".0f")])
    text = base.mark_text(align="left", dx=4, color=style.INK, fontSize=10.5).encode(x="standard_flat_lakh:Q", text="label:N")
    ui.chart(bars + text, max(300, 21 * len(s)))
    st.caption("Every bar prices the same standard flat, so the bars compare places, not flat sizes. "
               "From the linear model with a separate effect for each locality.")


def zones_tab(d):
    g = d.groupby("Zone")
    z = pd.DataFrame({"Listings": g.size(), "Median price": g.Price.median().map(core.inr),
                      "Median ₹/sq ft": g.ppsf.median().map(core.group_in), "Median area": g.Area.median().astype(int),
                      "% under construction": g.Status.agg(lambda s: f"{100 * (s == 'Under construction').mean():.0f}%"),
                      "% resale": g.Age.agg(lambda s: f"{100 * (s == 'Resale').mean():.0f}%")}).reindex(ZONES)
    st.dataframe(z, width="stretch")
    m = d.assign(B=d.BHK.clip(upper=4).map(lambda b: f"{b} BHK" if b < 4 else "4+ BHK"))
    mix = m.groupby(["Zone", "B"]).size().rename("n").reset_index()
    mix["share"] = mix.n / mix.groupby("Zone").n.transform("sum")
    c = alt.Chart(mix).mark_bar(height=18, stroke="#060a1c", strokeWidth=2).encode(
        y=alt.Y("Zone:N", sort=ZONES, title=None, axis=alt.Axis(labelLimit=190)),
        x=alt.X("share:Q", stack="normalize", title="Share of listings", axis=alt.Axis(format="%")),
        color=alt.Color("B:N", scale=alt.Scale(domain=BHK_ORDER, range=BHK_COLORS), legend=None),
        order=alt.Order("B:N"),
        tooltip=[alt.Tooltip("Zone:N"), alt.Tooltip("B:N", title="Type"), alt.Tooltip("share:Q", format=".0%"),
                 alt.Tooltip("n:Q", title="Listings", format=",")])
    style.sec("What gets built where", "🧱", "flat types by zone")
    style.legend(list(zip(BHK_ORDER, BHK_COLORS)))
    ui.chart(c, 280)
    st.caption("1 BHKs dominate the far suburbs; 3 BHKs and bigger are a third of listings only in South Mumbai.")


def locality_tab(d):
    t = core.locality_table()
    opts = t[t.listings >= 20].sort_values("listings", ascending=False).index.tolist()
    loc = st.selectbox("Locality", opts, index=opts.index("Powai") if "Powai" in opts else 0, key="mk_loc")
    s = d[d.Locality == loc]
    r = t.loc[loc]
    style.tiles([("Listings", f"{len(s):,}", f"{s.Project.nunique()} projects · {r.Zone}"),
                 ("Median asking price", core.inr(s.Price.median()), f"median area {int(s.Area.median()):,} sq ft"),
                 ("Median ₹/sq ft", core.group_in(s.ppsf.median()), f"zone median {core.group_in(d[d.Zone == r.Zone].ppsf.median())}"),
                 ("Standard 2 BHK", core.inr(r.standard_flat_lakh * 1e5), "950 sq ft, ready, new"),
                 ("Under construction", f"{100 * (s.Status == 'Under construction').mean():.0f}%",
                  f"{100 * (s.Age == 'Resale').mean():.0f}% resale")])
    c1, c2 = st.columns([1.1, 1], gap="medium")
    with c1:
        style.sec("Prices by flat type", "📦", "each dot is a listing")
        style.legend(list(zip(BHK_ORDER, BHK_COLORS)))
        m = s.assign(B=s.BHK.clip(upper=4).map(lambda b: f"{b} BHK" if b < 4 else "4+ BHK"))
        m = m.sample(min(len(m), 1500), random_state=0)
        pts = alt.Chart(m).mark_circle(size=34, opacity=0.55, stroke="#060a1c", strokeWidth=0.5).encode(
            x=alt.X("Area:Q", scale=alt.Scale(type="log", nice=False),
                    axis=alt.Axis(title="Area (sq ft)", values=[300, 500, 700, 1000, 1500, 2000, 3000, 5000])),
            y=alt.Y("price_lakh:Q", scale=alt.Scale(type="log"), axis=ui.log_lakh_axis("Asking price")),
            color=alt.Color("B:N", scale=alt.Scale(domain=BHK_ORDER, range=BHK_COLORS), legend=None),
            tooltip=[alt.Tooltip("Project:N"), alt.Tooltip("B:N", title="Type"), alt.Tooltip("Area:Q", format=","),
                     alt.Tooltip("price_lakh:Q", title="Price (lakh)", format=",.1f"),
                     alt.Tooltip("ppsf:Q", title="₹/sq ft", format=",.0f"), alt.Tooltip("Status:N")])
        ui.chart(pts, 330)
    with c2:
        style.sec("Biggest projects", "🏢", "by number of listings")
        p = s.groupby("Project").agg(Listings=("Price", "size"), ppsf=("ppsf", "median"),
                                     uc=("Status", lambda x: 100 * (x == "Under construction").mean()),
                                     price=("Price", "median")).sort_values("Listings", ascending=False).head(12)
        st.dataframe(pd.DataFrame({"Listings": p.Listings, "Median price": p.price.map(core.inr),
                                   "Median ₹/sq ft": p.ppsf.map(core.group_in),
                                   "Under constr.": p.uc.map(lambda v: f"{v:.0f}%")}), width="stretch", height=330)


def render():
    d = core.listings()
    style.html('<div class="card-t" style="font-size:1.6rem">Market explorer</div>'
               '<div class="card-p" style="margin-bottom:.8rem">Where prices are high or low, what gets built where, '
               'and a close look at any locality.</div>')
    a, b, c = st.tabs(["Locality price index", "Zones", "Locality deep-dive"])
    with a, style.card("mk-index"):
        style.sec("What the same flat costs in each locality", "🏷️")
        index_tab()
    with b, style.card("mk-zones"):
        style.sec("The seven zones", "🗺️")
        zones_tab(d)
    with c, style.card("mk-loc"):
        locality_tab(d)
