"""Streamlit dashboard for LEO edge architecture TFUP/TCP sensitivity."""

import sys
from pathlib import Path

# Ensure src is importable
repo_root = Path(__file__).resolve().parents[1]
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from leo_edge.architectures import (
    GroundOnly,
    CompressedFull,
    QuicklookFirst,
    RoiFirst,
    Progressive,
    ContactAware,
    ThreadAwarePriority,
)
from leo_edge.simulation import simulate_multi_contact
from leo_edge.products import ProductTier
from leo_edge.mission_threads import MISSION_THREADS as _MISSION_THREADS_SRC

# Display names map to src/leo_edge/mission_threads.py's keys, the single
# source of truth shared with experiments/e11_mission_thread_success.py
# and tests/test_mission_thread_consistency.py, so this dashboard can't
# silently drift from what e11 actually evaluates. MT-3 and the
# cadence-based MT-4 aren't shown here: MT-3 needs a prior-reference draw
# and MT-4 needs the whole-horizon cadence walk, neither of which fits this
# single-contact-window live check (see the caption below).
_DISPLAY_TO_KEY = {
    "MT-1 Time-sensitive cueing": "MT1_TIME_SENSITIVE_CUEING",
    "MT-2 Route reconnaissance (first product)": "MT2_ROUTE_RECON_FIRST",
}
MISSION_THREADS = {
    display: _MISSION_THREADS_SRC[key] for display, key in _DISPLAY_TO_KEY.items()
}
TERMINAL_CLASSES = {
    "Vehicle-mounted": 50_000_000,
    "Dismounted / manpack": 5_000_000,
}
CONDITIONS = {
    "Nominal": {"derate": 1.0, "tasking_delay_s": 60},
    "Interference (0.5x rate)": {"derate": 0.5, "tasking_delay_s": 60},
    "Reachback lost (direct tasking delay)": {"derate": 1.0, "tasking_delay_s": 180},
    "Combined degraded": {"derate": 0.5, "tasking_delay_s": 180},
}

CSV_PATH = repo_root / "results" / "frozen" / "v2" / "e03_results.csv"

st.set_page_config(page_title="LEO Edge Dashboard", layout="wide")
st.title("LEO Edge Architecture: TFUP / TCP Sensitivity")

# Load frozen results for reference
@st.cache_data
def load_results():
    df = pd.read_csv(CSV_PATH)
    return df

df_ref = load_results()

# Reference values
scene_bytes = 1_000_000_000  # 1 GB from e03
baseline_processing_time_s = 20.0
baseline_processor_power_w = 15.0

st.sidebar.header("Mission Context (docs/MISSION_THREADS.md)")
terminal_class = st.sidebar.selectbox("Terminal class", list(TERMINAL_CLASSES.keys()))
condition_name = st.sidebar.selectbox("Contested condition", list(CONDITIONS.keys()))
thread_name = st.sidebar.selectbox("Mission thread", list(MISSION_THREADS.keys()))

st.sidebar.header("Simulation Controls")
rate_bps = st.sidebar.slider(
    "Downlink rate (bps)",
    min_value=1_000_000,
    max_value=100_000_000,
    value=TERMINAL_CLASSES[terminal_class],
    step=1_000_000,
    format="%d",
)
contact_duration_s = st.sidebar.slider(
    "Contact duration (s)",
    min_value=60,
    max_value=600,
    value=300,
    step=10,
)
processor_power_w = st.sidebar.slider(
    "Processor power (W)",
    min_value=5.0,
    max_value=30.0,
    value=15.0,
    step=0.5,
)

contact_capacity_bytes = rate_bps * contact_duration_s / 8.0
# Scale processing time inversely with power (simple model)
processing_time_s = baseline_processing_time_s * (baseline_processor_power_w / max(processor_power_w, 1e-6))

st.sidebar.metric("Contact capacity (MB)", f"{contact_capacity_bytes/1e6:.1f}")
st.sidebar.metric("Effective processing time (s)", f"{processing_time_s:.2f}")

selected_thread = MISSION_THREADS[thread_name]
arch_map = {
    "A0_GROUND_ONLY": ("GroundOnly", GroundOnly()),
    "A1_COMPRESSED_FULL": ("CompressedFull", CompressedFull()),
    "A2_QUICKLOOK_FIRST": ("QuicklookFirst", QuicklookFirst()),
    "A3_ROI_FIRST": ("RoiFirst", RoiFirst()),
    "A4_PROGRESSIVE": ("Progressive", Progressive()),
    "A5_CONTACT_AWARE": ("ContactAware", ContactAware(alpha=0.2)),
    "A6_THREAD_AWARE_PRIORITY": (
        "ThreadAwarePriority",
        ThreadAwarePriority(priority_tier=selected_thread["needed_tier"]),
    ),
}

