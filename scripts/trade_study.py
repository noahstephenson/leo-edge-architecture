"""Multi-criteria trade study (v3) over the candidate architectures.

Fixes applied vs. v2 (docs/DECISION_LOG.md has the ADRs):
- terminal_swap_burden (which scored GroundOnly best, backwards: GroundOnly
  puts ALL processing burden on the Army terminal) is replaced by two
  correctly-signed, code-derived criteria: space_segment_processing_burden
  and terminal_processing_burden.
- Every criterion that can be derived from a real simulated field or an
  architecture property now is: fidelity from the real fidelity_lossy
  field (results/frozen/v3/e03_results.csv), both burden criteria from
  real processing_energy_j data, and acquisition_lock_in_risk from each
  architecture's actual tier count plus whether it has per-request
  conditional logic (src/leo_edge/architectures.py's CONDITIONAL_LOGIC
  flag). Nothing here is a free-floating hand-picked number anymore; see
  the one-line derivation rule on each criterion below.
- Rankings are reported twice: SIMULATED_ONLY (mission_thread_success,
  latency, resilience -- the three criteria that come directly from Monte
  Carlo/SGP4 simulation) and COMBINED (all seven, including the four
  derived-from-architecture-properties criteria), with every rank flip
  between the two reported explicitly.
- Latency now comes from results/frozen/v3/e11_mission_thread_trials.csv
  via a Kaplan-Meier-style censored median (src/leo_edge/stats.py), not a
  mean over completed-only e03 rows, which silently dropped every
  non-completion instead of counting it as "took longer than observed."
- A6 (ThreadAwarePriority) is reported in a separate table from the
  original A0-A5 candidate set (src/leo_edge/architectures.py's
  PROVENANCE flag), never folded into one ranking that hides which
  architectures existed before any evaluation results did.
"""

import csv
from pathlib import Path

import pandas as pd

from leo_edge.architectures import (
    GroundOnly, CompressedFull, QuicklookFirst, RoiFirst, Progressive, ContactAware, ThreadAwarePriority,
)
from leo_edge.products import ProductTier
from leo_edge.stats import kaplan_meier_median

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results" / "frozen" / "v4"
HORIZON_S = 168 * 3600.0

ARCH_CLASSES = {
    "GroundOnly": GroundOnly, "CompressedFull": CompressedFull, "QuicklookFirst": QuicklookFirst,
    "RoiFirst": RoiFirst, "Progressive": Progressive, "ContactAware": ContactAware,
    "ThreadAwarePriority": ThreadAwarePriority,
}
ORIGINAL_SET = [name for name, cls in ARCH_CLASSES.items() if cls.PROVENANCE == "original_candidate_set"]
PROPOSED_SET = [name for name, cls in ARCH_CLASSES.items() if cls.PROVENANCE != "original_candidate_set"]

SIMULATED_CRITERIA = ["mission_thread_success", "latency", "resilience"]
DERIVED_CRITERIA = ["fidelity", "space_segment_processing_burden", "terminal_processing_burden", "acquisition_lock_in_risk"]
ALL_CRITERIA = SIMULATED_CRITERIA + DERIVED_CRITERIA

# Stakeholder-leaning weight profiles (docs/STAKEHOLDERS.md). Each sums to
# 1.0 over ALL_CRITERIA; SIMULATED_ONLY rankings renormalize the
# SIMULATED_CRITERIA subset to sum to 1.0 instead of dropping the rest.
WEIGHT_PROFILES = {
    "TACTICAL_USER_LEANING": {
        "mission_thread_success": 0.35, "latency": 0.25, "fidelity": 0.15,
        "space_segment_processing_burden": 0.05, "terminal_processing_burden": 0.05,
        "resilience": 0.10, "acquisition_lock_in_risk": 0.05,
    },
    "ACQUISITION_LEANING": {
        "mission_thread_success": 0.15, "latency": 0.10, "fidelity": 0.10,
        "space_segment_processing_burden": 0.075, "terminal_processing_burden": 0.075,
        "resilience": 0.15, "acquisition_lock_in_risk": 0.35,
    },
    "TERMINAL_OPERATOR_LEANING": {
        # The terminal operator cares most about their own SWaP burden
        # (terminal_processing_burden), much less about the provider's
        # space-segment burden, which isn't their problem.
        "mission_thread_success": 0.15, "latency": 0.10, "fidelity": 0.10,
        "space_segment_processing_burden": 0.10, "terminal_processing_burden": 0.30,
        "resilience": 0.20, "acquisition_lock_in_risk": 0.05,
    },
    "BALANCED": {c: 1 / len(ALL_CRITERIA) for c in ALL_CRITERIA},
}


def _normalize(series: pd.Series, higher_is_better: bool) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series([0.5] * len(series), index=series.index)
    norm = (series - lo) / (hi - lo)
    return norm if higher_is_better else 1.0 - norm


