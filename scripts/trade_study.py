"""Multi-criteria trade study over the six candidate architectures.

Combines quantitative evidence from results/frozen/v2/ (e03 completion/
energy, e11 mission-thread success) with a stated qualitative rubric
(fidelity, terminal SWaP burden, acquisition lock-in risk) into a weighted
score per architecture, under several stakeholder-leaning weight profiles,
plus a weight-sensitivity sweep that reports where the top-ranked
architecture changes.

Every criterion is normalized to [0, 1] where higher is better before
weighting. The qualitative rubric values are stated assumptions with a
one-line rationale each, not measurements; see the RUBRIC dict below and
docs/TRADE_STUDY.md for how they're meant to be read.
"""

import csv
import itertools
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results" / "frozen" / "v2"

ARCHITECTURES = [
    "GroundOnly", "CompressedFull", "QuicklookFirst", "RoiFirst", "Progressive", "ContactAware",
]

# Qualitative rubric, 0 (worst) to 1 (best) per architecture. Stated design
# judgments, not measurements:
# - fidelity_when_complete: does the architecture's complete product retain
#   full information (lossless) or discard it (lossy compression)?
# - terminal_swap_burden (higher = lower burden, i.e. better): how much
#   onboard processing this architecture demands, as a proxy for the
#   compute/power burden it would place on whichever segment does the work.
# - acquisition_lock_in_risk (higher = lower risk, i.e. better): how
#   standardized/simple the architecture's provider-side behavior is; a
#   fixed, simple rule is easier to specify in a multi-vendor contract than
#   a complex adaptive one.
RUBRIC = {
    "GroundOnly":      {"fidelity_when_complete": 1.0, "terminal_swap_burden": 1.0, "acquisition_lock_in_risk": 1.0},
    "CompressedFull":  {"fidelity_when_complete": 0.6, "terminal_swap_burden": 0.6, "acquisition_lock_in_risk": 0.9},
    "QuicklookFirst":  {"fidelity_when_complete": 1.0, "terminal_swap_burden": 0.5, "acquisition_lock_in_risk": 0.8},
    "RoiFirst":        {"fidelity_when_complete": 1.0, "terminal_swap_burden": 0.5, "acquisition_lock_in_risk": 0.8},
    "Progressive":      {"fidelity_when_complete": 1.0, "terminal_swap_burden": 0.4, "acquisition_lock_in_risk": 0.6},
    "ContactAware":    {"fidelity_when_complete": 0.6, "terminal_swap_burden": 0.5, "acquisition_lock_in_risk": 0.4},
}

# Stakeholder-leaning weight profiles (docs/STAKEHOLDERS.md), all summing to 1.0.
WEIGHT_PROFILES = {
    "TACTICAL_USER_LEANING": {
        "mission_thread_success": 0.35, "latency": 0.25, "fidelity": 0.15,
        "terminal_swap_burden": 0.10, "resilience": 0.10, "acquisition_lock_in_risk": 0.05,
    },
    "ACQUISITION_LEANING": {
        "mission_thread_success": 0.15, "latency": 0.10, "fidelity": 0.10,
        "terminal_swap_burden": 0.15, "resilience": 0.15, "acquisition_lock_in_risk": 0.35,
    },
    "TERMINAL_OPERATOR_LEANING": {
        "mission_thread_success": 0.15, "latency": 0.10, "fidelity": 0.10,
        "terminal_swap_burden": 0.40, "resilience": 0.20, "acquisition_lock_in_risk": 0.05,
    },
    "BALANCED": {
        "mission_thread_success": 1 / 6, "latency": 1 / 6, "fidelity": 1 / 6,
        "terminal_swap_burden": 1 / 6, "resilience": 1 / 6, "acquisition_lock_in_risk": 1 / 6,
    },
}


def _normalize(series: pd.Series, higher_is_better: bool) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series([0.5] * len(series), index=series.index)
    norm = (series - lo) / (hi - lo)
    return norm if higher_is_better else 1.0 - norm


