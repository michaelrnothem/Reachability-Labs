from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np

from .gap_profile import GapProfile
from .metadata import PLOT_FOOTER, write_companion_meta


def _finalize(fig: plt.Figure, out_path: str | Path, *, kind: str) -> None:
    fig.text(0.5, 0.01, PLOT_FOOTER, ha="center", va="bottom", fontsize=7, alpha=0.7)
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    write_companion_meta(out_path, {"kind": kind})


def plot_success_curve(summary_rows: Sequence[dict], out_path: str | Path, *, title: str = "Constructive accessibility: success by control parameter", y_label: str = "constructive success") -> None:
    alpha = np.array([float(r["alpha"]) for r in summary_rows])
    sr = np.array([float(r["success_rate"]) for r in summary_rows])
    lo = np.array([float(r["ci_low"]) for r in summary_rows])
    hi = np.array([float(r["ci_high"]) for r in summary_rows])
    fig = plt.figure(figsize=(6, 4))
    plt.plot(alpha, sr, marker="o")
    plt.fill_between(alpha, lo, hi, alpha=0.2)
    plt.xlabel("control parameter")
    plt.ylabel(y_label)
    plt.title(title)
    _finalize(fig, out_path, kind="success_curve")


def plot_hazard_curve(hazard_rows: Sequence[dict], out_path: str | Path, alpha_focus: float | None = None, *, title_prefix: str = "Hazard profile at alpha") -> None:
    if not hazard_rows:
        return
    alphas = sorted({float(r["alpha"]) for r in hazard_rows})
    if alpha_focus is None:
        alpha_focus = alphas[len(alphas) // 2]
    rows = [r for r in hazard_rows if float(r["alpha"]) == alpha_focus]
    steps = np.array([int(r["step"]) for r in rows])
    hazard = np.array([float(r["hazard"]) for r in rows])
    fig = plt.figure(figsize=(6, 4))
    plt.plot(steps, hazard, marker="o")
    plt.xlabel("step")
    plt.ylabel("hazard")
    plt.title(f"{title_prefix}={alpha_focus:g}")
    _finalize(fig, out_path, kind="hazard_curve")


def plot_variance_decomposition(variance_rows: Sequence[dict], out_path: str | Path, *, title: str = "Variance decomposition by control parameter (shown where outcome variance > 0)") -> None:
    alpha = np.array([float(r["alpha"]) for r in variance_rows])
    within = np.array([float(r["within_share"]) if r["within_share"] != "" else np.nan for r in variance_rows])
    between = np.array([float(r["between_share"]) if r["between_share"] != "" else np.nan for r in variance_rows])
    valid = np.isfinite(within) & np.isfinite(between)
    fig = plt.figure(figsize=(6, 4))
    plt.plot(alpha[valid], within[valid], marker="o", label="within-instance share")
    plt.plot(alpha[valid], between[valid], marker="o", label="between-instance share")
    plt.xlabel("control parameter")
    plt.ylabel("share of total Bernoulli variance")
    plt.ylim(0, 1)
    plt.title(title)
    plt.legend()
    _finalize(fig, out_path, kind="variance_decomposition")


def plot_gap_profile(profile: GapProfile, out_path: str | Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].plot(profile.levels, profile.gap)
    axes[0].set_xlabel("viability level s")
    axes[0].set_ylabel("G(s)")
    axes[0].set_title("Gap profile")
    axes[1].plot(profile.levels, profile.forfeiture)
    axes[1].set_xlabel("viability level s")
    axes[1].set_ylabel("forfeiture fraction")
    axes[1].set_title("Normalized forfeiture")
    _finalize(fig, out_path, kind="gap_profile")
