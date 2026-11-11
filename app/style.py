"""Page design: a dark 'terminal' dashboard (IBM Plex, amber accent) plus small HTML helpers."""
import streamlit as st

import art

# Chart colours: validated categorical steps on the dark panel (#12161c), colour-blind checked.
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET = ("#3987e5", "#d95926", "#199e70", "#c98500", "#d55181",
                                                      "#008300", "#9085e9")
INK, SOFT, MUTED, GRID = "#e6edf3", "#9aa7b4", "#7d8a97", "#1d242d"
ACCENT = "#f5a524"      # amber, for text, buttons and the one highlighted mark
SLATE = "#5b6878"       # the "everything else" bars next to a highlighted one
UP, DOWN = "#3fb950", "#ff7b72"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
html, body, .stApp, .stApp p, .stApp label, .stApp input, .stApp textarea, .stApp button { font-family: 'IBM Plex Sans', 'Segoe UI', Arial, sans-serif; }
.stApp { background: #0b0d10; color: #e6edf3; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.4rem; max-width: 1400px; }
.mono, code { font-family: 'IBM Plex Mono', Consolas, monospace !important; }
h1, h2, h3 { color: #e6edf3; letter-spacing: -0.015em; }

/* sidebar: numbered mono navigation */
[data-testid="stSidebar"] { background: #0e1116; border-right: 1px solid #232a33; }
[data-testid="stSidebar"] button { justify-content: flex-start !important; border-radius: 4px !important; min-height: 40px; }
[data-testid="stSidebar"] button > div { justify-content: flex-start !important; width: 100%; }
[data-testid="stSidebar"] button p { font-family: 'IBM Plex Mono', Consolas, monospace !important; font-size: 13px; }
[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"] { color: #9aa7b4; background: transparent; border: 0; }
[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"]:hover { background: #161b22; color: #e6edf3; }
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] { background: #f5a524 !important; border: 0; }
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] p { color: #0b0d10 !important; font-weight: 600; }
.brand { display: flex; gap: .7rem; align-items: center; padding: 0 .2rem 1rem; margin-bottom: .6rem; border-bottom: 1px solid #232a33; }
.brand .logo { width: 32px; height: 32px; border: 1.5px solid #f5a524; border-radius: 6px; display: grid; place-items: center;
  font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 13px; color: #f5a524; }
.brand .name { font-weight: 700; font-size: 15px; color: #e6edf3; line-height: 1.2; }
.brand .sub { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #9aa7b4; }
.statusbox { border: 1px solid #232a33; border-radius: 6px; padding: .7rem .8rem; margin-top: 1.1rem;
  font-family: 'IBM Plex Mono', monospace; font-size: 11px; line-height: 1.75; color: #9aa7b4; }
.statusbox b { color: #e6edf3; font-weight: 500; } .statusbox .ok { color: #3fb950; } .statusbox .t { color: #e6edf3; }
.who { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #9aa7b4; margin-top: .9rem; }
.who b { color: #f5a524; font-weight: 500; }
.foot { color: #7d8a97; font-size: 11px; margin-top: .8rem; font-family: 'IBM Plex Mono', monospace; }
.foot a { color: #9aa7b4; }

/* top bar of every page */
.crumbs { display: flex; flex-wrap: wrap; justify-content: space-between; gap: .6rem; align-items: center;
  font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: #9aa7b4; padding-bottom: .8rem; margin-bottom: 1rem;
  border-bottom: 1px solid #232a33; }
.crumbs .here { color: #e6edf3; }
.crumbs .tags { display: flex; gap: .4rem; flex-wrap: wrap; }
.crumbs .tags span { border: 1px solid #232a33; border-radius: 4px; padding: 3px 8px; }
.crumbs .tags span.hot { border-color: #f5a524; color: #f5a524; }
div.card-t[style*="1.6rem"] { font-size: 30px !important; font-weight: 700; letter-spacing: -0.02em; margin-bottom: .2rem; }

/* panels: every keyed Streamlit container becomes one */
div[class*="st-key-card-"], .glass { background: #12161c !important; border: 1px solid #232a33 !important; border-radius: 6px !important; }
div[class*="st-key-card-"] { padding: 1rem 1.15rem !important; }
.glass { padding: 1rem 1.15rem; margin-bottom: .9rem; }
.sec { margin: 0 0 .7rem; }
.sec .t { font-family: 'IBM Plex Mono', monospace; font-size: 12px; font-weight: 600; letter-spacing: .1em; color: #9aa7b4; text-transform: uppercase; }
.sec .t i { font-style: normal; color: #f5a524; margin-right: .45rem; }
.sec .s { color: #7d8a97; font-size: 12px; margin-top: .15rem; }

/* hero (home) */
.hero { display: flex; flex-wrap: wrap; gap: 1.5rem; align-items: flex-end; background: #0e1116; border: 1px solid #232a33;
  border-radius: 6px; padding: 1.6rem 1.8rem 1.2rem; margin-bottom: 1rem; }
.hero .txt { flex: 1 1 380px; }
.hero .art { flex: 1 1 420px; min-width: 0; }
.hero .eyebrow { font-family: 'IBM Plex Mono', monospace; color: #f5a524; font-size: 12px; letter-spacing: .12em; }
.hero h1 { color: #e6edf3; font-size: 44px; font-weight: 700; margin: .3rem 0 .4rem; line-height: 1.06; letter-spacing: -0.025em; }
.hero p { color: #9aa7b4; margin: 0; font-size: 16px; line-height: 1.55; }

/* stat tiles: a grid with hairline gaps */
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 1px; background: #232a33;
  border: 1px solid #232a33; border-radius: 6px; overflow: hidden; margin: .2rem 0 1rem; }
.tile { background: #12161c; padding: .75rem .95rem; }
.tile .l { font-family: 'IBM Plex Mono', monospace; color: #9aa7b4; font-size: 11px; text-transform: uppercase; letter-spacing: .06em; }
.tile .v { font-family: 'IBM Plex Mono', Consolas, monospace; color: #e6edf3; font-size: 22px; font-weight: 500; margin-top: .2rem; white-space: nowrap; }
.tile .n { color: #7d8a97; font-size: 12px; margin-top: .1rem; }

/* estimate panel */
.est .l { font-family: 'IBM Plex Mono', monospace; font-size: 12px; font-weight: 600; letter-spacing: .1em; color: #9aa7b4; }
.est .big { font-family: 'IBM Plex Mono', monospace; font-size: 64px; font-weight: 600; color: #f5a524; letter-spacing: -0.03em; line-height: 1.1; margin-top: .4rem; }
.est .big span { font-size: 28px; color: #e6edf3; }
.est .rng { font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #9aa7b4; } .est .rng b { color: #e6edf3; font-weight: 500; }
.hist { display: grid; gap: 3px; align-items: end; height: 60px; margin-top: 1.1rem; }
.hist div { border-radius: 2px 2px 0 0; }
.hist-x { display: flex; justify-content: space-between; font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #7d8a97;
  border-top: 1px solid #2d3640; padding-top: 5px; margin-top: 5px; }
.est .note { font-size: 12px; color: #7d8a97; margin-top: .5rem; }

/* locality banner */
.banner { display: flex; flex-wrap: wrap; background: #12161c; border: 1px solid #232a33; border-radius: 6px; overflow: hidden; margin-bottom: 1rem; }
.banner .txt { flex: 1 1 380px; padding: 1.1rem 1.4rem; display: flex; flex-direction: column; justify-content: space-between; gap: .8rem; }
.banner .k { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #9aa7b4; letter-spacing: .1em; }
.banner .name { font-size: 38px; font-weight: 700; letter-spacing: -0.02em; line-height: 1.1; }
.banner .sub { font-size: 14px; color: #9aa7b4; }
.banner .stats { display: flex; flex-wrap: wrap; gap: 1.4rem; font-family: 'IBM Plex Mono', monospace; }
.banner .stats div div:last-child { font-size: 17px; color: #e6edf3; margin-top: 2px; }
.banner .art { flex: 1 1 420px; min-width: 0; background: #0e1116; border-left: 1px solid #232a33; }

/* floor plan */
.plan-wrap { padding: 2.2rem .3rem 0; }
.dim { display: flex; align-items: center; gap: 8px; color: #f5a524; font-family: 'IBM Plex Mono', monospace; font-size: 12px; font-weight: 600; margin-bottom: 10px; }
.dim i { width: 2px; height: 12px; background: #f5a524; } .dim b { flex: 1 1 auto; height: 1.5px; background: #f5a524; }
.plan { position: relative; height: 270px; border: 3px solid #c9d1d9; box-sizing: border-box; }
.room { position: absolute; box-sizing: border-box; border: 0.75px solid #c9d1d9; display: flex; align-items: center; justify-content: center;
  text-align: center; font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #c9d1d9; padding: 4px; }
.room.bed { background: rgba(245,165,36,0.10); color: #f5a524; font-weight: 600; }
.plan-legend { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-top: .8rem;
  font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #9aa7b4; }
.plan-legend em { font-style: normal; color: #f5a524; }

/* tables, bars, chips, legends, cards */
.mtab { width: 100%; border-collapse: collapse; font-family: 'IBM Plex Mono', monospace; font-size: 13px; }
.mtab th { color: #7d8a97; font-weight: 500; text-align: left; padding: 6px 8px 6px 0; border-bottom: 1px solid #232a33; }
.mtab td { color: #e6edf3; padding: 9px 8px 9px 0; border-bottom: 1px solid #1b2129; }
.mtab .r { text-align: right; white-space: nowrap; } .mtab .up { color: #3fb950; } .mtab .down { color: #ff7b72; } .mtab .dim { color: #9aa7b4; }
.mtab tr.best td { color: #f5a524; } .mtab tr.best td:first-child:before { content: "▶ "; }
.hbars { display: flex; flex-direction: column; gap: 9px; font-family: 'IBM Plex Mono', monospace; font-size: 13px; }
.hbars .row { display: grid; grid-template-columns: 140px minmax(0, 1fr) 76px; align-items: center; gap: 12px; color: #c9d1d9; }
.hbars .row.me { color: #f5a524; }
.hbars .track { height: 10px; background: #1b2129; } .hbars .fill { height: 10px; background: #5b6878; } .hbars .me .fill { background: #f5a524; }
.hbars .v { text-align: right; }
.chip { display: inline-block; padding: 3px 8px; border-radius: 4px; font-family: 'IBM Plex Mono', monospace; font-size: 11px;
  margin: 0 .3rem .35rem 0; border: 1px solid #2d3640; color: #c9d1d9; text-transform: uppercase; }
.chip.blue, .chip.green, .chip.amber { border-color: #f5a524; color: #f5a524; }
.lg { display: flex; flex-wrap: wrap; gap: .35rem 1rem; margin: -.1rem 0 .5rem; }
.lg span { display: inline-flex; align-items: center; gap: .4rem; color: #9aa7b4; font-size: 12px; font-family: 'IBM Plex Mono', monospace; }
.lg i { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
.card-t { color: #e6edf3; font-weight: 700; font-size: 16px; margin: 0 0 .3rem; }
.card-p { color: #9aa7b4; font-size: 14px; margin: .15rem 0; line-height: 1.55; }
.card-p b { color: #e6edf3; }
.insight { border-left: 2px solid #f5a524; padding-left: .8rem; }
.seg { border-radius: 6px; padding: .9rem 1rem; height: 100%; border: 1px solid #232a33; background: #12161c; border-top: 3px solid var(--c); }
.seg h4 { margin: 0 0 .15rem; color: #e6edf3; font-size: 15px; } .seg .who { color: #f5a524; font-size: 12px; font-family: 'IBM Plex Mono', monospace; margin: 0; }
.seg p { color: #9aa7b4; font-size: 13px; margin: .35rem 0 0; } .seg .num { color: #e6edf3; font-family: 'IBM Plex Mono', monospace; }

/* buttons, tabs */
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] { background: #f5a524 !important; border: 0 !important; }
[data-testid="stBaseButton-primaryFormSubmit"] p,
[data-testid="stBaseButton-primary"] p { color: #0b0d10 !important; font-family: 'IBM Plex Mono', monospace !important; font-weight: 600; letter-spacing: .03em; }
div[class*="st-key-card-go"] button { justify-content: flex-start; text-align: left; padding: .55rem .8rem; border-radius: 4px; }
div[class*="st-key-card-go"] button > div { justify-content: flex-start !important; width: 100%; }
div[class*="st-key-card-go"] button p { text-align: left; }
[role="tablist"] { gap: .4rem; border-bottom: 0 !important; box-shadow: none !important; margin-bottom: .5rem; }
[data-testid="stTab"] { background: #12161c; border: 1px solid #232a33; border-radius: 4px; padding: .35rem .9rem !important; height: auto; }
[data-testid="stTab"] p { font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #9aa7b4; }
[data-testid="stTab"][aria-selected="true"] { background: #f5a524; border-color: #f5a524; }
[data-testid="stTab"][aria-selected="true"] p { color: #0b0d10; font-weight: 600; }
.react-aria-SelectionIndicator { display: none !important; }

/* sign-in page */
.signin-hero { padding: .4rem 1rem 0 0; }
.signin-hero .eyebrow { font-family: 'IBM Plex Mono', monospace; font-size: 12px; letter-spacing: .12em; color: #f5a524; }
.signin-hero h1 { font-size: 50px; font-weight: 700; letter-spacing: -0.025em; line-height: 1.05; margin: .5rem 0 .6rem; color: #e6edf3; }
.signin-hero p { font-size: 17px; line-height: 1.55; color: #9aa7b4; max-width: 560px; }
.signin-head { display: flex; align-items: center; gap: 14px; margin-bottom: .4rem; }
.mini-plan { position: relative; width: 74px; height: 54px; border: 2px solid #c9d1d9; box-sizing: border-box; }
.mini-plan div { position: absolute; box-sizing: border-box; }
.signin-note { font-size: 12px; line-height: 1.6; color: #7d8a97; border-top: 1px solid #232a33; padding-top: .9rem; margin-top: .4rem; }
</style>
"""

HIDE_SIDEBAR = """<style>[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"]
{ display: none !important; } .block-container { max-width: 1320px; padding-top: 3rem; }</style>"""


def setup():
    st.markdown(CSS, unsafe_allow_html=True)


def html(text):
    st.markdown(" ".join(line.strip() for line in text.splitlines()), unsafe_allow_html=True)


def crumbs(num, page, extra=""):
    here = f' / <span class="here">{extra}</span>' if extra else ""
    html(f'<div class="crumbs"><div>{num:02d} / {page.upper()}{here}</div><div class="tags">'
         f'<span>54,598 LISTINGS</span><span>MMR · 7 ZONES</span><span class="hot">ASKING PRICES</span></div></div>')


def hero(title, subtitle, eyebrow="Mumbai Metropolitan Region · 54,598 listings"):
    html(f'<div class="hero"><div class="txt"><div class="eyebrow">{eyebrow.upper()}</div><h1>{title}</h1><p>{subtitle}</p></div>'
         f'<div class="art">{art.city(250)}</div></div>')


def tiles(items):
    """items: (label, value, note) tuples."""
    cells = "".join(f'<div class="tile"><div class="l">{i[0]}</div><div class="v">{i[1]}</div><div class="n">{i[2]}</div></div>'
                    for i in items)
    html(f'<div class="tiles">{cells}</div>')


def sec(title, icon="", sub="", num=None):
    """A panel heading in the terminal style: '05 · SAME FLAT ACROSS MUMBAI'. The icon argument is ignored."""
    n = f"<i>{num:02d}</i>" if num is not None else ""
    s = f'<div class="s">{sub}</div>' if sub else ""
    html(f'<div class="sec"><div class="t">{n}{title}</div>{s}</div>')


def legend(items):
    """HTML legend above a chart: items = [(label, colour)]. Keeps the chart full width."""
    html('<div class="lg">' + "".join(f'<span><i style="background:{c}"></i>{t}</span>' for t, c in items) + "</div>")


def glass(title, body, insight=False):
    html(f'<div class="glass"><div class="card-t">{title}</div><div class="{"insight" if insight else ""}">{body}</div></div>')


def card(key):
    """A panel that can hold Streamlit widgets and charts:  with style.card("x"): ..."""
    return st.container(border=True, key=f"card-{key}")