results = []
for key, (name, obj) in arch_map.items():
    out = obj.run(
        scene_bytes=scene_bytes,
        contact_capacity_bytes=contact_capacity_bytes,
        rate_bps=rate_bps,
        processing_time_s=processing_time_s,
    )
    results.append({
        "Architecture": key,
        "Name": name,
        "TFUP_s": out["tfup_s"],
        "TCP_s": out["tcp_s"],
        "bytes_transmitted": out["bytes_transmitted"],
        "processing_energy_j": out["processing_energy_j"],
        "tx_energy_j": out["tx_energy_j"],
        "contact_utilization": out["contact_utilization"],
        "Completed": out["completed"],
    })

res_df = pd.DataFrame(results)
res_df = res_df[["Architecture", "Name", "TFUP_s", "TCP_s", "Completed", "contact_utilization", "processing_energy_j", "tx_energy_j"]]

st.subheader("Live Analytic Results")
st.dataframe(res_df.style.format({"TFUP_s": "{:.2f}", "TCP_s": "{:.2f}", "contact_utilization": "{:.3f}", "processing_energy_j": "{:.1f}", "tx_energy_j": "{:.1f}"}), use_container_width=True)

# Plot
fig, ax = plt.subplots(figsize=(8, 4))
x = np.arange(len(res_df))
width = 0.35
ax.bar(x - width/2, res_df["TFUP_s"], width, label="TFUP")
ax.bar(x + width/2, res_df["TCP_s"], width, label="TCP")
ax.set_xticks(x)
ax.set_xticklabels(res_df["Architecture"], rotation=30, ha="right")
ax.set_ylabel("Seconds")
ax.set_title("TFUP and TCP by Architecture")
ax.legend()
st.pyplot(fig)

st.subheader(f"Mission-thread check: {thread_name}, {terminal_class}, {condition_name}")
thread = MISSION_THREADS[thread_name]
condition = CONDITIONS[condition_name]
derated_rate_bps = rate_bps * condition["derate"]
tasking_delay_s = condition["tasking_delay_s"]

thread_rows = []
for key, (name, obj) in arch_map.items():
    result = simulate_multi_contact(
        obj, scene_bytes, [(0.0, contact_duration_s)], derated_rate_bps, processing_time_s,
    )
    tier_time = result.tier_completion_s.get(thread["needed_tier"].value)
    if tier_time is None:
        latency_s = float("nan")
        reason = "architecture never produces this tier"
    else:
        latency_s = tier_time + tasking_delay_s
        reason = ""
    success = tier_time is not None and latency_s <= thread["latency_tolerance_s"]
    thread_rows.append({
        "Architecture": key,
        "Produces needed tier": tier_time is not None,
        "Latency (s, incl. tasking delay)": latency_s,
        "Tolerance (s)": thread["latency_tolerance_s"],
        "Success": success,
        "Note": reason,
    })

thread_df = pd.DataFrame(thread_rows)
st.dataframe(
    thread_df.style.format({"Latency (s, incl. tasking delay)": "{:.1f}"}, na_rep="N/A"),
    use_container_width=True,
)
st.caption(
    "This is a single-contact-window check (docs/MODEL_REFERENCE.md), not the full multi-week Monte Carlo "
    "in experiments/e11_mission_thread_success.py; it will show far more successes than the real mission-thread "
    "success rate, which also accounts for the wait for the next imaging pass over the target, the wait for the "
    "next usable downlink contact after that, and (for MT-3/MT-4, not shown here) prior-reference availability "
    "and per-pass cadence (docs/TRADE_STUDY.md, docs/V2_VS_V3.md)."
)

st.subheader("Reference frozen data (e03_results.csv)")
# Show a summary from reference
ref_summary = df_ref.groupby("architecture_name")[["tfup_s", "tcp_s"]].mean().reset_index()
st.dataframe(ref_summary, use_container_width=True)

st.caption(
    "Simple analytic model: processing time scales with 1/power, contact capacity = rate * duration /8. "
    "Architectures from src/leo_edge/architectures.py. TFUP/TCP show as NaN and Completed=False when the "
    "product didn't fit in this one contact window, not zero seconds."
)