def load_criteria():
    e03 = pd.read_csv(RESULTS_DIR / "e03_results.csv")
    e11 = pd.read_csv(RESULTS_DIR / "e11_mission_thread_success.csv")

    # Latency: mean TFUP among completed e03 runs (lower is better).
    completed = e03[e03["completed"].astype(bool)]
    latency = completed.groupby("architecture_name")["tfup_s"].mean()

    # Mission-thread success: mean success rate across all e11 threads/
    # terminals/conditions (higher is better).
    mission_success = e11.groupby("architecture")["success_rate"].mean()

    # Resilience: mean success rate under degraded conditions only, i.e.
    # excluding NOMINAL (higher is better).
    degraded = e11[e11["condition"] != "NOMINAL"]
    resilience = degraded.groupby("architecture")["success_rate"].mean()

    rows = []
    for arch in ARCHITECTURES:
        rows.append({
            "architecture": arch,
            "latency_s": latency.get(arch, float("nan")),
            "mission_thread_success": mission_success.get(arch, 0.0),
            "resilience": resilience.get(arch, 0.0),
            "fidelity": RUBRIC[arch]["fidelity_when_complete"],
            "terminal_swap_burden": RUBRIC[arch]["terminal_swap_burden"],
            "acquisition_lock_in_risk": RUBRIC[arch]["acquisition_lock_in_risk"],
        })
    df = pd.DataFrame(rows).set_index("architecture")

    # Latency has no data for architectures that never completed anything
    # in e03 (none currently); fill with the worst observed value so a
    # missing latency doesn't silently drop out of normalization.
    df["latency_s"] = df["latency_s"].fillna(df["latency_s"].max())

    norm = pd.DataFrame(index=df.index)
    norm["latency"] = _normalize(df["latency_s"], higher_is_better=False)
    norm["mission_thread_success"] = _normalize(df["mission_thread_success"], higher_is_better=True)
    norm["resilience"] = _normalize(df["resilience"], higher_is_better=True)
    norm["fidelity"] = df["fidelity"]
    norm["terminal_swap_burden"] = df["terminal_swap_burden"]
    norm["acquisition_lock_in_risk"] = df["acquisition_lock_in_risk"]
    return df, norm


def score(norm: pd.DataFrame, weights: dict) -> pd.Series:
    return sum(norm[c] * w for c, w in weights.items())


def weight_sensitivity(norm: pd.DataFrame, base_weights: dict, criterion: str, deltas):
    """Sweep one criterion's weight up/down (renormalizing the rest
    proportionally) and report the top-ranked architecture at each point,
    to find where the ranking flips."""
    rows = []
    for delta in deltas:
        w = dict(base_weights)
        new_w = max(0.0, min(1.0, w[criterion] + delta))
        remaining = 1.0 - new_w
        other_total = sum(v for k, v in w.items() if k != criterion)
        adjusted = {criterion: new_w}
        for k, v in w.items():
            if k == criterion:
                continue
            adjusted[k] = (v / other_total) * remaining if other_total > 0 else 0.0
        s = score(norm, adjusted)
        rows.append({
            "criterion": criterion, "weight": new_w,
            "top_architecture": s.idxmax(), "top_score": s.max(),
        })
    return rows


def main():
    df, norm = load_criteria()

    print("Normalized criteria (0=worst, 1=best):")
    print(norm.round(3).to_string())
    print()

    summary_rows = []
    for profile_name, weights in WEIGHT_PROFILES.items():
        s = score(norm, weights).sort_values(ascending=False)
        print(f"--- {profile_name} ---")
        print(s.round(3).to_string())
        print()
        for rank, (arch, val) in enumerate(s.items(), start=1):
            summary_rows.append({"profile": profile_name, "rank": rank, "architecture": arch, "score": val})

    out_path = RESULTS_DIR / "trade_study_scores.csv"
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["profile", "rank", "architecture", "score"])
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"Saved {out_path}")

    sens_rows = []
    for profile_name, weights in WEIGHT_PROFILES.items():
        for criterion in weights:
            sens_rows.extend(weight_sensitivity(norm, weights, criterion, [-0.15, -0.05, 0.0, 0.05, 0.15, 0.30]))
            for row in sens_rows[-6:]:
                row["profile"] = profile_name

    sens_path = RESULTS_DIR / "trade_study_sensitivity.csv"
    with sens_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["profile", "criterion", "weight", "top_architecture", "top_score"])
        writer.writeheader()
        writer.writerows(sens_rows)
    print(f"Saved {sens_path}")

    flips = set()
    for profile_name in WEIGHT_PROFILES:
        profile_rows = [r for r in sens_rows if r["profile"] == profile_name]
        by_criterion = {}
        for r in profile_rows:
            by_criterion.setdefault(r["criterion"], set()).add(r["top_architecture"])
        for criterion, tops in by_criterion.items():
            if len(tops) > 1:
                flips.add((profile_name, criterion, tuple(sorted(tops))))

    print()
    print("Weight-sensitivity rank flips found (profile, criterion swept, architectures that won at some point):")
    for f in sorted(flips):
        print(f"  {f}")


if __name__ == "__main__":
    main()
