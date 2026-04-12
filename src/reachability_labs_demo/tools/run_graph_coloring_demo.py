from __future__ import annotations

import argparse
from pathlib import Path

from reachability_labs_demo.graph_coloring_adapter import GraphColoringAdapter
from reachability_labs_demo.plotting import plot_hazard_curve, plot_success_curve, plot_variance_decomposition
from reachability_labs_demo.runtime import SweepConfig, run_sweep

DEFAULT_ALPHAS = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run the experimental graph-coloring adapter demo.")
    ap.add_argument("--out", default="graph_coloring_demo_run")
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--alphas", nargs="+", type=float, default=DEFAULT_ALPHAS, help="Average-degree-like sweep values.")
    ap.add_argument("--trials", type=int, default=18)
    ap.add_argument("--branches-per-instance", type=int, default=3)
    ap.add_argument("--pool-size", type=int, default=48)
    ap.add_argument("--sampled", action="store_true")
    ap.add_argument("--seed", type=int, default=7)
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    out = Path(args.out)
    adapter = GraphColoringAdapter(k=3)
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
    plot_success_curve(summary_rows, out / 'success_curve.png', title='Experimental graph-coloring adapter: success by density', y_label='constructive success')
    alpha_focus = min(summary_rows, key=lambda r: abs(float(r['success_rate']) - 0.5))['alpha']
    plot_hazard_curve(hazard_rows, out / 'hazard_curve.png', float(alpha_focus), title_prefix='Graph-coloring hazard profile at density')
    plot_variance_decomposition(variance_rows, out / 'variance_decomposition.png', title='Graph-coloring variance decomposition (shown where outcome variance > 0)')
    print(f"[done] wrote graph-coloring demo outputs to {out}")
    print(f"[info] density nearest 50% success: {alpha_focus}")
    print('[note] This adapter is experimental but already fits the same runtime, receipts, and diagnostics contract as KSAT.')


if __name__ == '__main__':
    main()
