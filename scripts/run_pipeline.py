"""
Master Orchestration Script for Flood Prediction Pipeline.
Executes data inspection, baseline training, LSTM training,
evaluation, prediction generation, and research plot rendering in sequence.
"""

import subprocess
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

STEPS = [
    ("1. Dataset Profiling", [sys.executable, "scripts/inspect_data.py"]),
    ("2. Baseline Models Training", [sys.executable, "scripts/train_baselines.py"]),
    ("3. Leak-Free LSTM Model Training", [sys.executable, "scripts/train_lstm.py"]),
    ("4. Comparative Evaluation & Metrics Generation", [sys.executable, "scripts/evaluate_all.py"]),
    ("5. Test Predictions & Risk Assessments", [sys.executable, "scripts/generate_predictions.py"]),
    ("6. Research Plot Generation", [sys.executable, "scripts/generate_plots.py"]),
]


def main():
    print("=" * 80)
    print("STARTING END-TO-END FLOOD PREDICTION & DECISION SUPPORT PIPELINE")
    print("=" * 80)

    total_start = time.time()

    for title, cmd in STEPS:
        print(f"\n>>> EXECUTING STEP: {title}")
        print(f"    Command: {' '.join(cmd)}")
        step_start = time.time()
        ret = subprocess.run(cmd)
        if ret.returncode != 0:
            print(f"[FAILED] Step '{title}' exited with error code {ret.returncode}.")
            sys.exit(ret.returncode)
        print(f"    Finished '{title}' in {time.time() - step_start:.2f}s.")

    print("\n" + "=" * 80)
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {time.time() - total_start:.2f}s!")
    print("=" * 80)


if __name__ == "__main__":
    main()
