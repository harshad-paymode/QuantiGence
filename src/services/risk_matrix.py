from src.core.logger import configure_logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import math
from scipy.stats import rankdata

logger = configure_logging()

# small helper
def _percentile_rank(value: float, arr: np.ndarray) -> float:
    """
    Percentile rank of `value` within `arr` in [0,1].
    Ties are treated by giving the midpoint fraction for equal values:
      (count_less + 0.5*count_equal) / n
    """
    arr = np.asarray(arr)
    if arr.size == 0:
        return float("nan")
    # ignore NaNs in arr
    arr = arr[~np.isnan(arr)]
    if arr.size == 0:
        return float("nan")
    less = np.sum(arr < value)
    equal = np.sum(arr == value)
    return float((less + 0.5 * equal) / arr.size)

def convert_to_risk_score(category_score: dict) -> dict:
    risk_score_dict = {}
    for key, val in category_score.items():
        risk_score_dict[key] = (100 - val)
    return risk_score_dict

def calculate_category_scores(
    metrics: pd.Series,
    ratio_groups: Dict[str, List[str]],
    peers_df: Optional[pd.DataFrame] = None,
    direction_map: Optional[Dict[str, bool]] = None,
    winsor_pct: float = 0.01,
    normalize_method: str = "percentile",  # 'percentile' (preferred) or 'minmax' or 'zscore'
    min_metrics_per_category: int = 1,
    output_scale: int = 100,
) -> Dict[str, Any]:
    """
    Calculate category scores (0..output_scale) for a single company-period vector.

    Required inputs:
      - metrics: pd.Series indexed by exact metric names -> numeric values or NaN
      - ratio_groups: dict category -> list of metric names

    Optional:
      - peers_df: DataFrame indexed by metric names, columns = peer entities (companies / periods).
                  If provided, normalization & winsorization operate across peers (preferred).
      - direction_map: optional dict metric -> bool (True if higher-is-good). If not provided,
                       heuristics will be used.
      - winsor_pct: fraction to winsorize tails (0.01 => 1% tails)
      - normalize_method: 'percentile'|'minmax'|'zscore'
      - min_metrics_per_category: categories with fewer valid metrics will return NaN
      - output_scale: final 0..output_scale (default 100)

    Returns:
      {
        "category_scores": {category: score_or_nan, ...},
        "per_metric": pd.DataFrame with columns ['raw','transformed','normalized','direction_is_good'],
        "metadata": {...}
      }
    """

    # -------------- input checks & prep ----------------
    metrics = metrics.copy()
    metrics.index = metrics.index.astype(str)
    metrics = pd.to_numeric(metrics, errors="coerce")

    # direction heuristics (expandable)
    def heuristic_higher_is_good(name: str) -> bool:
        ln = name.lower()
        # valuation metrics (price-to, p/e, ev-to) usually higher -> more expensive (worse)
        if any(k in ln for k in ("price-to", "p/e", "p/b", "ev-to", "price to")):
            return False
        # typically good if contains these
        if any(k in ln for k in ("margin", "return", "roe", "roa", "profit", "income", "yield", "growth", "efficiency")):
            return True
        # typically bad if contains these
        if any(k in ln for k in ("debt", "leverage", "capex", "expense", "cost", "volatility", "tracking", "ulcer", "loss", "short")):
            return False
        # if name suggests 'per share' treat as positive generally
        if "per share" in ln or "per-share" in ln:
            return True
        # fallback: assume higher is better (we will also normalize sign later)
        return True

    # keywords to treat as absolute-dollar magnitudes
    ABS_KEYWORDS = ("tangible", "working capital", "cash", "total assets", "book value", "market cap", "enterprise value", "value")

    # --------------- transform metrics -----------------
    transformed = {}
    transform_notes = {}
    for name, raw in metrics.items():
        if pd.isna(raw):
            transform_notes[name] = {"raw": raw, "reason": "nan"}
            continue
        val = float(raw)
        ln = name.lower()

        # detect dollar-like absolute metrics: keyword OR large magnitude
        is_abs = (abs(val) >= 1e6) or any(k in ln for k in ABS_KEYWORDS)
        if is_abs:
            # compress magnitude while preserving sign: use log10(1+abs)
            t = np.sign(val) * np.log10(abs(val) + 1.0)
            transform_notes[name] = {"raw": val, "is_abs": True, "transform": "sign*log10(1+abs)"}
        else:
            t = float(val)
            transform_notes[name] = {"raw": val, "is_abs": False, "transform": "linear"}

        # directionality: use map override if provided else heuristic
        if direction_map and name in direction_map:
            higher_good = bool(direction_map[name])
        else:
            higher_good = heuristic_higher_is_good(name)

        transform_notes[name]["higher_is_good"] = higher_good
        # keep "positive = good" convention by flipping when higher_is_good is False
        adj = float(t if higher_good else -t)
        transformed[name] = adj

    if len(transformed) == 0:
        logger.info("No valid metrics found in input vector.")
        # return empty diagnostics
        per_metric_df = pd.DataFrame.from_dict(transform_notes, orient="index")
        return {"category_scores": {c: np.nan for c in ratio_groups.keys()}, "per_metric": per_metric_df, "metadata": {"used_peers": peers_df is not None}}

    # -------------- prepare peer arrays (if provided) --------------
    # peers_df expected indexed by metric names. We'll coerce numeric.
    peers_available = False
    peers_numeric = {}
    if peers_df is not None:
        try:
            # ensure index are strings
            peers = peers_df.copy()
            peers.index = peers.index.astype(str)
            # extract arrays for metrics we care about
            for m in transformed.keys():
                if m in peers.index:
                    arr = pd.to_numeric(peers.loc[m].values, errors="coerce")
                    # transform arr same way we transformed the single vector entry:
                    arr_clean = []
                    for v in arr:
                        if pd.isna(v):
                            continue
                        vv = float(v)
                        is_abs = (abs(vv) >= 1e6) or any(k in m.lower() for k in ABS_KEYWORDS)
                        if is_abs:
                            tv = np.sign(vv) * np.log10(abs(vv) + 1.0)
                        else:
                            tv = float(vv)
                        # incorporate directionality: flip if higher_is_good is False
                        if direction_map and m in direction_map:
                            higher_good = bool(direction_map[m])
                        else:
                            higher_good = heuristic_higher_is_good(m)
                        tv = float(tv if higher_good else -tv)
                        arr_clean.append(tv)
                    if len(arr_clean) > 0:
                        peers_numeric[m] = np.array(arr_clean, dtype=float)
                        peers_available = True
        except Exception:
            logger.exception("peers_df parsing failed; falling back to no-peers mode.")
            peers_available = False

    # -------------- winsorize & normalize per metric --------------
    per_metric = []
    for name, adj in transformed.items():
        arr_for_metric = None
        # if peers available for this metric use that array for winsorize & percentile
        if peers_available and name in peers_numeric:
            arr_for_metric = peers_numeric[name]
            # compute winsor bounds from peers
            low = np.nanpercentile(arr_for_metric, 100.0 * winsor_pct)
            high = np.nanpercentile(arr_for_metric, 100.0 * (1.0 - winsor_pct))
            val_w = np.clip(adj, low, high)
        else:
            # fallback: use single-value -> no winsorization possible; just use adj
            val_w = adj

        # Normalization
        if normalize_method == "percentile":
            if peers_available and name in peers_numeric:
                # percentile rank of val_w within peers array
                norm = _percentile_rank(val_w, peers_numeric[name])
            else:
                # fallback: min-max across all transformed values for the category will be done later.
                # For now store raw adjusted value; we will min-max per category below.
                norm = val_w  # sentinel
        elif normalize_method == "zscore":
            if peers_available and name in peers_numeric:
                mu = float(np.nanmean(peers_numeric[name]))
                sd = float(np.nanstd(peers_numeric[name], ddof=0))
                norm = 0.0 if sd == 0 else (val_w - mu) / sd
            else:
                norm = val_w
        elif normalize_method == "minmax":
            if peers_available and name in peers_numeric:
                mn = float(np.nanmin(peers_numeric[name]))
                mx = float(np.nanmax(peers_numeric[name]))
                if np.isclose(mx, mn):
                    norm = 0.5
                else:
                    norm = float((val_w - mn) / (mx - mn))
            else:
                norm = val_w
        else:
            raise ValueError("normalize_method must be 'percentile'|'zscore'|'minmax'")

        per_metric.append({"metric": name, "raw": float(transform_notes[name]["raw"]), "transformed": float(adj), "winsorized": float(val_w), "normalized": norm, "higher_is_good": transform_notes[name]["higher_is_good"], "used_peers": (peers_available and name in peers_numeric)})

    per_metric_df = pd.DataFrame(per_metric).set_index("metric")

    # -------------- If normalize_method required category min-max fallback --------------
    # For metrics where "normalized" currently holds raw adjusted values (i.e. no peers and percentile requested),
    # we will perform min-max scaling **within each category** (this follows the earlier recommended fallback).
    if normalize_method == "percentile" and not peers_available:
        # We'll compute min-max scaling per category on per_metric_df['transformed'] values for metrics in that category.
        # Build mapping metric->category to know which metrics are in which category
        metric_to_cats = {}
        for cat, mlist in ratio_groups.items():
            for m in mlist:
                metric_to_cats.setdefault(m, []).append(cat)

        # create new normalized column
        per_metric_df["normalized_pct"] = np.nan

        for cat, mlist in ratio_groups.items():
            # collect transformed values for metrics in this category that exist in per_metric_df
            present = [m for m in mlist if m in per_metric_df.index]
            if len(present) == 0:
                continue
            arr = per_metric_df.loc[present, "transformed"].values.astype(float)
            mn = np.nanmin(arr)
            mx = np.nanmax(arr)
            if np.isclose(mx, mn):
                scaled = np.full_like(arr, 0.5, dtype=float)
            else:
                scaled = (arr - mn) / (mx - mn)
                scaled = np.clip(scaled, 0.0, 1.0)
            per_metric_df.loc[present, "normalized_pct"] = scaled

        # move normalized result to 'normalized' column for aggregation
        per_metric_df["normalized"] = per_metric_df["normalized_pct"]
        per_metric_df.drop(columns=["normalized_pct"], inplace=True, errors="ignore")

    # -------------- aggregate per category ----------------
    category_scores: Dict[str, float] = {}
    for cat, mlist in ratio_groups.items():
        present = [m for m in mlist if m in per_metric_df.index and not pd.isna(per_metric_df.loc[m, "normalized"])]
        if len(present) < min_metrics_per_category:
            category_scores[cat] = np.nan
            continue

        vals = per_metric_df.loc[present, "normalized"].astype(float).values
        # if normalize_method was zscore, we need to convert to 0..1 before averaging (robust)
        if normalize_method == "zscore":
            # convert z to percentile-like via normal CDF approximation (use rank fallback if peers not available)
            try:
                from scipy.stats import norm as _norm
                probs = _norm.cdf(vals)  # 0..1
            except Exception:
                # fallback to rank-based
                probs = (rankdata(vals) - 1) / (len(vals) - 1) if len(vals) > 1 else np.array([0.5] * len(vals))
            cat_score = float(np.nanmean(probs))
        else:
            # normalized is already 0..1 for percentile/minmax; ensure clipping
            clipped = np.clip(vals, 0.0, 1.0)
            cat_score = float(np.nanmean(clipped))

        category_scores[cat] = round(float(cat_score * output_scale), 2)

    # -------------- final metadata & return ----------------
    metadata = {
        "normalize_method": normalize_method,
        "used_peers": peers_available,
        "winsor_pct": winsor_pct,
        "min_metrics_per_category": min_metrics_per_category,
    }

    # reorder per_metric_df columns for convenience
    per_metric_df = per_metric_df[["raw", "transformed", "winsorized", "normalized", "higher_is_good", "used_peers"]]

    logger.info("Calculated category scores for %d categories (peers used: %s)", len(category_scores), peers_available)

    risk_score_dict = convert_to_risk_score(category_scores)

    return {"category_scores": risk_score_dict, "metadata": metadata}