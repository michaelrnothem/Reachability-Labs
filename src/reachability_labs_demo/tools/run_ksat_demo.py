from __future__ import annotations

import argparse
from pathlib import Path

from reachability_labs_demo.ksat_adapter import KSatDemoAdapter
from reachability_labs_demo.plotting import plot_hazard_curve, plot_success_curve, plot_variance_decomposition
from reachability_labs_demo.runtime import SweepConfig, run_sweep


DEFAULT_ALPHAS = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run the flagship random 3-SAT adapter through the Constructive Accessibility Instrument.")
    ap.add_argument("--out", default="demo_run")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--alphas", nargs="+", type=float, default=DEFAULT_ALPHAS)
    ap.add_argument("--trials", type=int, default=24, help="Total branches per alpha.")
    ap.add_argument("--branches-per-instance", type=int, default=3, help="Repeated branches per instance for variance decomposition.")
    ap.add_argument("--pool-size", type=int, default=64)
    ap.add_argument("--sampled", action="store_true", help="Use a mixed sampled proposer (unit-clause aware + random local moves).")
    ap.add_argument("--seed", type=int, default=1)
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    out = Path(args.out)
    adapter = KSatDemoAdapter()
    cfg = SweepConfig(
        n=args.n,
        alphas=args.alphas,
        trials=args.trials,
        branches_per_instance=args.branches_per_instance,
        pool_size=args.pool_size,
        exact_local=not args.sampled,
        base_seed=args.seed,
    )
    _, summary_rows, hazard_rows, variance_rows = run_sweep(adapter, cfg, out)
    plot_success_curve(summary_rows, out / "success_curve.png", title="Flagship 3-SAT adapter: success by alpha")
    alpha_focus = min(summary_rows, key=lambda r: abs(float(r["success_rate"]) - 0.5))["alpha"]
    plot_hazard_curve(hazard_rows, out / "hazard_curve.png", float(alpha_focus), title_prefix="3-SAT hazard profile at alpha")
    plot_variance_decomposition(variance_rows, out / "variance_decomposition.png", title="3-SAT variance decomposition (shown where outcome variance > 0)")
    print(f"[done] wrote 3-SAT instrument outputs to {out}")
    print(f"[info] alpha nearest 50% success: {alpha_focus}")
    if args.sampled:
        print("[note] sampled mode uses a mixed proposer approximation; default exact-local mode is the recommended paper-facing demo.")


if __name__ == "__main__":
    main()
