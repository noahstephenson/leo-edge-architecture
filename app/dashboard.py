"""Streamlit dashboard: how commercial LEO imagery reaches an Army edge
terminal, and what the study found. Notional and unofficial.

Every number on the results tabs is read from results/frozen/v4/, not typed
in here. The live explorer runs the real architecture code for one contact
window.
"""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from leo_edge.architectures import (
    CompressedFull, ContactAware, GroundOnly, Progressive, QuicklookFirst, RoiFirst, ThreadAwarePriority,
)
from leo_edge.mission_threads import MISSION_THREADS as _THREADS
from leo_edge.simulation import simulate_multi_contact

RESULTS = repo_root / "results" / "frozen" / "v4"
SCENE_BYTES = 1_000_000_000  # one 1 GB scene, as in experiment e03
BASE_PROC_S, BASE_POWER_W = 20.0, 15.0

st.set_page_config(page_title="LEO Edge: imagery to the tactical edge", layout="wide")


@st.cache_data
def load(name):
    return pd.read_csv(RESULTS / name)


# ---------- plain-language labels ----------
ARCH_LABELS = {
    "GroundOnly": "A0 Raw only (no onboard processing)",
    "CompressedFull": "A1 Compress, send one product",
    "QuicklookFirst": "A2 Quicklook first, then full",
    "RoiFirst": "A3 Region of interest first, then full",
    "Progressive": "A4 Progressive tiers (P0 to P4)",
    "ContactAware": "A5 Contact-aware (compressed or raw)",
    "ThreadAwarePriority": "A6 Thread-aware (proposed)",
}
THREAD_LABELS = {
    "MT1_TIME_SENSITIVE_CUEING": "MT-1 Time-sensitive cueing",
    "MT2_ROUTE_RECON_FIRST": "MT-2 Route reconnaissance",
}
THREAD_STORY = {
    "MT1_TIME_SENSITIVE_CUEING": "A unit needs a fast, coarse answer to 'is something there?' to decide whether to commit assets. Speed beats resolution.",
    "MT2_ROUTE_RECON_FIRST": "A unit planning a route needs a full-resolution crop of the corridor before it moves. A coarse image is not enough.",
}
TIER_NAMES = {
    "P0_METADATA": "P0 metadata", "P1_THUMBNAIL": "P1 thumbnail", "P2_QUICKLOOK": "P2 quicklook",
    "P3_ROI": "P3 region of interest", "P4_FULL": "P4 full scene",
}
TERMINALS = {"Vehicle-mounted terminal (about 50 Mbps)": 50_000_000, "Dismounted / manpack terminal (about 5 Mbps)": 5_000_000}
CONDITIONS = {
    "Nominal": (1.0, 60),
    "Jamming or interference (link at half rate)": (0.5, 60),
    "Reachback lost (tasking takes 180 s)": (1.0, 180),
    "Both degraded": (0.5, 180),
}


def make_architectures(needed_tier):
    return {
        "GroundOnly": GroundOnly(), "CompressedFull": CompressedFull(), "QuicklookFirst": QuicklookFirst(),
        "RoiFirst": RoiFirst(), "Progressive": Progressive(), "ContactAware": ContactAware(alpha=0.2),
        "ThreadAwarePriority": ThreadAwarePriority(priority_tier=needed_tier),
    }


st.title("Getting commercial satellite imagery to a tactical edge terminal")
st.caption("A notional, unofficial systems-architecture study. Nothing here is an Army requirement, program, or decision.")

tab_start, tab_try, tab_sweep, tab_trade, tab_about = st.tabs(
    ["1. The problem", "2. Try it", "3. How much access is enough?", "4. Which architecture?", "5. Terms and limits"]
)