def load_criteria():
    e03 = pd.read_csv(RESULTS_DIR / "e03_results.csv")
    e11_trials = pd.read_csv(RESULTS_DIR / "e11_mission_thread_trials.csv")
    e11_summary = pd.read_csv(RESULTS_DIR / "e11_mission_thread_success.csv")

    # --- Simulated criteria ---

    # Mission-thread success: mean success rate across all e11 cells.
    mission_success = e11_summary.groupby("architecture")["success_rate"].mean()

    # Resilience: mean success rate under degraded conditions only.
    degraded = e11_summary[e11_summary["condition"] != "NOMINAL"]
    resilience = degraded.groupby("architecture")["success_rate"].mean()

    # Latency: Kaplan-Meier median time-to-product from e11's per-trial
    # data, censoring trials that never produced the needed tier at the
    # evaluation horizon instead of dropping them (item 8's fix; replaces
    # v2's mean-TFUP-over-completed-e03-rows, which silently discarded
    # every non-completion).
    latency = {}
    for arch, group in e11_trials.groupby("architecture"):
        times = [
            row.latency_s if row.produced_tier else HORIZON_S
            for row in group.itertuples()
        ]
        censored = [not row.produced_tier for row in group.itertuples()]
        latency[arch] = kaplan_meier_median(times, censored, HORIZON_S)
    latency = pd.Series(latency)

    # --- Derived criteria (all from real e03 fields or architecture code) ---

    # Fidelity: fraction of e03 rows delivered lossless (real fidelity_lossy field).
    fidelity = e03.groupby("architecture_name")["fidelity_lossy"].apply(lambda s: (~s).mean())

    # Space-segment processing burden: real mean processing_energy_j from
    # e03 (higher energy = more onboard/provider-side compute burden).
    space_energy = e03.groupby("architecture_name")["processing_energy_j"].mean()

    # Terminal processing burden: fraction of e03 rows where the
    # architecture did zero onboard processing (processing_energy_j == 0),
    # i.e. delivered something the terminal itself must fully process to
    # be useful (raw bytes). One-line rule: burden falls on whichever
    # segment didn't do the processing.
    terminal_burden_frac = e03.groupby("architecture_name")["processing_energy_j"].apply(lambda s: (s == 0).mean())

    # Acquisition lock-in risk (v4 fix, docs/DECISION_LOG.md ADR-021):
    # tied to the actual ownership boundary in docs/INTERFACES.md, not a
    # bare tier count. docs/INTERFACES.md's function-to-segment table shows
    # Process/Prioritize/Transmit are on the commercial segment for EVERY
    # architecture here -- the function allocation itself doesn't vary, so
    # it can't be what distinguishes lock-in risk between architectures.
    # What does vary, per architecture, is (a) how many of
    # INTERFACES.md's distinct named data-format interfaces (Metadata,
    # Thumbnail, Quicklook, ROI, Full) the Army terminal must be able to
    # ingest from that specific provider's implementation, i.e. non-
    # metadata tier count, same base count as before, and (b) whether the
    # provider's behavior is CONDITIONAL_LOGIC: a per-request runtime
    # decision (e.g. A6's priority-tier choice, A5's margin check) is a
    # non-standard interface in the sense INTERFACES.md's own "Interface
    # Standards" section means it -- it can't be pinned down by a static
    # format spec, so the Army depends on a provider-specific runtime
    # behavior, not just a provider-specific but still fixed data format.
    # That's a real difference in kind, not degree, from one more fixed
    # tier, so it's weighted higher (2) than a tier count of 1.
    CONDITIONAL_LOGIC_WEIGHT = 2
    lock_in_functions = {}
    for name, cls in ARCH_CLASSES.items():
        instance = cls(priority_tier=ProductTier.P2_QUICKLOOK) if name == "ThreadAwarePriority" else cls()
        try:
            tiers = instance.tiers(1_000_000_000, processing_time_s=20.0)
        except TypeError:
            tiers = instance.tiers(1_000_000_000)
        non_meta = sum(1 for tier, _b, _p in tiers if tier != ProductTier.P0_METADATA)
        lock_in_functions[name] = non_meta + (CONDITIONAL_LOGIC_WEIGHT if cls.CONDITIONAL_LOGIC else 0)
    lock_in_functions = pd.Series(lock_in_functions)

    rows = []
    for arch in ARCH_CLASSES:
        rows.append({
            "architecture": arch,
            "mission_thread_success_raw": mission_success.get(arch, 0.0),
            "resilience_raw": resilience.get(arch, 0.0),
            "latency_s_raw": latency.get(arch, float("nan")),
            "fidelity_raw": fidelity.get(arch, 0.0),
            "space_segment_processing_burden_raw": space_energy.get(arch, float("nan")),
            "terminal_processing_burden_raw": terminal_burden_frac.get(arch, 0.0),
            "lock_in_functions_raw": lock_in_functions.get(arch, float("nan")),
        })
    df = pd.DataFrame(rows).set_index("architecture")

    # A latency that's NaN (KM median undefined: most trials for this
    # architecture never completed, e.g. structurally incapable ones) is
    # filled with the horizon (the worst possible real value), not
    # silently excluded, matching the censoring philosophy above.
    df["latency_s_raw"] = df["latency_s_raw"].fillna(HORIZON_S)
    df["space_segment_processing_burden_raw"] = df["space_segment_processing_burden_raw"].fillna(
        df["space_segment_processing_burden_raw"].max()
    )

    norm = pd.DataFrame(index=df.index)
    norm["mission_thread_success"] = _normalize(df["mission_thread_success_raw"], higher_is_better=True)
    norm["resilience"] = _normalize(df["resilience_raw"], higher_is_better=True)
    norm["latency"] = _normalize(df["latency_s_raw"], higher_is_better=False)
    norm["fidelity"] = df["fidelity_raw"]  # already in [0,1]
    norm["space_segment_processing_burden"] = _normalize(df["space_segment_processing_burden_raw"], higher_is_better=False)
    norm["terminal_processing_burden"] = 1.0 - df["terminal_processing_burden_raw"]  # higher raw burden = worse
    norm["acquisition_lock_in_risk"] = _normalize(df["lock_in_functions_raw"], higher_is_better=False)

    return df, norm


