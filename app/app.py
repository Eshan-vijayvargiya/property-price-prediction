"""Mumbai Property Price Lab: price estimates, launch pricing, buyer segments and price drivers
for the Mumbai Metropolitan Region, from 54,598 cleaned listings.

Run from the project folder:  python -m streamlit run app/app.py
"""
import importlib

import streamlit as st

import core
import features
import places
import style
import ui

# After a git push, Streamlit Cloud re-runs this file but can keep OLD helper modules in memory.
for _module in (places, features, style, ui, core):
    importlib.reload(_module)

import pg_data  # noqa: E402  (page modules import the helpers above, so they load after the reload)
import pg_drivers  # noqa: E402
import pg_estimate  # noqa: E402
import pg_home  # noqa: E402
import pg_launch  # noqa: E402
import pg_market  # noqa: E402
import pg_models  # noqa: E402
import pg_segments  # noqa: E402

for _module in (pg_home, pg_estimate, pg_launch, pg_market, pg_segments, pg_drivers, pg_models, pg_data):
    importlib.reload(_module)

st.set_page_config(page_title="Mumbai Property Price Lab", page_icon="🏙️", layout="wide",
                   initial_sidebar_state="expanded")
style.setup()
state = st.session_state
state.setdefault("page", "Home")

PAGES = {
    "Home": (":material/home:", pg_home.render),
    "Price estimator": (":material/calculate:", pg_estimate.render),
    "Launch planner": (":material/apartment:", pg_launch.render),
    "Market explorer": (":material/travel_explore:", pg_market.render),
    "Buyer segments": (":material/groups:", pg_segments.render),
    "Price drivers": (":material/trending_up:", pg_drivers.render),
    "Model lab": (":material/science:", pg_models.render),
    "About the data": (":material/database:", pg_data.render),
}


def go(page):
    state.page = page


with st.sidebar:
    style.html(f'<div class="brand">{style.LOGO}<div><div class="name">Property Price Lab</div>'
               f'<div class="sub">Mumbai · Predict · Segment</div></div></div>')
    for name, (icon, _) in PAGES.items():
        if st.button(name, icon=icon, key=f"nav_{name}", width="stretch",
                     type="primary" if state.page == name else "tertiary"):
            go(name)
            st.rerun()
    style.html("""<div class="side-note"><b>Asking prices, not sale prices.</b> Listings scraped from Makaan.com
    (Kaggle: Mumbai House Prices). Estimates show what similar flats are <i>listed</i> for.</div>
    <div class="foot">Built by Eshan Vijayvargiya ·
    <a href="https://github.com/Eshan-vijayvargiya/property-price-prediction">code</a></div>""")

if state.page == "Home":
    pg_home.render(go)
else:
    PAGES[state.page][1]()
