# Raw Telemetry Sources & Ingestion Provenance

This directory documents the real-world hydrological telemetry and manual gauge datasets collected for Tamil Nadu river monitoring stations.

## Raw Source Files & Observation Counts

As audited and preserved in `data/raw/cleaning_report.json`:

1. **`rwl_manual_hr_tamil-nadu-sw-gw_27_1991_2020.csv`**
   - Observations: 48 rows
   - Type: Historical manual gauge records
   - Status: Logged and excluded from modeling due to extreme sparsity (2 days of data for 1 station).

2. **`rwl_tel_hr_cwc_009_2021_2025.csv`**
   - Observations: 618,724 rows
   - Type: Automated hourly telemetry from Central Water Commission (CWC) monitoring stations across Tamil Nadu river basins.
   - Status: Primary historical training baseline.

3. **`rwl_tel_hr_cwc_009_2026_2030.csv`**
   - Observations: 20,507 rows
   - Type: CWC telemetry records continuing into 2026.
   - Status: Integrated into continuous chronological sequence.

4. **`rwl_tel_hr_tamil_nadu_sw_gw_27_2026_2030.csv`**
   - Observations: 6,523 rows
   - Type: Tamil Nadu State Surface & Groundwater telemetry monitoring data.
   - Status: Integrated for stations 31–34 (Kamuthi Bridge, Nandambakkam CheckDam, Parthibanur Regulator, Virudhachalam Anicut).

## Ingestion Pipeline Summary
- Resampling onto a uniform 1-hour grid.
- Gaps <= 6 hours linearly interpolated.
- Gaps >= 72 hours treated as hard segment breaks (no bridging, preventing artificial flatlined sequence generation).
- Single-point sensor spikes and sentinel values (<= -500) flagged.
- Resulting clean dataset saved to `data/processed/cleaned_dataset.csv` (906,972 continuous hourly rows).
