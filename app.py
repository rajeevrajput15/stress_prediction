import os
import time

import pandas as pd
import streamlit as st

# ============================================================
# PAGE CONFIGURATION (must be the first Streamlit call)
# ============================================================
st.set_page_config(
    page_title="Real-Time Stress Monitoring System",
    page_icon="❤️",
    layout="wide",
)

st.title("❤️ Real-Time Stress Monitoring System")
st.subheader("ESP32 + MAX30102 + GSR + MPU6050 + Temperature Sensor")
st.write("Dashboard based on sensor data stored in stress_data.csv")

# ============================================================
# SIDEBAR: REFRESH CONTROLS
# ============================================================
st.sidebar.header("⚙️ Controls")
auto_refresh = st.sidebar.checkbox("Auto-refresh", value=False)
refresh_secs = st.sidebar.slider("Refresh every (seconds)", 2, 60, 5)
if st.sidebar.button("🔄 Reload now"):
    st.rerun()

# ============================================================
# LOAD CSV (path relative to this file, not the working folder)
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "stress_data.csv")

REQUIRED = [
    "heart_rate", "spo2", "gsr",
    "accel_x", "accel_y", "accel_z",
    "temperature", "stress_level",
]

if not os.path.exists(CSV_FILE):
    st.error("❌ stress_data.csv not found.")
    st.info("Put stress_data.csv in the same folder as app.py.")
    st.stop()

try:
    df = pd.read_csv(CSV_FILE)
except Exception as e:
    st.error(f"Error reading CSV file: {e}")
    st.stop()

# Normalize column names: strip spaces, lowercase
df.columns = df.columns.str.strip().str.lower()

# Fix known header typos (e.g. "aceel_y" -> "accel_y")
df = df.rename(columns={
    "aceel_x": "accel_x",
    "aceel_y": "accel_y",
    "aceel_z": "accel_z",
})

missing = [c for c in REQUIRED if c not in df.columns]
if missing:
    st.error("❌ Missing columns in stress_data.csv:")
    st.write(missing)
    st.write("Columns found in your CSV:")
    st.write(list(df.columns))
    st.stop()

# ============================================================
# CLEAN DATA
# ============================================================
for col in REQUIRED:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=REQUIRED).reset_index(drop=True)

if df.empty:
    st.error("❌ No valid sensor data found in the CSV.")
    st.stop()

df["stress_level"] = df["stress_level"].astype(int)

# ============================================================
# LATEST VALUES
# ============================================================
latest = df.iloc[-1]
STRESS_LABELS = {0: "Low", 1: "Moderate", 2: "High"}
stress_level = int(latest["stress_level"])
stress_status = STRESS_LABELS.get(stress_level, "Unknown")

st.success("🟢 Sensor data loaded successfully")
st.divider()

# ============================================================
# CURRENT READINGS
# ============================================================
st.header("📡 Current Sensor Readings")

c1, c2, c3, c4 = st.columns(4)
c1.metric("❤️ Heart Rate", f"{latest['heart_rate']:.1f} BPM")
c2.metric("🫁 SpO₂", f"{latest['spo2']:.1f} %")
c3.metric("💧 GSR", f"{latest['gsr']:.1f}")
c4.metric("🌡️ Temperature", f"{latest['temperature']:.1f} °C")

st.subheader("🧠 Current Stress Status")
if stress_level == 0:
    st.info("🟢 LOW STRESS")
elif stress_level == 1:
    st.warning("🟡 MODERATE STRESS")
elif stress_level == 2:
    st.error("🔴 HIGH STRESS")
else:
    st.info("Stress level unavailable")

st.write(f"Current stress classification: **{stress_status}**")
st.divider()

# ============================================================
# DATA SUMMARY
# ============================================================
st.header("📊 Data Summary")

s1, s2, s3, s4 = st.columns(4)
s1.metric("Total Samples", len(df))
s2.metric("Avg Heart Rate", f"{df['heart_rate'].mean():.1f} BPM")
s3.metric("Avg SpO₂", f"{df['spo2'].mean():.1f} %")
s4.metric("Avg Temperature", f"{df['temperature'].mean():.1f} °C")

# ============================================================
# SENSOR GRAPHS
# ============================================================
def sensor_chart(title, columns, caption):
    st.divider()
    st.header(title)
    st.line_chart(df[columns])
    st.caption(caption)


sensor_chart("❤️ Heart Rate", ["heart_rate"],
             "Heart rate across recorded samples (BPM).")
sensor_chart("🫁 SpO₂ Level", ["spo2"],
             "Blood oxygen saturation from the MAX30102 sensor (%).")
sensor_chart("💧 GSR / Galvanic Skin Response", ["gsr"],
             "GSR sensor readings across recorded samples.")
sensor_chart("🌡️ Temperature", ["temperature"],
             "Temperature readings across recorded samples (°C).")
sensor_chart("📐 MPU6050 - Accelerometer (X, Y, Z)",
             ["accel_x", "accel_y", "accel_z"],
             "MPU6050 accelerometer readings on all three axes.")

# ============================================================
# MAIN STRESS MONITORING (LAST 4 SAMPLES)
# ============================================================
st.divider()
st.header("🧠 MAIN STRESS LEVEL MONITORING")

last_four = df.tail(4).copy()
last_four["Sample"] = [f"#{i + 1}" for i in last_four.index]
last_four["Stress Status"] = last_four["stress_level"].map(STRESS_LABELS).fillna("Unknown")

st.write("### Last 4 Sensor Inputs")

display = last_four[
    ["Sample", "heart_rate", "spo2", "gsr", "temperature",
     "stress_level", "Stress Status"]
].rename(columns={
    "heart_rate": "Heart Rate (BPM)",
    "spo2": "SpO₂ (%)",
    "gsr": "GSR",
    "temperature": "Temperature (°C)",
    "stress_level": "Stress Level",
})
st.dataframe(display, hide_index=True)

st.write("### 📈 Stress Level - Last 4 Inputs")
stress_chart = last_four.set_index("Sample")[["stress_level"]].rename(
    columns={"stress_level": "Stress"}
)
st.line_chart(stress_chart)
st.caption("Stress level: 0 = Low | 1 = Moderate | 2 = High")

st.subheader("📋 Detailed Last 4 Sensor Readings")
st.dataframe(last_four[REQUIRED], hide_index=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("❤️ Real-Time Stress Monitoring System | ESP32 + MAX30102 + GSR + MPU6050")

# ============================================================
# AUTO-REFRESH (keep at the very end of the script)
# ============================================================
if auto_refresh:
    time.sleep(refresh_secs)
    st.rerun()
