"""Fit the final models and the analysis the app shows.

Needs data/listings.parquet (build_data.py) and data/oof.parquet + models/eval.json (evaluate.py).
Writes:
  models/price_models.joblib  location encoder + 2 gradient-boosting models (known / new project)
  models/intervals.json       price ranges from cross-validated errors, with their real coverage
  models/drivers.json         % effects from the linear model (cluster-robust standard errors)
  models/importance.json      grouped permutation importance
  models/segments.joblib      scaler + K-Means
  data/localities.parquet     locality price index
  data/listings.parquet       + Segment column
Run from the repo root:  python scripts/train.py
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.model_selection import GroupKFold, KFold
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate import gbm  # noqa: E402
from features import (GROUPS, NUMERIC, ZONES, LocationEncoder, basic, make_X,  # noqa: E402
                      out_of_fold_location, project_key)

STANDARD = {"BHK": 2, "Area": 950, "Studio": 0, "Status": "Ready to move", "Age": "New"}


# ---------- 1. final price models ----------
def fit_price_models(d, y):
    enc = LocationEncoder().fit(d)
    known = gbm().fit(make_X(d, out_of_fold_location(d)), y)
    new = gbm().fit(make_X(d, out_of_fold_location(d, groups=project_key(d))), y)
    joblib.dump({"encoder": enc, "known": known, "new": new, "features": NUMERIC}, ROOT / "models/price_models.joblib",
                compress=3)
    print("price models saved")


# ---------- 2. price ranges ----------
def intervals(d, oof):
    """80% / 90% ranges from cross-validated errors (log scale), one width per zone.

    One width for all of Mumbai covered 80% overall but only ~65% in South Mumbai and ~90% in
    Mira Road, so each zone gets its own limits. Coverage is checked cross-conformally:
    limits from 4 folds, coverage measured on the 5th.
    """
    zone = d.Zone.values
    out = {}
    for test in ["Known project", "New project"]:
        r = (oof["y"] - oof[f"gbm_{test}"]).values
        fold = oof[f"fold_{test}"].values
        res = {}
        for level in [0.8, 0.9]:
            a = (1 - level) / 2
            hit_global, hit_zone = np.zeros(len(r), bool), np.zeros(len(r), bool)
            for k in range(5):
                tr, te = fold != k, fold == k
                lo, hi = np.quantile(r[tr], [a, 1 - a])
                hit_global[te] = (r[te] >= lo) & (r[te] <= hi)
                for z in ZONES:
                    zt, ze = tr & (zone == z), te & (zone == z)
                    lo, hi = np.quantile(r[zt], [a, 1 - a])
                    hit_zone[ze] = (r[ze] >= lo) & (r[ze] <= hi)
            res[str(level)] = {
                "lo": float(np.quantile(r, a)), "hi": float(np.quantile(r, 1 - a)),
                "by_zone": {z: {"lo": float(np.quantile(r[zone == z], a)), "hi": float(np.quantile(r[zone == z], 1 - a))}
                            for z in ZONES},
                "coverage_pct": round(100 * float(hit_zone.mean()), 1),
                "coverage_one_width_pct": round(100 * float(hit_global.mean()), 1),
                "coverage_by_zone": {z: round(100 * float(hit_zone[zone == z].mean()), 1) for z in ZONES},
                "coverage_by_zone_one_width": {z: round(100 * float(hit_global[zone == z].mean()), 1) for z in ZONES},
            }
        out[test] = res
    json.dump(out, open(ROOT / "models/intervals.json", "w"), indent=1)
    for t, v in out.items():
        print("intervals", t, v["0.8"]["coverage_pct"], v["0.8"]["coverage_by_zone"], v["0.8"]["coverage_by_zone_one_width"])


# ---------- 3. price drivers: linear model with locality fixed effects ----------
def design(d):
    b = basic(d)
    X = pd.DataFrame({"const": 1.0, "log_area": b.log_area, "Studio": b.Studio,
                      "under_construction": b.under_construction, "resale": b.resale, "age_unknown": b.age_unknown},
                     index=d.index)
    for k in [1, 3, 4, 5]:
        X[f"bhk_{k}"] = (d.BHK == k).astype(float)  # vs 2 BHK
    base_loc = d.Locality.value_counts().index[0]  # the biggest locality is the reference
    locs = [loc for loc in sorted(d.Locality.unique()) if loc != base_loc]
    dummies = pd.DataFrame({f"loc={loc}": (d.Locality == loc).astype(float) for loc in locs}, index=d.index)
    return pd.concat([X, dummies], axis=1), base_loc


def ols_cluster(X, y, groups):
    """OLS with standard errors clustered by project (flats in one project aren't independent)."""
    Xv = X.values
    XtX_inv = np.linalg.pinv(Xv.T @ Xv)
    beta = XtX_inv @ Xv.T @ y
    u = y - Xv @ beta
    s = pd.DataFrame(Xv * u[:, None]).groupby(groups.values).sum().values
    G, n, p = s.shape[0], len(y), Xv.shape[1]
    V = XtX_inv @ (s.T @ s) @ XtX_inv * (G / (G - 1)) * ((n - 1) / (n - p))
    return pd.Series(beta, X.columns), pd.Series(np.sqrt(np.diag(V)), X.columns), u


def drivers(d, y):
    X, base_loc = design(d)
    beta, se, u = ols_cluster(X, y, project_key(d))
    r2 = 1 - (u ** 2).sum() / ((y - y.mean()) ** 2).sum()

    def pct(name, scale=1.0):
        b, s = beta[name] * scale, se[name] * scale
        return {"effect_pct": round(100 * (np.exp(b) - 1), 1),
                "low_pct": round(100 * (np.exp(b - 1.96 * s) - 1), 1),
                "high_pct": round(100 * (np.exp(b + 1.96 * s) - 1), 1)}

    eff = {
        "10% more area (same BHK, locality)": pct("log_area", np.log(1.1)),
        "Under construction (vs ready to move)": pct("under_construction"),
        "Resale (vs new)": pct("resale"),
        "Studio (vs 1 BHK flat)": pct("Studio"),
        "1 BHK (vs 2 BHK, same area)": pct("bhk_1"),
        "3 BHK (vs 2 BHK, same area)": pct("bhk_3"),
        "4 BHK (vs 2 BHK, same area)": pct("bhk_4"),
    }
    # does the under-construction discount differ by zone? one regression per zone, same controls
    uc_zone = {}
    for z, i in d.groupby("Zone").indices.items():
        dz = d.iloc[i]
        if (dz.Status == "Under construction").mean() < 0.05:
            continue
        Xz, _ = design(dz)
        Xz = Xz.loc[:, Xz.std() > 0].assign(const=1.0)
        bz, sz, _ = ols_cluster(Xz, y[i], project_key(dz))
        uc_zone[z] = {"effect_pct": round(100 * (np.exp(bz["under_construction"]) - 1), 1),
                      "low_pct": round(100 * (np.exp(bz["under_construction"] - 1.96 * sz["under_construction"]) - 1), 1),
                      "high_pct": round(100 * (np.exp(bz["under_construction"] + 1.96 * sz["under_construction"]) - 1), 1),
                      "n": int(len(i))}
    json.dump({"r2_log": round(float(r2), 3), "n": int(len(y)), "projects": int(project_key(d).nunique()),
               "effects": eff, "under_construction_by_zone": uc_zone, "reference_locality": base_loc},
              open(ROOT / "models/drivers.json", "w"), indent=1)
    print("drivers r2", round(r2, 3), json.dumps(eff), json.dumps(uc_zone))
    return beta, base_loc


def locality_index(d, beta, base_loc):
    """Price of the same standard flat (2 BHK, 950 sq ft, ready, new) in every locality."""
    std = (beta["const"] + beta["log_area"] * np.log(STANDARD["Area"]))
    g = d.groupby("Locality")
    t = pd.DataFrame({
        "Zone": g.Zone.agg(lambda s: s.mode()[0]), "listings": g.size(), "projects": g.Project.nunique(),
        "median_ppsf": g.ppsf.median(), "median_price_lakh": g.price_lakh.median(), "median_area": g.Area.median(),
        "under_construction_pct": g.Status.agg(lambda s: 100 * (s == "Under construction").mean()),
        "share_1bhk": g.BHK.agg(lambda s: 100 * (s == 1).mean()), "share_2bhk": g.BHK.agg(lambda s: 100 * (s == 2).mean()),
        "share_3bhk_plus": g.BHK.agg(lambda s: 100 * (s >= 3).mean()),
    })
    t["standard_flat_lakh"] = [np.exp(std + beta.get(f"loc={loc}", 0.0)) / 1e5 for loc in t.index]
    t = t.reset_index().sort_values("standard_flat_lakh", ascending=False)
    t.round(1).to_parquet(ROOT / "data/localities.parquet", index=False)
    print(t.head(8)[["Locality", "Zone", "listings", "standard_flat_lakh", "median_ppsf"]].round(0).to_string())


# ---------- 4. grouped permutation importance ----------
def importance(d, y):
    out = {}
    for test, groups in [("Known project", None), ("New project", project_key(d))]:
        cv = GroupKFold(5) if groups is not None else KFold(5, shuffle=True, random_state=0)
        tr, te = next(iter(cv.split(d, groups=groups)))
        a, b = d.iloc[tr], d.iloc[te]
        inner = None if groups is None else groups.iloc[tr]
        m = gbm().fit(make_X(a, out_of_fold_location(a, groups=inner)), y[tr])
        Xb = make_X(b, LocationEncoder().fit(a).transform(b))
        base = np.median(np.abs(np.exp(m.predict(Xb) - y[te]) - 1))
        rng = np.random.RandomState(0)
        res = {}
        for name, cols in GROUPS.items():
            vals = []
            for _ in range(5):
                Xp = Xb.copy()
                idx = rng.permutation(len(Xp))
                Xp[cols] = Xb[cols].values[idx]  # shuffle the group's columns together
                vals.append(np.median(np.abs(np.exp(m.predict(Xp) - y[te]) - 1)) - base)
            res[name] = round(100 * float(np.mean(vals)), 1)
        out[test] = {"base_error_pct": round(100 * float(base), 1), "increase_pct_points": res}
    json.dump(out, open(ROOT / "models/importance.json", "w"), indent=1)
    print("importance", out)


# ---------- 5. K-Means segments ----------
NAMES = {
    "budget": "Budget starter homes", "compact": "Compact city homes", "value": "Spacious value homes",
    "premium": "Premium family homes", "luxury": "Large luxury homes",
}


def segments(d):
    F = np.column_stack([np.log(d.Area), np.log(d.ppsf)])
    sc = StandardScaler().fit(F)
    X = sc.transform(F)
    rng = np.random.RandomState(0).choice(len(X), 10000, replace=False)
    curve = []
    for k in range(2, 9):
        km_k = KMeans(k, n_init=10, random_state=0).fit(X)
        curve.append({"k": k, "silhouette": round(float(silhouette_score(X[rng], km_k.labels_[rng])), 3),
                      "inertia_per_row": round(float(km_k.inertia_ / len(X)), 3)})
    km = KMeans(5, n_init=10, random_state=0).fit(X)
    cent = pd.DataFrame(np.exp(sc.inverse_transform(km.cluster_centers_)), columns=["area", "ppsf"])
    names = {}
    lux = int(cent.area.idxmax())
    names[lux] = NAMES["luxury"]
    rest = cent.drop(lux)
    hi = rest.ppsf >= rest.ppsf.median()
    for grp, small, big in [(rest[hi], "compact", "premium"), (rest[~hi], "budget", "value")]:
        names[int(grp.area.idxmin())] = NAMES[small]
        names[int(grp.area.idxmax())] = NAMES[big]
    assert len(names) == 5, names
    # stability: do other random starts find the same segments?
    stability = [round(float(adjusted_rand_score(km.labels_, KMeans(5, n_init=10, random_state=s).fit(X).labels_)), 3)
                 for s in (1, 2, 3, 4, 5)]
    joblib.dump({"scaler": sc, "kmeans": km, "names": names, "curve": curve, "stability_ari": stability},
                ROOT / "models/segments.joblib")
    d["Segment"] = [names[i] for i in km.labels_]
    print("segments", curve, d.groupby("Segment").agg(n=("Price", "size"), lakh=("price_lakh", "median"),
                                                     area=("Area", "median"), ppsf=("ppsf", "median")).round(0))
    return d


def main():
    d = pd.read_parquet(ROOT / "data/listings.parquet").drop(columns=["Segment"], errors="ignore")
    y = np.log(d.Price.values)
    oof = pd.read_parquet(ROOT / "data/oof.parquet")
    beta, base_loc = drivers(d, y)
    locality_index(d, beta, base_loc)
    intervals(d, oof)
    s = oof.sample(4000, random_state=0)
    pd.DataFrame({"actual_lakh": np.exp(s.y) / 1e5, "known_lakh": np.exp(s["gbm_Known project"]) / 1e5,
                  "new_lakh": np.exp(s["gbm_New project"]) / 1e5, "Zone": d.Zone.loc[s.index].values,
                  "BHK": d.BHK.loc[s.index].values}).round(2).to_parquet(ROOT / "data/oof_sample.parquet", index=False)
    importance(d, y)
    d = segments(d)
    d.to_parquet(ROOT / "data/listings.parquet", index=False)
    fit_price_models(d, y)


if __name__ == "__main__":
    main()
