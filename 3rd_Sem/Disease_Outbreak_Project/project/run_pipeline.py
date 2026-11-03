"""One-command setup for the real-data version of the project.

Example:
    python run_pipeline.py --country India
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(script, *args):
    cmd = [sys.executable, str(ROOT / script), *args]
    print("\n$", " ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--country", default="India")
    a = p.parse_args()
    run("data/download_real_data.py", "--country", a.country)
    run("models/train_forecasting.py")
    print("\nSetup complete. Start the dashboard with:")
    print("streamlit run app/dashboard.py")
