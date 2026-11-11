"""Builds notebooks/property_price_analysis.ipynb (the analysis as a readable walkthrough) and runs it.

Run from the repo root after build_data.py, evaluate.py and train.py:  python scripts/make_notebook.py
"""
from pathlib import Path

import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parents[1]
cells = []


def md(s):
    cells.append(nbf.v4.new_markdown_cell(s.strip()))


def code(s):
    cells.append(nbf.v4.new_code_cell(s.strip()))


md("""
# Mumbai property prices: prediction, segments and drivers

**Question.** What should a flat in the Mumbai Metropolitan Region cost, what drives the price, and what kinds of
buyers does the market serve? Framed for a developer pricing a new launch.

**Data.** *Mumbai House Prices* (Kaggle, Dravid Vaishnav): 76,038 listings scraped from Makaan.com, with BHK, type,
project, area, price, locality, construction status and new/resale. These are **asking prices**, not registered sales.

This notebook walks through the analysis. The heavy lifting lives in `scripts/` (run `build_data.py`, `evaluate.py`,
`train.py` first); here we load their outputs and look at the results.
""")
code("""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT / "app"))
from features import ZONES, LocationEncoder, project_key

plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "font.size": 10})
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
raw = pd.read_csv(ROOT / "data/raw/mumbai.csv")
d = pd.read_parquet(ROOT / "data/listings.parquet")
raw.head()
""")
md("""
## 1. Cleaning

The biggest problem is duplicates: the same flat posted again. Left in, a flat can be in both the training and test
data, so the model looks better than it is. Every rule is counted.
""")
code("""
rep = json.load(open(ROOT / "data/cleaning_report.json"))
print(f"Raw rows: {rep['raw_rows']:,}   exact duplicates: {raw.duplicated().sum():,} ({raw.duplicated().mean():.0%})")
pd.DataFrame(rep["steps"]).set_index("rule")
""")
code("""
print(f"Clean listings: {len(d):,} · localities: {d.Locality.nunique()} · projects: {d.Project.nunique():,}")
d.groupby("Zone").agg(listings=("Price", "size"), median_price_lakh=("price_lakh", "median"),
                      median_ppsf=("ppsf", "median"), median_area=("Area", "median")).reindex(ZONES).round(0)
""")
md("""
Localities are grouped into **7 zones** with whole-word keyword rules (`app/places.py`), after tidying spellings
("Dombivali" → "Dombivli", "Sector-12 Kamothe" → "Kamothe"). Whole words matter: a plain substring match would put
*Kharghar* under *Khar*.
""")
code("""
z = d.groupby("Zone").ppsf.median().reindex(ZONES).sort_values()
ax = z.plot.barh(color=BLUE, figsize=(7, 3.2))
ax.set_xlabel("Median asking price per sq ft (₹)"); ax.set_ylabel("")
ax.set_title(f"Location matters: {z.max() / z.min():.1f}x between the dearest and cheapest zone")
for i, v in enumerate(z): ax.text(v + 300, i, f"₹{v:,.0f}", va="center", fontsize=9)
plt.tight_layout()
""")
md("""
## 2. The dataset I rejected first

The popular *Housing Prices in Metropolitan Areas of India* data looked like a good fit, but in every city it is two
batches. In the batch where amenities are all coded 9 ("not mentioned"), **area and bedrooms still agree, but price
barely relates to either**. The price column seems misaligned with the rest of the row, for about 70% of the data.
(`scripts/check_six_city.py`)
""")
code("""
six = json.load(open(ROOT / "data/six_city_check.json"))
pd.DataFrame([{"city": c, "batch": b, **m} for c, v in six["cities"].items() for b, m in v.items()]).set_index(["city", "batch"])
""")
code("""
s = pd.DataFrame(six["mumbai_sample"])
fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
for ax, (b, g), c in zip(axes, s.groupby("batch"), [BLUE, ORANGE]):
    ax.scatter(g.area, g.price_lakh, s=6, alpha=0.5, color=c); ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_title(f"Mumbai: {b.lower()}"); ax.set_xlabel("Area (sq ft)")
axes[0].set_ylabel("Price (lakh)"); plt.tight_layout()
""")
md("""
## 3. Features: borrowing strength for small projects

175 localities and ~9,500 projects, half of them with 1-2 listings. Each level gets a *typical log price per sq ft*,
**shrunk towards the level above** when it has few listings (an m-estimate):

    project value = (sum of its listings + 5 x locality value) / (its listings + 5)

and the same for locality → zone (weight 10) and zone → Mumbai (weight 20). Training rows get these values
**out of fold**, so a listing never sees its own price.
""")
code("""
enc = LocationEncoder().fit(d)
ex = d.assign(key=project_key(d)).groupby("key").size().sort_values()
for k in [ex.index[0], ex.index[len(ex) // 2], ex.index[-1]]:
    loc = k.split(" | ")[0]
    print(f"{k[:55]:55s} listings={enc.proj_n[k]:3d}  project={np.exp(enc.proj[k]):8,.0f}  locality={np.exp(enc.loc[loc]):8,.0f}  ₹/sq ft")
""")
md("""
## 4. Models under three honest tests

A random split flatters the model, because flats from one project land on both sides. So every model is tested three
ways (5-fold cross-validation each):

* **Known project**: random folds. A new listing in a project already on the market.
* **New project**: whole projects held out. Pricing a launch the model has never seen. *The developer's case.*
* **New locality**: whole localities held out. Only the zone is known.
""")
code("""
ev = json.load(open(ROOT / "models/eval.json"))
tab = pd.DataFrame({t: {m: v["median_error_pct"] for m, v in r.items() if not m.startswith("_")} for t, r in ev.items()})
tab.columns = [f"{c}: median % error" for c in tab.columns]
tab
""")
code("""
pd.DataFrame({t: {m: v["within_20_pct"] for m, v in r.items() if not m.startswith("_")} for t, r in ev.items()}).add_suffix(": % within ±20%")
""")
md("""
**Reading it.**
* Knowing the project nearly halves the error against the simple locality rule.
* For a brand-new project the best model is about ±12%: location and size explain most of the price; builder,
  floor, view and amenities (not in the data) explain the rest.
* For a new locality every model struggles (25%+), and the plain linear model is close to the best tree: with only the
  zone to go on, there is little for a complex model to add.
* Deployed model: gradient boosting with a monotonic constraint (price only rises with area). The random forest was a
  little better on known projects, but its file is ~98 MB against ~2 MB.
""")
code("""
o = pd.read_parquet(ROOT / "data/oof_sample.parquet")
fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
for ax, col, t in zip(axes, ["known_lakh", "new_lakh"], ["Known project", "New project"]):
    ax.scatter(o.actual_lakh, o[col], s=4, alpha=0.35, color=BLUE)
    ax.plot([15, 2500], [15, 2500], color=ORANGE, lw=1, ls="--")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_title(t); ax.set_xlabel("Actual (lakh)")
axes[0].set_ylabel("Predicted (lakh)"); plt.tight_layout()
""")
md("""
### Price ranges that actually hold

Each estimate comes with an 80% range taken from the model's own cross-validated errors (limits set on 4 folds,
checked on the 5th). One width for all of Mumbai covered 80% overall but not in each zone, so each zone gets its own.
""")
code("""
iv = json.load(open(ROOT / "models/intervals.json"))
n8 = iv["New project"]["0.8"]
pd.DataFrame({"one width": n8["coverage_by_zone_one_width"], "per zone": n8["coverage_by_zone"],
              "range low %": {z: round(100 * (np.exp(v["lo"]) - 1)) for z, v in n8["by_zone"].items()},
              "range high %": {z: round(100 * (np.exp(v["hi"]) - 1)) for z, v in n8["by_zone"].items()}})
""")
md("""
## 5. Price drivers

A linear model on log price with a fixed effect for each locality, so every effect compares flats **in the same
locality**. Standard errors are clustered by project (flats in one project are not independent).
""")
code("""
dr = json.load(open(ROOT / "models/drivers.json"))
print("R² (log price):", dr["r2_log"])
pd.DataFrame(dr["effects"]).T
""")
md("""
* **Bedrooms carry size information the area figure misses.** At the same stated area a 3 BHK lists ~33% above a 2 BHK.
  Listings mix *carpet* area and *built-up / super built-up* area (often 20-40% bigger), so the bedroom count is the
  cleaner size signal.
* **No discount for waiting.** Under-construction flats list about the same as ready ones (+1.8%); resale flats ~4%
  below new.
""")
code("""
pd.DataFrame(dr["under_construction_by_zone"]).T
""")
code("""
imp = json.load(open(ROOT / "models/importance.json"))
pd.DataFrame({t: r["increase_pct_points"] for t, r in imp.items()}).rename_axis("feature group (shuffled together)")
""")
md("""
## 6. Buyer segments (K-Means)

Two features every buyer trades off: **log area** (how big) and **log price per sq ft** (how premium the location),
standardised. The silhouette score is flat from k = 3 to 7: the market is a continuous spread, not separate islands.
k = 5 gives segments a marketing team can name; five other random starts reproduce them.
""")
code("""
import joblib
seg = joblib.load(ROOT / "models/segments.joblib")
print("silhouette by k:", {c["k"]: c["silhouette"] for c in seg["curve"]})
print("stability (adjusted Rand index vs 5 other seeds):", seg["stability_ari"])
d.groupby("Segment").agg(share=("Price", lambda x: f"{len(x) / len(d):.0%}"), median_price_lakh=("price_lakh", "median"),
                         median_area=("Area", "median"), median_ppsf=("ppsf", "median"),
                         typical_bhk=("BHK", lambda x: x.mode()[0])).sort_values("median_price_lakh")
""")
code("""
m = d.sample(4000, random_state=1)
fig, ax = plt.subplots(figsize=(7, 4.6))
cols = {"Budget starter homes": AQUA, "Spacious value homes": "#eda100", "Compact city homes": BLUE,
        "Premium family homes": "#6250d6", "Large luxury homes": "#e87ba4"}
for n, g in m.groupby("Segment"):
    ax.scatter(g.Area, g.ppsf, s=5, alpha=0.5, color=cols[n], label=n)
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("Area (sq ft)"); ax.set_ylabel("₹ per sq ft")
ax.legend(markerscale=3, fontsize=8, frameon=False); ax.set_title("Same budget, different homes: location or space")
plt.tight_layout()
""")
md("""
**The key trade-off.** *Compact city homes* (~550 sq ft in the western and central suburbs) and *Spacious value homes*
(~1,090 sq ft in Navi Mumbai, Mira Road and Thane's edges) cost about the same, ₹0.9-1 crore. Buyers at that budget
choose between location and space; a developer chooses which of them to build for.

## 7. Limits

* Asking prices, not sale prices; no dates, so no trends.
* Carpet and built-up area are mixed.
* No floor, view, amenities, parking or builder: most of the remaining error, especially in South Mumbai and Thane.
* The segments describe homes; the buyer labels are an interpretation.
""")

nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3"}})
out = ROOT / "notebooks/property_price_analysis.ipynb"
ExecutePreprocessor(timeout=600, kernel_name="python3").preprocess(nb, {"metadata": {"path": str(ROOT / "notebooks")}})
nbf.write(nb, out)
print("wrote", out)
