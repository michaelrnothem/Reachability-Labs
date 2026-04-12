from __future__ import annotations

import argparse
from pathlib import Path

from reachability_labs_demo.gap_profile import compute_gap_profile, load_curves_csv, save_profile
from reachability_labs_demo.plotting import plot_gap_profile


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Compute the existence–reachability gap profile from curve CSV data.")
    ap.add_argument("--csv", required=True, help="CSV with columns alpha,existence,reachability")
    ap.add_argument("--out", default="gap_profile_run")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    alpha, existence, reachability = load_curves_csv(args.csv)
    profile = compute_gap_profile(alpha, existence, reachability)
    save_profile(profile, out / "gap_profile.csv", out / "gap_profile_summary.json")
    plot_gap_profile(profile, out / "gap_profile.png")
    print(f"[done] midpoint gap G(0.5) = {profile.midpoint_gap:.4f}")
    print(f"[done] peak gap = {profile.peak_gap:.4f} at s = {profile.peak_level:.4f}")
    print(f"[done] wrote outputs to {out}")


if __name__ == "__main__":
    main()
