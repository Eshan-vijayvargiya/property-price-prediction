"""About the data: source, every cleaning step, the zones, and why the popular six-city dataset wasn't used."""
import altair as alt
import pandas as pd
import streamlit as st

import core
import places
import style
import ui


def render():
    rep = core.js("cleaning_report")
    six = core.js("six_city_check")
    style.html('<div class="card-t" style="font-size:1.6rem">About the data</div>'
               '<div class="card-p" style="margin-bottom:.8rem"><b>Mumbai House Prices</b> by Dravid Vaishnav on Kaggle: '
               f'{rep["raw_rows"]:,} flat listings across the Mumbai Metropolitan Region, scraped from Makaan.com. Columns: '
               'BHK, type, project, area, price, locality, construction status and new/resale. No licence is stated on the '
               'Kaggle page, so it is used here for learning, with credit.</div>')
    with style.card("dt-funnel"):
        style.sec("Every cleaning step", "🧹", f"{rep['raw_rows']:,} → {rep['clean_rows']:,} listings")
        steps = pd.DataFrame(rep["steps"])
        steps = steps[steps.removed > 0]
        steps["label"] = steps.removed.map(lambda v: f"−{v:,}")
        base = alt.Chart(steps).encode(y=alt.Y("rule:N", sort=None, title=None, axis=alt.Axis(labelLimit=460)))
        bars = base.mark_bar(cornerRadiusEnd=3, height=16, color=style.ORANGE).encode(
            x=alt.X("removed:Q", title="Listings removed (compressed scale)", scale=alt.Scale(type="symlog"), axis=alt.Axis(values=[0, 10, 100, 1000, 10000, 20000], format=",")),
            tooltip=[alt.Tooltip("rule:N", title="Rule"), alt.Tooltip("removed:Q", title="Removed", format=",")])
        text = base.mark_text(align="left", dx=4, color=style.INK, fontSize=11).encode(x="removed:Q", text="label:N")
        ui.chart(bars + text, 250)
        st.caption("Duplicates were the big one: 27% of rows. Left in, the same flat lands in both the training and the "
                   "test data and the model looks better than it is. A rule for impossible sizes (under 150 sq ft per "
                   "bedroom) was also checked and removed nothing.")
    with style.card("dt-zones"):
        style.sec("The seven zones", "🗺️", "localities matched by whole words, after tidying spellings")
        rows = [{"Zone": z, "Includes (examples)": ", ".join(k.title() for k in keys[:9]) + " …"} for z, keys in places.ZONES]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.caption("Whole-word matching, so 'Khar' doesn't swallow 'Kharghar'. Spellings are tidied first "
                   "('Dombivali' → 'Dombivli', 'Sector-12 Kamothe' → 'Kamothe').")

    with style.card("dt-six"):
        style.sec("The dataset I didn't use, and why", "🕵️", "Kaggle: Housing Prices in Metropolitan Areas of India")
        s = pd.DataFrame(six["mumbai_sample"])
        cols = st.columns(2, gap="medium")
        for col, batch, color in zip(cols, ["Amenities listed", "Amenities missing"], [style.BLUE, style.YELLOW]):
            r = six["cities"]["Mumbai"][batch]
            with col:
                style.html(f'<div class="card-p"><b>Mumbai, {batch.lower()}</b> · {r["rows"]:,} rows · '
                           f'price vs area correlation <b>{r["r_price_area"]:.2f}</b></div>')
                pts = alt.Chart(s[s.batch == batch]).mark_circle(size=20, opacity=0.5, color=color, clip=True).encode(
                    x=alt.X("area:Q", scale=alt.Scale(type="log", domain=[250, 6000], nice=False),
                            axis=alt.Axis(title="Area (sq ft)", values=[300, 500, 1000, 2000, 5000])),
                    y=alt.Y("price_lakh:Q", scale=alt.Scale(type="log", domain=[15, 3000], nice=False),
                            axis=ui.log_lakh_axis("Price")),
                    tooltip=["area", "price_lakh"])
                ui.chart(pts, 250)
        style.html("""<div class="card-p">It's popular for price models, so I checked it first. In every city the file is two
        batches: rows with amenities filled in, then rows where every amenity is coded 9 ("not mentioned"). In the second
        batch, <b>area and bedrooms still agree (correlation ~0.8), but price barely relates to either (~0.2)</b>, against
        ~0.85 in the first batch. A bigger flat should cost more; here it doesn't. The price column looks shifted against
        the rest of the row, for about 70% of the data (99% of Kolkata). A model trained on it learns noise, so I switched
        datasets.</div>""")
        rows = []
        for city, v in six["cities"].items():
            for batch, m in v.items():
                rows.append({"City": city, "Rows": batch, "Count": m["rows"], "Price vs area": m["r_price_area"],
                             "Price vs bedrooms": m["r_price_bedrooms"], "Area vs bedrooms": m["r_area_bedrooms"]})
        with st.expander("All six cities"):
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
            st.caption("Correlations of log price, log area and bedroom count. Hyderabad has almost no second batch; "
                       "Kolkata almost no first.")

    with style.card("dt-limits"):
        style.sec("What the data can't tell you", "⚠️")
        style.html("""<div class="card-p">
        • <b>Asking prices, not sale prices.</b> Registered sale values are usually lower; the gap varies by market.<br>
        • <b>No dates.</b> Prices are a snapshot from one scrape (around 2022-23 by the Kaggle upload), so no trends.<br>
        • <b>Carpet vs built-up area are mixed</b>, which is why bedrooms carry extra size information.<br>
        • <b>No floor, view, amenities, parking or builder.</b> These are most of what's left in the error, especially in
        South Mumbai and Thane.<br>
        • <b>Listings, not homes.</b> Big projects post many listings, so they weigh more in averages.</div>""")
