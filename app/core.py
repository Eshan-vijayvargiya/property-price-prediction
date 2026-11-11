"""Loads the data and models once, and turns a flat description into a price with a range."""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from features import ZONES, make_X, project_key

ROOT = Path(__file__).resolve().parents[1]
STATUS = ["Ready to move", "Under construction"]
AGES = ["New", "Resale", "Not stated"]


@st.cache_data(show_spinner=False)
def listings():
    return pd.read_parquet(ROOT / "data/listings.parquet")


@st.cache_data(show_spinner=False)
def localities():
    return pd.read_parquet(ROOT / "data/localities.parquet")


@st.cache_data(show_spinner=False)
def oof_sample():
    return pd.read_parquet(ROOT / "data/oof_sample.parquet")


@st.cache_data(show_spinner=False)
def js(name):
    folder = "data" if name in ("cleaning_report", "six_city_check") else "models"
    return json.load(open(ROOT / folder / f"{name}.json"))


@st.cache_resource(show_spinner=False)
def models():
    return joblib.load(ROOT / "models/price_models.joblib")


@st.cache_resource(show_spinner=False)
def segmenter():
    return joblib.load(ROOT / "models/segments.joblib")


def zone_of(locality):
    return locality_table().loc[locality, "Zone"]


@st.cache_data(show_spinner=False)
def locality_table():
    return localities().set_index("Locality")


def known_project(locality, project):
    if not project:
        return False
    key = f"{locality} | {project}"
    return key in models()["encoder"].proj_n


def predict(rows, level=0.8):
    """rows: DataFrame with Zone, Locality, Project ('' = new project), BHK, Area, Studio, Status, Age.

    Returns price estimate, low and high (rupees) and which model was used.
    A listed project uses the 'known project' model; anything else the 'new project' model,
    which was trained the way it is used: without the project's own prices.
    """
    m = models()
    rows = rows.copy()
    rows["Project"] = rows["Project"].fillna("")
    enc = m["encoder"]
    X = make_X(rows, enc.transform(rows))
    known = project_key(rows).map(lambda k: k in enc.proj_n).values
    p = np.where(known, m["known"].predict(X), m["new"].predict(X))
    iv = js("intervals")  # one range width per zone and model, from cross-validated errors

    def limit(side):
        k = [iv["Known project"][str(level)]["by_zone"][z][side] for z in rows["Zone"]]
        n = [iv["New project"][str(level)]["by_zone"][z][side] for z in rows["Zone"]]
        return np.where(known, k, n)

    lo, hi = limit("lo"), limit("hi")
    return pd.DataFrame({"price": np.exp(p), "low": np.exp(p + lo), "high": np.exp(p + hi),
                         "model": np.where(known, "Known project", "New project")}, index=rows.index)


def one(zone, locality, project, bhk, area, status, age, studio=0):
    row = pd.DataFrame([{"Zone": zone, "Locality": locality, "Project": project or "", "BHK": bhk, "Area": area,
                         "Studio": studio, "Status": status, "Age": age}])
    return predict(row).iloc[0]


def segment_of(area, ppsf):
    s = segmenter()
    x = s["scaler"].transform(np.array([[np.log(area), np.log(ppsf)]]))
    return s["names"][int(s["kmeans"].predict(x)[0])]


# ---------- money in Indian units ----------
def inr(x, digits=None):
    """1.42e7 -> '₹1.42 Cr'; 8.5e6 -> '₹85 L'."""
    if x is None or pd.isna(x):
        return "–"
    if x >= 1e7:
        v = x / 1e7
        if digits is None:
            digits = 2 if v < 10 else 1 if v < 100 else 0
        return f"₹{v:,.{digits}f} Cr"
    v = x / 1e5
    return f"₹{v:.0f} L" if v >= 10 and digits is None else f"₹{v:.1f} L"


def group_in(n):
    """Indian digit grouping: 1234567 -> '12,34,567'."""
    s = f"{int(round(n))}"
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


def psf(x):
    return f"₹{group_in(x)}/sq ft"


ZONE_LIST = ZONES
