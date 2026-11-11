"""Why this project does NOT use the popular six-city dataset.

"Housing Prices in Metropolitan Areas of India" (Kaggle) is often used for price models.
In every city the file is really two batches: rows with amenities filled in, then rows
where every amenity is 9 ("not mentioned"). In the second batch, area and bedrooms still
agree, but price hardly relates to either - the price column looks misaligned with the
rest of the row. A model trained on it learns noise.

Downloads the CSVs from a public GitHub mirror and writes data/six_city_check.json.
Run from the repo root:  python scripts/check_six_city.py
"""
import io
import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MIRROR = "https://raw.githubusercontent.com/anish2105/House-Price-Prediction/main/{}.csv"
CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Kolkata"]


def load(city):
    local = ROOT / "data/raw/six_city" / f"{city}.csv"
    if local.exists():
        return pd.read_csv(local)
    with urllib.request.urlopen(MIRROR.format(city)) as r:
        return pd.read_csv(io.BytesIO(r.read()))


def main():
    out, sample = {}, []
    for c in CITIES:
        d = load(c).drop_duplicates()
        amen = d.columns[5:]
        d["batch"] = np.where((d[amen] == 9).all(axis=1), "Amenities missing", "Amenities listed")
        out[c] = {}
        for b, x in d.groupby("batch"):
            if len(x) < 100:
                continue
            lp, la, br = np.log(x.Price), np.log(x.Area), x["No. of Bedrooms"]
            out[c][b] = {"rows": int(len(x)),
                         "r_price_area": round(float(np.corrcoef(lp, la)[0, 1]), 2),
                         "r_price_bedrooms": round(float(np.corrcoef(lp, br)[0, 1]), 2),
                         "r_area_bedrooms": round(float(np.corrcoef(la, br)[0, 1]), 2)}
            if c == "Mumbai":
                s = x.sample(min(800, len(x)), random_state=0)
                sample += [{"batch": b, "area": int(a), "price_lakh": round(p / 1e5, 1)} for a, p in zip(s.Area, s.Price)]
    json.dump({"cities": out, "mumbai_sample": sample}, open(ROOT / "data/six_city_check.json", "w"))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
