"""Compare price models under three honest tests. Writes models/eval.json and data/oof.parquet.

Tests (5-fold cross-validation each):
  Known project  - random folds: a new listing in a project already on the market
  New project    - whole projects held out: pricing a launch the model has never seen
  New locality   - whole localities held out: only the zone is known

Run from the repo root:  python scripts/evaluate.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold, KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from features import NUMERIC, LocationEncoder, basic, make_X, out_of_fold_location, project_key  # noqa: E402

LIN_NUM = ["log_area", "Studio", "under_construction", "resale", "age_unknown"]


def linear_model():
    pre = ColumnTransformer([
        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=1), ["Zone", "Locality", "BHK"]),
        ("num", "passthrough", LIN_NUM),
    ])
    return make_pipeline(pre, Ridge(alpha=1.0))


def lin_frame(df):
    return pd.concat([df[["Zone", "Locality"]], df[["BHK"]].astype(str), basic(df)[LIN_NUM]], axis=1)


def gbm():
    """Gradient boosting. Price may only rise with area (monotonic constraint): without it a 1,000 sq ft
    flat could be estimated below a 975 sq ft one in the same place. Costs ~0.2 points of accuracy."""
    up = {"log_area": 1, "log_area_per_bhk": 1}
    return HistGradientBoostingRegressor(max_iter=700, learning_rate=0.05, max_leaf_nodes=48,
                                         min_samples_leaf=20, l2_regularization=1.0,
                                         categorical_features=[NUMERIC.index("zone_id")],
                                         monotonic_cst=[up.get(c, 0) for c in NUMERIC], random_state=0)


def forest():
    return RandomForestRegressor(n_estimators=200, min_samples_leaf=2, max_features=0.5,
                                 n_jobs=-1, random_state=0)


def baseline(train, test):
    """Typical price per sq ft of the locality (else the zone) x area."""
    lp = np.log(train.Price / train.Area)
    loc = lp.groupby(train.Locality).median()
    zone = lp.groupby(train.Zone).median()
    r = test.Locality.map(loc).astype(float).fillna(test.Zone.map(zone).astype(float))
    return r.values + np.log(test.Area.values)


def scores(y, p):
    ape = np.abs(np.exp(p - y) - 1)
    return {"median_error_pct": round(100 * float(np.median(ape)), 1),
            "within_10_pct": round(100 * float((ape <= 0.10).mean()), 1),
            "within_20_pct": round(100 * float((ape <= 0.20).mean()), 1),
            "r2_log": round(float(1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)), 3),
            "rmse_log": round(float(np.sqrt(np.mean((y - p) ** 2))), 4)}


def main():
    d = pd.read_parquet(ROOT / "data/listings.parquet")
    y = np.log(d.Price.values)
    tests = {"Known project": None, "New project": project_key(d), "New locality": d.Locality}
    models = ["Baseline (locality price/sq ft x area)", "Linear regression", "Random forest", "Gradient boosting"]
    res, oof = {}, pd.DataFrame(index=d.index)
    for test, groups in tests.items():
        cv = GroupKFold(5) if groups is not None else KFold(5, shuffle=True, random_state=0)
        pred = {m: np.zeros(len(d)) for m in models}
        fold = np.zeros(len(d), int)
        t0 = time.time()
        for k, (tr, te) in enumerate(cv.split(d, groups=groups)):
            a, b = d.iloc[tr], d.iloc[te]
            fold[te] = k
            pred[models[0]][te] = baseline(a, b)
            lm = linear_model().fit(lin_frame(a), y[tr])
            pred[models[1]][te] = lm.predict(lin_frame(b))
            inner = None if groups is None else groups.iloc[tr]
            Xa = make_X(a, out_of_fold_location(a, groups=inner))
            Xb = make_X(b, LocationEncoder().fit(a).transform(b))
            pred[models[2]][te] = forest().fit(Xa, y[tr]).predict(Xb)
            pred[models[3]][te] = gbm().fit(Xa, y[tr]).predict(Xb)
            print(f"  {test} fold {k + 1}/5 done ({time.time() - t0:.0f}s)", flush=True)
        res[test] = {m: scores(y, pred[m]) for m in models}
        res[test]["_by_zone_gbm"] = {z: scores(y[i], pred[models[3]][i])
                                     for z, i in d.groupby("Zone").indices.items()}
        res[test]["_by_bhk_gbm"] = {str(b): scores(y[i], pred[models[3]][i])
                                    for b, i in d.groupby("BHK").indices.items()}
        oof[f"gbm_{test}"] = pred[models[3]]
        oof[f"lin_{test}"] = pred[models[1]]
        oof[f"fold_{test}"] = fold
        print(test, json.dumps({m: res[test][m] for m in models}, indent=1), flush=True)
    oof["y"] = y
    oof.to_parquet(ROOT / "data/oof.parquet")
    json.dump(res, open(ROOT / "models/eval.json", "w"), indent=1)


if __name__ == "__main__":
    main()
