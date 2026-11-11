"""Mumbai Property Price Lab: price estimates, launch pricing, buyer segments and price drivers
for the Mumbai Metropolitan Region, from 54,598 cleaned listings.

Run from the project folder:  python -m streamlit run app/app.py
"""
import importlib

import streamlit as st

import art
import core
import features
import places
import style
import ui

# After a git push, Streamlit Cloud re-runs this file but can keep OLD helper modules in memory.
for _module in (places, features, art, style, ui, core):
    importlib.reload(_module)

import pg_data  # noqa: E402  (page modules import the helpers above, so they load after the reload)
import pg_drivers  # noqa: E402
import pg_estimate  # noqa: E402
import pg_home  # noqa: E402
import pg_launch  # noqa: E402
import pg_login  # noqa: E402
import pg_market  # noqa: E402
import pg_models  # noqa: E402
import pg_segments  # noqa: E402

for _module in (pg_login, pg_home, pg_estimate, pg_launch, pg_market, pg_segments, pg_drivers, pg_models, pg_data):
    importlib.reload(_module)

st.set_page_config(page_title="Mumbai Property Price Lab", page_icon="🏙️", layout="wide",
                   initial_sidebar_state="expanded")
style.setup()
state = st.session_state
state.setdefault("page", "Home")

PAGES = {
    "Home": pg_home.render,
    "Price estimator": pg_estimate.render,
    "Launch planner": pg_launch.render,
    "Market explorer": pg_market.render,
    "Buyer segments": pg_segments.render,
    "Price drivers": pg_drivers.render,
    "Model lab": pg_models.render,
    "About the data": pg_data.render,
}


def go(page):
    state.page = page


# Front page first: sign in (name + mobile or email) or skip. Stays signed in for the browser session.
if "visitor" not in state:
    pg_login.render(go)
    st.stop()

with st.sidebar:
    style.html('<div class="brand"><div class="logo">PL</div><div><div class="name">Property Price Lab</div>'
               '<div class="sub">MMR · 54,598 LISTINGS</div></div></div>')
    for i, name in enumerate(PAGES, start=1):
        if st.button(f"{i:02d}  {name}", key=f"nav_{name}", width="stretch",
                     type="primary" if state.page == name else "tertiary"):
            go(name)
            st.rerun()
    ev, iv = core.js("eval"), core.js("intervals")
    style.html(f"""<div class="statusbox"><div class="t">MODEL STATUS</div>
    <div>gbm · price rises with area</div>
    <div>cv known&nbsp;&nbsp;<b>±{ev['Known project']['Gradient boosting']['median_error_pct']:.1f}%</b></div>
    <div>cv new&nbsp;&nbsp;&nbsp;&nbsp;<b>±{ev['New project']['Gradient boosting']['median_error_pct']:.1f}%</b></div>
    <div>80% range <span class="ok">{iv['New project']['0.8']['coverage_pct']:.1f}% hit</span></div></div>""")
    who = "guest" if state.visitor == "guest" else state.visitor
    style.html(f"""<div class="who">SIGNED IN AS <b>{who.upper()}</b></div>
    <div class="foot">Asking prices from Makaan.com listings (Kaggle: Mumbai House Prices), not sale prices.<br>
    Built by Eshan Vijayvargiya · <a href="https://github.com/Eshan-vijayvargiya/property-price-prediction">code</a></div>""")

style.crumbs(list(PAGES).index(state.page) + 1, state.page)
if state.page == "Home":
    pg_home.render(go)
else:
    PAGES[state.page]()
