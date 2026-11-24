import numpy as np
import pandas as pd
from pathlib import Path

# 1. Setup file paths cleanly
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "simulated_pump_logs.csv"
REPORT_PATH = BASE_DIR / "output" / "pump_anomaly_report.xlsx"

# 2. Generate 500 hours of synthetic centrifugal pump sensor readings
np.random.seed(42)
hours = 500
timestamps = pd.date_range(start="2026-11-01 00:00:00", periods=hours, freq="h")

df = pd.DataFrame({
    "timestamp": timestamps,
    "pump_id": "PUMP-01A",
    "bearing_temp_c": np.random.normal(loc=58.0, scale=2.5, size=hours),
    "vibration_mm_s": np.random.normal(loc=2.1, scale=0.3, size=hours),
    "motor_current_a": np.random.normal(loc=42.0, scale=1.5, size=hours),
})

# 3. Inject realistic mechanical faults (bearing wear + cavitation spike)
df.loc[380:, "bearing_temp_c"] += np.linspace(0, 24, hours - 380)
df.loc[380:, "vibration_mm_s"] += np.linspace(0, 4.8, hours - 380)
df.loc[142:145, "vibration_mm_s"] += 5.5
df.loc[142:145, "motor_current_a"] += 11.0

df.to_csv(DATA_PATH, index=False)

# 4. Flag anomalies using ISO vibration & thermal thresholds
df["vib_alarm"] = df["vibration_mm_s"] > 4.5
df["temp_alarm"] = df["bearing_temp_c"] > 75.0
df["status"] = np.where(df["vib_alarm"] | df["temp_alarm"], "CRITICAL_FAULT", "NORMAL")

# 5. Export summary & fault logs to a multi-sheet Excel report
faults_df = df[df["status"] == "CRITICAL_FAULT"].copy()
summary_df = pd.DataFrame({
    "Metric": ["Total Operating Hours", "Critical Fault Hours", "Max Vibration (mm/s)", "Max Bearing Temp (C)"],
    "Value": [
        len(df),
        len(faults_df),
        round(df["vibration_mm_s"].max(), 2),
        round(df["bearing_temp_c"].max(), 2),
    ]
})

with pd.ExcelWriter(REPORT_PATH, engine="openpyxl") as writer:
    summary_df.to_excel(writer, sheet_name="Executive_Summary", index=False)
    faults_df.to_excel(writer, sheet_name="Fault_Logs", index=False)
    df.to_excel(writer, sheet_name="Raw_Telemetry", index=False)

print(f"Pipeline complete! Detected {len(faults_df)} critical fault hours.")
print(f"Excel report saved to: {REPORT_PATH}")