# ======================= TAB 1 =======================
with tab_start:
    st.header("The operational problem")
    st.markdown(
        """
The Army increasingly **buys imagery as a service** from commercial LEO satellites, while
**owning its own tactical ground terminals**. A satellite is only in range of a terminal for a few
minutes at a time, and it has to be over the target area first. So a unit that asks for imagery waits,
first for a satellite to pass over the target, then for a downlink window to the terminal.

The study asks: **which imagery functions should the commercial provider do, which should the Army do,
and how much satellite access does it take before any of that matters?**
"""
    )
    st.graphviz_chart(
        """
digraph G {
  rankdir=LR; node [shape=box, style="rounded,filled", fontname="Helvetica"];
  subgraph cluster_a { label="Army: requesting side"; style=filled; color="#e3efe3";
    user [label="Tactical user", fillcolor="#cfe5cf"]; rear [label="Rear-echelon\\ntasking cell", fillcolor="#cfe5cf"]; }
  subgraph cluster_c { label="Commercial provider (bought as a service)"; style=filled; color="#e0e9f7";
    sat [label="LEO satellites\\ncollect, tier, prioritize, transmit", fillcolor="#c6d9f2"]; }
  subgraph cluster_e { label="Army: edge"; style=filled; color="#e3efe3";
    term [label="Edge terminal\\nvehicle or dismounted", fillcolor="#cfe5cf"]; }
  user -> rear [label="1 request"]; rear -> sat [label="2 collection request"];
  user -> sat [label="1b direct tasking", style=dashed];
  sat -> term [label="3 tiered product\\nonly in contact windows", penwidth=3];
  term -> user [label="4 actionable product"];
}
"""
    )
    st.markdown(
        """
**The thick arrow is the ownership boundary.** It is the only place the Army depends on a provider's
implementation. The seven candidate architectures differ only in what the blue box does before that arrow:
for example, sending a small quicklook first instead of waiting for the full scene.
"""
    )

    st.subheader("Four notional mission threads")
    rows = []
    for key, t in _THREADS.items():
        rows.append({
            "Thread": {"MT1_TIME_SENSITIVE_CUEING": "MT-1 Cueing", "MT2_ROUTE_RECON_FIRST": "MT-2 Route reconnaissance",
                       "MT3_BATTLE_DAMAGE_ASSESSMENT": "MT-3 Damage assessment", "MT4_PERSISTENT_MONITORING": "MT-4 Persistent monitoring"}[key],
            "Needs first": TIER_NAMES[t["needed_tier"].name],
            "Must arrive within": f"{t['latency_tolerance_s']} s" + (" of each pass" if t["cadence"] else " of the request"),
        })
    st.table(pd.DataFrame(rows))
    st.caption("All tolerances are assumptions chosen to be plausible, not sourced requirements (docs/MISSION_THREADS.md).")

    st.subheader("What the study found")
    sweep = load("e12_access_sweep.csv")
    g = sweep.groupby(["satellites", "planes", "terminals", "architecture"])[["successes", "n_trials"]].sum().reset_index()
    g["rate"] = g.successes / g.n_trials
    best = g.loc[g.groupby(["satellites", "planes", "terminals"]).rate.idxmax()]
    lo, hi = best.sort_values("satellites").iloc[0], best.sort_values("rate").iloc[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("Best success rate, 1 satellite", f"{lo.rate:.0%}")
    c2.metric(f"Best success rate, {int(hi.satellites)} satellites in {int(hi.planes)} planes, {int(hi.terminals)} terminals", f"{hi.rate:.0%}")
    never = int((sweep.groupby("architecture").successes.sum() == 0).sum())
    c3.metric("Architectures that never succeed", f"{never} of {sweep.architecture.nunique()}")
    st.markdown(
        """
- **Access dominates.** More satellites raise mission-thread success far more than any architecture choice.
- **Tiering is necessary.** Raw downlink, compress-everything, and the contact-aware policy never deliver an early product, so they never succeed.
- **Once access is high enough to test, architecture matters** among the tiered designs, but the sweep stops at 24 satellites and only one cell is informative. Treat that as a lead, not a conclusion.

Use the tabs above to explore each finding.
"""
    )

# ======================= TAB 2 =======================
with tab_try:
    st.header("Try it: one satellite pass over one terminal")
    st.markdown(
        "Pick a mission, a terminal, and conditions. The real architecture code then answers: "
        "**does each architecture get the product the unit needs to it in time?**"
    )
    c1, c2, c3 = st.columns(3)
    thread_key = c1.selectbox("Mission", list(THREAD_LABELS), format_func=THREAD_LABELS.get)
    terminal_name = c2.selectbox("Terminal", list(TERMINALS))
    cond_name = c3.selectbox("Conditions", list(CONDITIONS))
    thread = _THREADS[thread_key]
    st.info(THREAD_STORY[thread_key] + f" Needs **{TIER_NAMES[thread['needed_tier'].name]}** within **{thread['latency_tolerance_s']} s** of the request.")

    with st.expander("Adjust the link (advanced)"):
        a1, a2, a3 = st.columns(3)
        rate_bps = a1.slider("Downlink rate (Mbps)", 1, 100, TERMINALS[terminal_name] // 1_000_000) * 1_000_000
        contact_s = a2.slider("How long the satellite stays in range (s)", 60, 600, 300, 10)
        power_w = a3.slider("Onboard processor power (W)", 5.0, 30.0, 15.0, 0.5)

    derate, tasking_s = CONDITIONS[cond_name]
    proc_s = BASE_PROC_S * BASE_POWER_W / power_w
    eff_rate = rate_bps * derate
    st.markdown(
        f"**Scenario:** the satellite is in range for **{contact_s} s** at **{eff_rate/1e6:.0f} Mbps** "
        f"(about {eff_rate * contact_s / 8 / 1e6:,.0f} MB can be sent). Tasking takes **{tasking_s} s**. "
        f"Onboard processing takes about **{proc_s:.0f} s**. The scene is 1 GB."
    )

    rows = []
    for name, arch in make_architectures(thread["needed_tier"]).items():
        r = simulate_multi_contact(arch, SCENE_BYTES, [(0.0, contact_s)], eff_rate, proc_s)
        t_needed = r.tier_completion_s.get(thread["needed_tier"].value)
        total = None if t_needed is None else t_needed + tasking_s
        if t_needed is None:
            verdict, why = "Misses", "never delivers this tier in the window"
        elif total <= thread["latency_tolerance_s"]:
            verdict, why = "Meets", f"needed product arrives {total:.0f} s after the request"
        else:
            verdict, why = "Misses", f"arrives {total:.0f} s after the request, too late"
        rows.append({"Architecture": ARCH_LABELS[name], "Result": verdict, "Why": why, "_total": total})
    res = pd.DataFrame(rows)

    def color(v):
        return "background-color:#cfe5cf" if v == "Meets" else "background-color:#f3d2d2"

    st.dataframe(res[["Architecture", "Result", "Why"]].style.map(color, subset=["Result"]), width="stretch", hide_index=True)

    fig, ax = plt.subplots(figsize=(9, 3.6))
    plot = res.dropna(subset=["_total"])
    ax.barh([r.split(" (")[0] for r in plot.Architecture], plot._total, color=["#5a9e5a" if v == "Meets" else "#c76b6b" for v in plot.Result])
    ax.axvline(thread["latency_tolerance_s"], color="black", linestyle="--")
    ax.text(thread["latency_tolerance_s"], -0.6, " time limit", va="bottom")
    ax.set_xlabel("Seconds from request until the needed product arrives")
    ax.invert_yaxis()
    st.pyplot(fig)
    if plot.empty:
        st.warning("No architecture delivers the needed product in this window. Try a longer window or a faster link.")
    st.caption(
        "This checks one satellite pass only. In reality a unit must first wait for a satellite to pass over the target, "
        "then wait for a downlink window, so real success is far lower. Tabs 3 and 4 show the full picture."
    )

# ======================= TAB 3 =======================
with tab_sweep:
    st.header("How much satellite access is enough?")
    st.markdown(
        "The sweep adds real satellites (each propagated with SGP4, arranged as Walker-delta constellations) "
        "and Army ground terminals, and asks how often a mission thread succeeds. "
        "The chart shows the **best architecture** at each size."
    )
    sweep = load("e12_access_sweep.csv")
    g = sweep.groupby(["satellites", "planes", "terminals", "architecture"])[["successes", "n_trials"]].sum().reset_index()
    g["rate"] = g.successes / g.n_trials
    best = g.loc[g.groupby(["satellites", "planes", "terminals"]).rate.idxmax()]
    best = best.sort_values("planes").groupby(["satellites", "terminals"], as_index=False).tail(1)
    pivot = best.pivot(index="satellites", columns="terminals", values="rate")
    pivot.columns = [f"{c} terminal(s)" for c in pivot.columns]
    st.line_chart(pivot, y_label="Best architecture's mission-thread success rate", x_label="Satellites in the constellation")
    st.caption("Each point pools all four threads and both conditions. There are only 40 trials per thread per cell, so differences under about 3 points are noise.")

    st.subheader("Where can architectures be compared at all?")
    status = load("e12_cell_status.csv").sort_values("planes").groupby(["satellites", "terminals"], as_index=False).tail(1)
    label = {"UNINFORMATIVE": "too low to compare", "TIES": "compared: tied", "SEPARATES": "compared: a winner"}
    status["Outcome"] = status.status.map(label)
    st.dataframe(status.pivot(index="terminals", columns="satellites", values="Outcome"), width="stretch")
    st.caption(
        "An architecture comparison is only meaningful when the best one succeeds more than 30% of the time. "
        "Below that, nothing works well enough to tell designs apart, which is different from the designs being equal."
    )

    st.subheader("Can each thread be met at all?")
    feas = load("e12_feasibility_floors.csv")
    feas = feas.sort_values("planes").groupby(["satellites", "thread"], as_index=False).tail(1)
    fp = feas.assign(Thread=feas.thread.map(lambda t: t.split("_")[0]), Status=feas.status.str.replace("_", " ").str.lower()).pivot(index="satellites", columns="Thread", values="Status")
    st.dataframe(fp, width="stretch")
    st.caption(
        "'infeasible at this access' means the typical wait for the next overflight already exceeds the time limit. "
        "No thread is impossible outright: the fastest possible chain (tasking + processing + transmit) fits inside every limit."
    )

# ======================= TAB 4 =======================
with tab_trade:
    st.header("Which architecture should the Army ask for?")
    st.markdown(
        "Seven criteria are scored (3 from simulation, 4 derived from each design's properties) under four "
        "stakeholder weightings. Pick a view to see the ranking."
    )
    scores = load("trade_study_scores.csv")
    a, b, c = st.columns(3)
    profile = a.selectbox("Whose priorities?", sorted(scores.profile.unique()), format_func=lambda p: p.replace("_", " ").title())
    aset = b.selectbox("Which designs?", ["ORIGINAL_SET", "WITH_A6"], format_func=lambda s: "Original six (A0 to A5)" if s == "ORIGINAL_SET" else "Original six plus proposed A6")
    view = c.selectbox("Which criteria?", ["COMBINED", "SIMULATED_ONLY"], format_func=lambda s: "All seven" if s == "COMBINED" else "Simulated only (success, latency, resilience)")
    sub = scores[(scores.profile == profile) & (scores.architecture_set == aset) & (scores.view == view)].sort_values("rank")
    sub = sub.assign(Architecture=sub.architecture.map(ARCH_LABELS), Score=sub.score.round(3))[["rank", "Architecture", "Score"]]
    st.dataframe(sub, width="stretch", hide_index=True)
    st.markdown(
        """
**Why the answer changes with the view.** On the simulated criteria alone, the designs that send the needed tier first
(Progressive and the proposed A6) win. Once *acquisition lock-in risk* is included, **A3 Region-of-interest first** wins
in every weighting, because it has the fewest and simplest interfaces to specify in a contract, even though
Progressive and A6 succeed more often. That is a genuine tradeoff for whoever writes the requirement.
"""
    )
    e11 = load("e11_mission_thread_success.csv")
    base = e11.groupby("architecture").success_rate.mean().sort_values(ascending=False)
    st.subheader("Single-satellite baseline: mission-thread success")
    st.bar_chart(pd.DataFrame({"Success rate": base.values}, index=[ARCH_LABELS[a].split(" (")[0] for a in base.index]))

# ======================= TAB 5 =======================
with tab_about:
    st.header("Terms and honest limits")
    st.markdown(
        """
**Terms**
- **Tier (P0 to P4):** a product at increasing detail: metadata, thumbnail, quicklook, region-of-interest crop, full scene.
- **TFUP / TCP:** time to the first useful product, and time to the complete product.
- **Contact window:** the few minutes a satellite is in range of a terminal.
- **Tasking:** telling the provider what to image, through a rear-echelon cell (reachback) or directly from the edge terminal.
- **Walker-delta constellation:** satellites spread evenly across several orbital planes.
- **AOI:** area of interest, the place being imaged.

**Limits**
- Everything operational is notional. Tolerances, terminal locations, and the target area are assumptions.
- The access sweep stops at 24 satellites and uses 40 trials per cell.
- Only one cell of the sweep is informative enough to compare architectures, so the architecture finding is a lead.
- No design here moves processing to the Army edge; that is a gap, not a finding (docs/ALLOCATION_SPACE.md).

Full detail: `README.md`, `docs/ACQUISITION_IMPLICATIONS.md`, `docs/TRADE_STUDY.md`, `docs/DECISION_LOG.md`.
"""
    )
