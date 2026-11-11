"""Page design: deep-navy 'glass' dashboard, plus small HTML helpers for cards, tiles and headers."""
import streamlit as st

# Chart colours: validated dark-mode categorical steps (colour-blind safe on the dark surface).
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET = ("#3987e5", "#d95926", "#199e70", "#c98500", "#d55181",
                                                      "#008300", "#9085e9")
INK, SOFT, MUTED, GRID = "#eef1ff", "#a9b0d6", "#7480a8", "rgba(160,170,230,0.10)"
ACCENT = "#7c5cff"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap');
html, body, .stApp { font-family: 'Inter', 'Segoe UI', Arial, sans-serif; }
.stApp { background:
  radial-gradient(900px 420px at 8% -8%, rgba(124,92,255,.20) 0%, rgba(124,92,255,0) 60%),
  radial-gradient(800px 380px at 95% -5%, rgba(59,130,246,.16) 0%, rgba(59,130,246,0) 60%),
  #060a1c; }
h1, h2, h3, h4, .hero h1, .tile .v, .price-big { font-family: 'Plus Jakarta Sans', 'Inter', 'Segoe UI', Arial, sans-serif !important;
  letter-spacing: -0.015em; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 3.2rem; max-width: 1320px; }

/* sidebar */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0a0f26 0%, #070b1d 100%); border-right: 1px solid rgba(139,151,255,.10); }
[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"], [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
  justify-content: flex-start; border: 1px solid transparent; background: transparent; color: #c3c9ea; border-radius: 12px; }
[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"]:hover { background: rgba(124,92,255,.10); color: #fff; }
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] { justify-content: flex-start; border-radius: 12px; border: 1px solid rgba(160,140,255,.45);
  background: linear-gradient(90deg, rgba(124,92,255,.38), rgba(59,130,246,.22)); box-shadow: 0 0 18px rgba(124,92,255,.25); }
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] p { color: #fff !important; font-weight: 600; }
[data-testid="stBaseButton-primary"] { background: linear-gradient(90deg, #7c5cff, #3b82f6); border: 0; }
.brand { display: flex; gap: .7rem; align-items: center; margin: .1rem 0 1.2rem; }
.brand .name { font-family: 'Plus Jakarta Sans', 'Segoe UI', Arial, sans-serif; font-weight: 800; font-size: 1.2rem; color: #fff; line-height: 1.1; }
.brand .sub { color: #8f98c4; font-size: .78rem; margin-top: .1rem; }
.side-note { background: linear-gradient(160deg, rgba(124,92,255,.16), rgba(59,130,246,.08)); border: 1px solid rgba(139,151,255,.18);
  border-radius: 14px; padding: .7rem .8rem; margin-top: 1.2rem; color: #b8bfe6; font-size: .78rem; }
.side-note b { color: #fff; }
.foot { color: #6b76a3; font-size: .74rem; margin-top: 1rem; }
.foot a { color: #9aa3d6; }

/* glass surfaces: every bordered Streamlit container becomes a card */
div[class*="st-key-card-"], .glass {
  background: linear-gradient(160deg, rgba(31,40,86,.55) 0%, rgba(13,18,44,.70) 100%) !important;
  border: 1px solid rgba(139,151,255,.16) !important; border-radius: 18px !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.05), 0 14px 34px rgba(0,0,0,.30); }
div[class*="st-key-card-"] { padding: 1rem 1.1rem !important; }
.glass { padding: 1rem 1.15rem; margin-bottom: .9rem; }
.sec { display: flex; align-items: center; gap: .6rem; margin: .1rem 0 .6rem; }
.sec .ic { width: 28px; height: 28px; border-radius: 9px; display: grid; place-items: center; font-size: .95rem;
  background: linear-gradient(135deg, rgba(124,92,255,.45), rgba(59,130,246,.35)); }
.sec .t { font-family: 'Plus Jakarta Sans', 'Segoe UI', Arial, sans-serif; color: #fff; font-weight: 700; font-size: 1.04rem; }
.sec .s { color: #8f98c4; font-size: .78rem; font-weight: 400; line-height: 1.2; margin-top: .1rem; }
.sec .ic { flex: 0 0 auto; }

/* hero */
.hero { position: relative; overflow: hidden; border-radius: 22px; padding: 1.6rem 1.8rem 1.5rem; margin-bottom: 1.1rem;
  background: linear-gradient(115deg, rgba(40,32,110,.85) 0%, rgba(18,26,70,.85) 55%, rgba(14,40,90,.85) 100%);
  border: 1px solid rgba(160,140,255,.25); box-shadow: 0 18px 40px rgba(0,0,0,.35); }
.hero .eyebrow { color: #b9a8ff; font-weight: 600; font-size: .76rem; letter-spacing: .16em; text-transform: uppercase; }
.hero h1 { color: #fff; font-size: 2.2rem; font-weight: 800; margin: .2rem 0 .3rem; line-height: 1.1; }
.hero p { color: #c3c9ea; margin: 0; font-size: 1rem; max-width: 720px; }
.hero svg.sky { position: absolute; right: 0; bottom: 0; opacity: .38; z-index: 0; }
.hero > div, .hero > h1, .hero > p { position: relative; z-index: 1; }

/* tiles */
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: .8rem; margin: .2rem 0 1rem; }
.tile { background: linear-gradient(160deg, rgba(31,40,86,.55), rgba(13,18,44,.7)); border: 1px solid rgba(139,151,255,.16);
  border-radius: 16px; padding: .8rem 1rem; }
.tile .l { color: #9aa3d6; font-size: .78rem; font-weight: 500; }
.tile .v { color: #fff; font-size: 1.55rem; white-space: nowrap; font-weight: 800; line-height: 1.15; margin-top: .2rem; }
.tile .n { color: #7f89b8; font-size: .76rem; margin-top: .15rem; }
.tile .up { color: #34d399; } .tile .down { color: #f87171; }

/* price result */
.price-card { border-radius: 20px; padding: 1.2rem 1.3rem; position: relative; overflow: hidden;
  background: linear-gradient(135deg, rgba(124,92,255,.30) 0%, rgba(59,130,246,.18) 60%, rgba(34,211,238,.10) 100%);
  border: 1px solid rgba(170,150,255,.35); box-shadow: 0 0 30px rgba(124,92,255,.18); }
.price-card .l { color: #c9c2ff; font-size: .8rem; font-weight: 600; letter-spacing: .12em; text-transform: uppercase; }
.price-big { font-size: 3rem; font-weight: 800; line-height: 1.05; margin: .25rem 0 .15rem;
  background: linear-gradient(90deg, #ffffff, #c9bbff); -webkit-background-clip: text; background-clip: text; color: transparent; }
.price-card .r { color: #dfe3ff; font-size: .98rem; } .price-card .r b { color: #fff; }
.range { position: relative; height: 10px; border-radius: 99px; background: rgba(255,255,255,.10); margin: .8rem 0 .35rem; }
.range span { position: absolute; top: 0; bottom: 0; border-radius: 99px; background: linear-gradient(90deg, #7c5cff, #22d3ee); }
.range i { position: absolute; top: -4px; width: 4px; height: 18px; border-radius: 3px; background: #fff; box-shadow: 0 0 10px #fff; }
.price-card .meta { color: #aeb5e0; font-size: .82rem; }

/* chips, badges, lists */
.chip { display: inline-block; padding: .2rem .6rem; border-radius: 999px; font-size: .78rem; font-weight: 600; margin: 0 .3rem .35rem 0;
  background: rgba(124,92,255,.14); color: #e3dcff; border: 1px solid rgba(160,140,255,.28); }
.chip.blue { background: rgba(59,130,246,.14); color: #d6e6ff; border-color: rgba(59,130,246,.35); }
.chip.green { background: rgba(16,185,129,.14); color: #c8f5e4; border-color: rgba(16,185,129,.35); }
.chip.amber { background: rgba(245,158,11,.14); color: #fde8c2; border-color: rgba(245,158,11,.35); }
.card-t { font-family: 'Plus Jakarta Sans', 'Segoe UI', Arial, sans-serif; color: #fff; font-weight: 700; font-size: 1.05rem; margin: 0 0 .3rem; }
.card-p { color: #b6bde4; font-size: .9rem; margin: .15rem 0; line-height: 1.5; }
.card-p b { color: #fff; }
.insight { border-left: 3px solid #7c5cff; padding-left: .8rem; }
.mtab { width: 100%; border-collapse: collapse; font-size: .87rem; }
.mtab th { color: #8f98c4; font-weight: 500; text-align: left; padding: .35rem .45rem; border-bottom: 1px solid rgba(139,151,255,.16); }
.mtab td { color: #dde1fb; padding: .35rem .45rem; border-bottom: 1px solid rgba(139,151,255,.08); }
.mtab tr.best td { color: #fff; font-weight: 700; } .mtab tr.best td:first-child:before { content: "★ "; color: #c9bbff; }
.seg { border-radius: 16px; padding: .9rem 1rem; height: 100%; border: 1px solid rgba(139,151,255,.16);
  background: linear-gradient(160deg, rgba(31,40,86,.55), rgba(13,18,44,.7)); border-top: 3px solid var(--c); }
.seg h4 { margin: 0 0 .15rem; color: #fff; font-size: 1.02rem; } .seg .who { color: #c9bbff; font-size: .82rem; font-weight: 600; }
.seg p { color: #b6bde4; font-size: .84rem; margin: .3rem 0 0; } .seg .num { color: #fff; font-weight: 700; }
.steps { display: flex; flex-wrap: wrap; gap: .5rem; align-items: center; margin: .2rem 0 1rem; }
.steps div { background: rgba(124,92,255,.10); border: 1px solid rgba(160,140,255,.22); border-radius: 12px; padding: .45rem .7rem;
  color: #e3e6ff; font-size: .85rem; } .steps span { color: #b9a8ff; font-weight: 700; }

/* tabs as pills */
[role="tablist"] { gap: .45rem; border-bottom: 0 !important; box-shadow: none !important; margin-bottom: .4rem; }
[data-testid="stTab"] { background: rgba(31,40,86,.45); border: 1px solid rgba(139,151,255,.16); border-radius: 12px;
  padding: .4rem .95rem !important; height: auto; }
[data-testid="stTab"] p { color: #c3c9ea; font-weight: 500; }
[data-testid="stTab"][aria-selected="true"] { background: linear-gradient(90deg, rgba(124,92,255,.45), rgba(59,130,246,.30));
  border-color: rgba(170,150,255,.5); box-shadow: 0 0 16px rgba(124,92,255,.25); }
[data-testid="stTab"][aria-selected="true"] p { color: #fff; font-weight: 600; }
.react-aria-SelectionIndicator { display: none !important; }

/* left-aligned nav and link buttons */
[data-testid="stSidebar"] button > div, div[class*="st-key-card-go"] button > div { justify-content: flex-start !important; width: 100%; }
div[class*="st-key-card-go"] button { justify-content: flex-start; text-align: left; padding: .55rem .8rem; }
div[class*="st-key-card-go"] button p { text-align: left; }

/* html legend */
.lg { display: flex; flex-wrap: wrap; gap: .35rem 1rem; margin: -.1rem 0 .4rem; }
.lg span { display: inline-flex; align-items: center; gap: .4rem; color: #c3c9ea; font-size: .8rem; }
.lg i { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
</style>
"""

LOGO = """<svg width="40" height="40" viewBox="0 0 40 40"><defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#8b6dff"/><stop offset="1" stop-color="#3b82f6"/></linearGradient></defs>
<rect width="40" height="40" rx="12" fill="url(#lg)"/>
<path d="M9 30V17l7-4v17M16 30V10l8 4v16M24 30V19l7 3v8" stroke="#fff" stroke-width="2" fill="none" stroke-linejoin="round"/>
<path d="M7 30h26" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>"""

SKYLINE = """<svg class="sky" width="430" height="150" viewBox="0 0 430 150"><defs><linearGradient id="sk" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#a48bff" stop-opacity=".9"/><stop offset="1" stop-color="#3b82f6" stop-opacity=".05"/></linearGradient></defs>
<g fill="url(#sk)"><rect x="20" y="70" width="34" height="80"/><rect x="60" y="40" width="28" height="110"/><rect x="94" y="85" width="40" height="65"/>
<rect x="140" y="20" width="30" height="130"/><rect x="176" y="60" width="36" height="90"/><rect x="218" y="5" width="26" height="145"/>
<rect x="250" y="50" width="42" height="100"/><rect x="298" y="78" width="30" height="72"/><rect x="334" y="35" width="34" height="115"/>
<rect x="374" y="90" width="40" height="60"/></g>
<g fill="#fff" opacity=".35"><rect x="66" y="50" width="4" height="4"/><rect x="76" y="62" width="4" height="4"/><rect x="146" y="32" width="4" height="4"/>
<rect x="156" y="48" width="4" height="4"/><rect x="224" y="20" width="4" height="4"/><rect x="232" y="40" width="4" height="4"/>
<rect x="258" y="62" width="4" height="4"/><rect x="342" y="48" width="4" height="4"/><rect x="352" y="66" width="4" height="4"/></g></svg>"""


def setup():
    st.markdown(CSS, unsafe_allow_html=True)


def html(text):
    st.markdown(" ".join(line.strip() for line in text.splitlines()), unsafe_allow_html=True)


def hero(title, subtitle, eyebrow="Mumbai Metropolitan Region · 54,598 listings"):
    html(f'<div class="hero">{SKYLINE}<div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{subtitle}</p></div>')


def tiles(items):
    """items: (label, value, note) tuples."""
    cells = "".join(f'<div class="tile"><div class="l">{i[0]}</div><div class="v">{i[1]}</div><div class="n">{i[2]}</div></div>'
                    for i in items)
    html(f'<div class="tiles">{cells}</div>')


def sec(title, icon="", sub=""):
    s = f'<div class="s">{sub}</div>' if sub else ""
    html(f'<div class="sec"><div class="ic">{icon}</div><div><div class="t">{title}</div>{s}</div></div>')


def legend(items):
    """HTML legend above a chart: items = [(label, colour)]. Keeps the chart full width."""
    html('<div class="lg">' + "".join(f'<span><i style="background:{c}"></i>{t}</span>' for t, c in items) + "</div>")


def glass(title, body, insight=False):
    html(f'<div class="glass"><div class="card-t">{title}</div><div class="{"insight" if insight else ""}">{body}</div></div>')


def card(key):
    """A glass card that can hold Streamlit widgets and charts:  with style.card("x"): ..."""
    return st.container(border=True, key=f"card-{key}")