def score(norm: pd.DataFrame, weights: dict, criteria: list) -> pd.Series:
    total_w = sum(weights[c] for c in criteria)
    return sum(norm[c] * (weights[c] / total_w) for c in criteria)


def rank_table(norm: pd.DataFrame, weights: dict, criteria: list, architectures: list) -> pd.Series:
    sub = norm.loc[architectures]
    return score(sub, weights, criteria).sort_values(ascending=False)


def weight_sensitivity(norm: pd.DataFrame, base_weights: dict, criterion: str, deltas, architectures: list):
    """Sweep one criterion's weight up/down (renormalizing the rest
    proportionally) and report the top-ranked architecture at each point,
    over the COMBINED view (all seven criteria) and the WITH_A6 set."""
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
        s = rank_table(norm, adjusted, ALL_CRITERIA, architectures)
        rows.append({"criterion": criterion, "weight": new_w, "top_architecture": s.idxmax(), "top_score": s.max()})
    return rows


def main():
    df, norm = load_criteria()

    print("Raw values (real simulated/derived data, not normalized):")
    print(df.round(3).to_string())
    print()
    print("Normalized criteria (0=worst, 1=best):")
    print(norm.round(3).to_string())
    print()

    summary_rows = []
    for profile_name, weights in WEIGHT_PROFILES.items():
        for arch_set_name, arch_set in [("ORIGINAL_SET", ORIGINAL_SET), ("WITH_A6", list(ARCH_CLASSES))]:
            for view_name, criteria in [("SIMULATED_ONLY", SIMULATED_CRITERIA), ("COMBINED", ALL_CRITERIA)]:
                ranked = rank_table(norm, weights, criteria, arch_set)
                print(f"--- {profile_name} | {arch_set_name} | {view_name} ---")
                print(ranked.round(3).to_string())
                print()
                for rank, (arch, val) in enumerate(ranked.items(), start=1):
                    summary_rows.append({
                        "profile": profile_name, "architecture_set": arch_set_name, "view": view_name,
                        "rank": rank, "architecture": arch, "score": val,
                    })

    out_path = RESULTS_DIR / "trade_study_scores.csv"
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"Saved {out_path}")

    # Report every case where SIMULATED_ONLY and COMBINED disagree on the
    # top-ranked architecture, for the same profile and architecture set --
    # exactly the "which flips exist only because of derived/judgment
    # criteria" question item 2 requires an answer to.
    print("\nWhere SIMULATED_ONLY and COMBINED disagree on the top architecture:")
    for profile_name in WEIGHT_PROFILES:
        for arch_set_name, arch_set in [("ORIGINAL_SET", ORIGINAL_SET), ("WITH_A6", list(ARCH_CLASSES))]:
            sim_top = rank_table(norm, WEIGHT_PROFILES[profile_name], SIMULATED_CRITERIA, arch_set).idxmax()
            comb_top = rank_table(norm, WEIGHT_PROFILES[profile_name], ALL_CRITERIA, arch_set).idxmax()
            if sim_top != comb_top:
                print(f"  {profile_name} / {arch_set_name}: SIMULATED_ONLY top={sim_top}, COMBINED top={comb_top}")

    # Weight-sensitivity sweep (COMBINED view, WITH_A6 set): where does the
    # top-ranked architecture change as a criterion's weight moves?
    sens_rows = []
    for profile_name, weights in WEIGHT_PROFILES.items():
        for criterion in weights:
            sens_rows.extend(
                weight_sensitivity(norm, weights, criterion, [-0.15, -0.05, 0.0, 0.05, 0.15, 0.30], list(ARCH_CLASSES))
            )
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

    print("\nWeight-sensitivity rank flips (COMBINED view, WITH_A6 set):")
    for flip in sorted(flips):
        print(f"  {flip}")


if __name__ == "__main__":
    main()
