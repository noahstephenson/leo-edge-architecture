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
)

CSV_PATH = repo_root / "results" / "frozen" / "v1" / "e03_results.csv"

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

st.sidebar.header("Simulation Controls")
rate_bps = st.sidebar.slider(
    "Downlink rate (bps)",
    min_value=1_000_000,
    max_value=100_000_000,
    value=10_000_000,
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

arch_map = {
    "A0_GROUND_ONLY": ("GroundOnly", GroundOnly()),
    "A1_COMPRESSED_FULL": ("CompressedFull", CompressedFull()),
    "A2_QUICKLOOK_FIRST": ("QuicklookFirst", QuicklookFirst()),
    "A3_ROI_FIRST": ("RoiFirst", RoiFirst()),
    "A4_PROGRESSIVE": ("Progressive", Progressive()),
    "A5_CONTACT_AWARE": ("ContactAware", ContactAware(alpha=0.2)),
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
    })

res_df = pd.DataFrame(results)
res_df = res_df[["Architecture", "Name", "TFUP_s", "TCP_s", "contact_utilization", "processing_energy_j", "tx_energy_j"]]

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

st.subheader("Reference frozen data (e03_results.csv)")
# Show a summary from reference
ref_summary = df_ref.groupby("architecture_name")[["tfup_s", "tcp_s"]].mean().reset_index()
st.dataframe(ref_summary, use_container_width=True)

st.caption("Simple analytic model: processing time scales with 1/power, contact capacity = rate * duration /8. Architectures from src/leo_edge/architectures.py")
