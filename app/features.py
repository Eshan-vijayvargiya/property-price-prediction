"""Turn a listing into model features. Shared by training and the app.

The tricky part is location. There are 175 localities and ~9,500 projects, many with
only one or two listings. Each level gets a "typical log price per sq ft", shrunk
towards the level above when it has few listings:

    project  -> shrunk towards its locality
    locality -> shrunk towards its zone
    zone     -> shrunk towards the whole region

so a project with 1 listing mostly borrows its locality's value, and a project with
100 listings mostly speaks for itself (an m-estimate / empirical-Bayes style average).
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, KFold

ZONES = ["South Mumbai", "Western Suburbs", "Central Suburbs", "Thane", "Navi Mumbai & Panvel",
         "Mira Road & Vasai-Virar", "Kalyan-Dombivli & beyond"]
SHRINK = {"zone": 20, "loc": 10, "proj": 5}  # how many listings count as "half trusted"

NUMERIC = ["log_area", "log_area_per_bhk", "BHK", "Studio", "under_construction", "resale", "age_unknown",
           "zone_id", "te_zone", "te_loc", "te_proj", "log_n_loc", "log_n_proj"]
GROUPS = {  # for grouped permutation importance
    "Location (zone, locality)": ["zone_id", "te_zone", "te_loc", "log_n_loc"],
    "Project": ["te_proj", "log_n_proj"],
    "Size (area, BHK)": ["log_area", "log_area_per_bhk", "BHK", "Studio"],
    "Construction status": ["under_construction"],
    "New or resale": ["resale", "age_unknown"],
}


def project_key(df):
    return df["Locality"].astype(str) + " | " + df["Project"].fillna("").astype(str)


class LocationEncoder:
    """Shrunk average log price per sq ft for zone, locality and project."""

    def fit(self, df):
        y = np.log(df["Price"] / df["Area"])
        self.prior = float(y.mean())
        t = pd.DataFrame({"zone": df["Zone"].values, "loc": df["Locality"].values,
                          "proj": project_key(df).values, "y": y.values})
        z = t.groupby("zone").y.agg(["sum", "count"])
        self.zone = ((z["sum"] + SHRINK["zone"] * self.prior) / (z["count"] + SHRINK["zone"])).to_dict()
        l = t.groupby(["loc", "zone"]).y.agg(["sum", "count"]).reset_index()
        lp = l.zone.map(self.zone).fillna(self.prior)
        l["te"] = (l["sum"] + SHRINK["loc"] * lp) / (l["count"] + SHRINK["loc"])
        self.loc = dict(zip(l["loc"], l["te"]))
        self.loc_n = dict(zip(l["loc"], l["count"]))
        p = t.groupby(["proj", "loc"]).y.agg(["sum", "count"]).reset_index()
        pp = p["loc"].map(self.loc)
        p["te"] = (p["sum"] + SHRINK["proj"] * pp) / (p["count"] + SHRINK["proj"])
        self.proj = dict(zip(p["proj"], p["te"]))
        self.proj_n = dict(zip(p["proj"], p["count"]))
        return self

    def transform(self, df):
        zone = df["Zone"].map(self.zone).fillna(self.prior).astype(float)
        loc = df["Locality"].map(self.loc).astype(float).fillna(zone)
        key = project_key(df)
        proj = key.map(self.proj).astype(float).fillna(loc)
        return pd.DataFrame({
            "te_zone": zone.values, "te_loc": loc.values, "te_proj": proj.values,
            "log_n_loc": np.log1p(df["Locality"].map(self.loc_n).fillna(0).astype(float)).values,
            "log_n_proj": np.log1p(key.map(self.proj_n).fillna(0).astype(float)).values,
        }, index=df.index)


def out_of_fold_location(df, groups=None, k=5, seed=0):
    """Location features for training rows, each computed without its own fold.

    Without this the model would see each listing's own price inside te_proj
    (target leakage) and learn to trust it far too much. With `groups`, whole
    projects are held out together, to mimic pricing a project never seen before.
    """
    out = pd.DataFrame(index=df.index, columns=["te_zone", "te_loc", "te_proj", "log_n_loc", "log_n_proj"],
                       dtype=float)
    cv = GroupKFold(k) if groups is not None else KFold(k, shuffle=True, random_state=seed)
    for tr, te in cv.split(df, groups=groups):
        enc = LocationEncoder().fit(df.iloc[tr])
        out.iloc[te] = enc.transform(df.iloc[te]).values
    return out


def basic(df):
    """Features that don't depend on other listings."""
    bhk = df["BHK"].astype(float)
    return pd.DataFrame({
        "log_area": np.log(df["Area"].astype(float)),
        "log_area_per_bhk": np.log(df["Area"].astype(float) / bhk),
        "BHK": bhk,
        "Studio": df["Studio"].astype(float),
        "under_construction": (df["Status"] == "Under construction").astype(float),
        "resale": (df["Age"] == "Resale").astype(float),
        "age_unknown": (df["Age"] == "Not stated").astype(float),
        "zone_id": df["Zone"].map({z: i for i, z in enumerate(ZONES)}).astype(float),
    }, index=df.index)


def make_X(df, loc_feats):
    return pd.concat([basic(df), loc_feats], axis=1)[NUMERIC]
