"""Clean the Mumbai (MMR) listings into data/listings.parquet.

Source: "Mumbai House Prices" by Dravid Vaishnav on Kaggle (listings scraped from Makaan.com).
Every rule is counted in data/cleaning_report.json, so nothing is dropped silently.
Run from the repo root:  python scripts/build_data.py
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from places import tidy, zone  # noqa: E402


def locality(region):
    """'Sector-12 Kamothe' -> 'Kamothe'; 'Dombivali' -> 'Dombivli'."""
    s = tidy(region)
    s = re.sub(r"^Sector\s*\S*\s*", "", s).strip() or "Navi Mumbai"
    s = re.sub(r"\bNew Panvel\b", "Panvel", s)
    s = re.sub(r"^Kasaradavali.*", "Kasarvadavali", s)
    return s


def main():
    raw = pd.read_csv(ROOT / "data/raw/mumbai.csv")
    rep = {"raw_rows": len(raw), "steps": []}

    def step(df, mask, why):
        rep["steps"].append({"rule": why, "removed": int(mask.sum())})
        return df[~mask].copy()

    d = raw.copy()
    d = step(d, d.duplicated(), "Exact duplicate listings (same flat posted again)")
    d = step(d, ~d["type"].isin(["Apartment", "Studio Apartment"]),
             "Villas, independent houses and penthouses (too few, a different market)")
    d = step(d, d.bhk > 5, "More than 5 bedrooms (too few to model)")

    d["Price"] = d.price * np.where(d.price_unit == "Cr", 1e7, 1e5)
    d = step(d, (d.area < 200) | (d.area > 6000), "Area under 200 or over 6,000 sq ft")
    d = step(d, d.area / d.bhk < 150, "Under 150 sq ft per bedroom (area or BHK mistyped)")

    d["ppsf"] = d.Price / d.area
    lo, hi = d.ppsf.quantile([0.005, 0.995])
    d = step(d, (d.ppsf < lo) | (d.ppsf > hi), "Price per sq ft in the extreme 0.5% at either end")

    d["Locality"] = d.region.map(locality)
    lp = np.log(d.ppsf)
    g = d.groupby("Locality").ppsf
    med = g.transform(lambda s: np.log(s).median())
    n = g.transform("size")
    d = step(d, (n >= 5) & ((lp - med).abs() > np.log(3)),
             "Price per sq ft over 3x above or below the locality's typical value")

    d["Zone"] = d.region.map(zone)
    d = step(d, d.Zone == "Other / unclear", "Locality too small or unclear to place in a zone")

    out = pd.DataFrame({
        "Zone": d.Zone, "Locality": d.Locality,
        "Project": d.locality.str.strip().str.replace(r"\s+", " ", regex=True).str.title(),
        "BHK": d.bhk.astype(int), "Area": d.area.astype(int),
        "Studio": (d["type"] == "Studio Apartment").astype(int),
        "Status": d.status.map({"Ready to move": "Ready to move", "Under Construction": "Under construction"}),
        "Age": d.age.map({"New": "New", "Resale": "Resale", "Unknown": "Not stated"}),
        "Price": d.Price, "ppsf": d.ppsf.round(0),
    })
    out["price_lakh"] = out.Price / 1e5
    out = out.sort_values(["Zone", "Locality", "Project", "Price"]).reset_index(drop=True)
    out.to_parquet(ROOT / "data/listings.parquet", index=False)

    rep["clean_rows"] = len(out)
    rep["localities"] = int(out.Locality.nunique())
    rep["projects"] = int(out.Project.nunique())
    rep["by_zone"] = out.Zone.value_counts().to_dict()
    json.dump(rep, open(ROOT / "data/cleaning_report.json", "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
