"""Front page: sign in with a name and a mobile number or email, or skip.

If the app has a `signin_webhook` secret (a Google Apps Script web-app URL), each sign-in is appended to
a private Google Sheet. Without it the form still works; nothing is stored. See docs/SIGNIN_SETUP.md.
"""
import json
import re
import urllib.request
from datetime import datetime, timezone

import streamlit as st

import art
import core
import style

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def clean_contact(text):
    """Return (kind, value) for a valid Indian mobile or an email, else (None, reason)."""
    t = text.strip()
    if EMAIL.match(t):
        return "email", t.lower()
    digits = re.sub(r"[\s\-()]", "", t)
    digits = re.sub(r"^(\+91|0091|91(?=\d{10}$)|0(?=\d{10}$))", "", digits)
    if re.fullmatch(r"[6-9]\d{9}", digits):
        return "mobile", digits
    return None, "Enter a 10-digit mobile number or an email address."


def save(name, contact, kind):
    """Best effort: a failure here never blocks the visitor."""
    try:
        url = st.secrets.get("signin_webhook", "")
    except Exception:
        url = ""
    if not url:
        return False
    body = json.dumps({"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), "name": name,
                       "contact": contact, "kind": kind, "app": "property-price-lab"}).encode()
    try:
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=6).read(200)
        return True
    except Exception:
        return False


def render(go):
    st.markdown(style.HIDE_SIDEBAR, unsafe_allow_html=True)
    ev = core.js("eval")
    new = ev["New project"]["Gradient boosting"]["median_error_pct"]
    left, right = st.columns([1.35, 1], gap="large")
    with left:
        style.html(f"""<div class="brand" style="border:0;padding-left:0"><div class="logo">PL</div><div>
        <div class="name">Property Price Lab</div><div class="sub">MUMBAI METROPOLITAN REGION</div></div></div>
        <div class="signin-hero"><div class="eyebrow">PRICE · PLAN · SEGMENT</div>
        <h1>What should a flat in Mumbai cost?</h1>
        <p>Price any flat with an honest range, plan a new launch against nearby projects, and see who buys what.
        Built from 54,598 property listings.</p></div>""")
        style.html(art.city(330))
        style.tiles([("Listings", "54,598", "after removing duplicates"), ("Localities", "175", "in 7 zones"),
                     ("Error on new launches", f"±{new:.0f}%", "projects the model never saw")])
    with right, style.card("signin"):
        style.html("""<div class="signin-head"><div class="mini-plan" aria-hidden="true">
        <div style="left:0;top:0;width:56%;height:60%;border-right:1px solid #c9d1d9;border-bottom:1px solid #c9d1d9"></div>
        <div style="left:56%;top:0;width:44%;height:50%;border-bottom:1px solid #c9d1d9;background:rgba(245,165,36,.25)"></div>
        <div style="left:56%;top:50%;width:44%;height:50%;background:rgba(245,165,36,.25)"></div>
        <div style="left:30%;top:60%;width:1px;height:40%;background:#c9d1d9"></div></div>
        <div class="sec" style="margin:0"><div class="t"><i>01</i>SIGN IN</div></div></div>
        <div style="font-size:30px;font-weight:700;letter-spacing:-0.02em;margin:.3rem 0 .1rem">Enter the lab</div>
        <div class="card-p" style="margin-bottom:.6rem">Tell me who's visiting. It takes ten seconds.</div>""")
        with st.form("signin", border=False):
            name = st.text_input("Name", placeholder="Your full name", max_chars=60)
            contact = st.text_input("Mobile number or email", placeholder="98765 43210 or you@company.com", max_chars=80)
            sent = st.form_submit_button("ENTER PROPERTY PRICE LAB →", type="primary", width="stretch")
        if sent:
            kind, value = clean_contact(contact)
            if len(name.strip()) < 2:
                st.error("Please enter your name.")
            elif kind is None:
                st.error(value)
            else:
                save(name.strip(), value, kind)
                st.session_state.visitor = name.strip().split()[0].title()
                go("Home")
                st.rerun()
        if st.button("Skip for now", type="tertiary", width="stretch", key="skip"):
            st.session_state.visitor = "guest"
            go("Home")
            st.rerun()
        style.html('<div class="signin-note">Your details are only used to see who visited the app. '
                   'They are never shared or used for marketing.</div>')
        style.html('<div class="foot" style="text-align:center">BUILT BY ESHAN VIJAYVARGIYA · ASKING PRICES FROM '
                   'MAKAAN.COM LISTINGS (KAGGLE)</div>')
