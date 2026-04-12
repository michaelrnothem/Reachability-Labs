from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from .metadata import provenance, write_companion_meta


@dataclass
class GapProfile:
    levels: np.ndarray
    alpha_e: np.ndarray
    alpha_r: np.ndarray
    gap: np.ndarray
    forfeiture: np.ndarray
    midpoint_gap: float
    peak_gap: float
    peak_level: float
    area: float
    centroid: float


def monotone_nonincreasing(y: Sequence[float]) -> np.ndarray:
    arr = np.asarray(y, dtype=float).copy()
    for i in range(1, len(arr)):
        arr[i] = min(arr[i - 1], arr[i])
    return arr


def alpha_at_level(alpha: Sequence[float], curve: Sequence[float], level: float) -> float:
    x = np.asarray(alpha, dtype=float)
    y = monotone_nonincreasing(curve)
    if level > y[0] or level < y[-1]:
        raise ValueError(f"level {level} is outside the curve range [{y[-1]}, {y[0]}]")
    idx = np.where(y >= level)[0]
    right = idx[-1]
    if right == len(y) - 1 or y[right] == level:
        return float(x[right])
    x0, x1 = x[right], x[right + 1]
    y0, y1 = y[right], y[right + 1]
    if y0 == y1:
        return float(x0)
    t = (level - y0) / (y1 - y0)
    return float(x0 + t * (x1 - x0))


def compute_gap_profile(alpha: Sequence[float], existence: Sequence[float], reachability: Sequence[float], *, levels: Iterable[float] | None = None, alpha0: float | None = None) -> GapProfile:
    alpha = np.asarray(alpha, dtype=float)
    existence = monotone_nonincreasing(existence)
    reachability = monotone_nonincreasing(reachability)
    low = max(existence[-1], reachability[-1])
    high = min(existence[0], reachability[0])
    levels = np.asarray(list(levels) if levels is not None else np.linspace(low, high, 101), dtype=float)
    alpha_e = np.array([alpha_at_level(alpha, existence, s) for s in levels])
    alpha_r = np.array([alpha_at_level(alpha, reachability, s) for s in levels])
    gap = alpha_e - alpha_r
    baseline = float(alpha[0] if alpha0 is None else alpha0)
    denom = np.maximum(alpha_e - baseline, 1e-12)
    forfeiture = gap / denom
    midpoint_gap = alpha_at_level(alpha, existence, 0.5) - alpha_at_level(alpha, reachability, 0.5)
    peak_idx = int(np.argmax(gap))
    area = float(np.trapezoid(gap, levels))
    gap_sum = float(np.trapezoid(gap, levels))
    centroid = float(np.trapezoid(levels * gap, levels) / gap_sum) if gap_sum > 0 else float(levels.mean())
    return GapProfile(levels, alpha_e, alpha_r, gap, forfeiture, float(midpoint_gap), float(gap[peak_idx]), float(levels[peak_idx]), area, centroid)


def load_curves_csv(path: str | Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = []
    with Path(path).open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows.extend(reader)
    alpha = np.array([float(r["alpha"]) for r in rows], dtype=float)
    existence = np.array([float(r["existence"]) for r in rows], dtype=float)
    reachability = np.array([float(r["reachability"]) for r in rows], dtype=float)
    return alpha, existence, reachability


def save_profile(profile: GapProfile, out_csv: str | Path, out_json: str | Path) -> None:
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["level", "alpha_e", "alpha_r", "gap", "forfeiture"])
        writer.writeheader()
        for s, ae, ar, g, frac in zip(profile.levels, profile.alpha_e, profile.alpha_r, profile.gap, profile.forfeiture):
            writer.writerow({"level": s, "alpha_e": ae, "alpha_r": ar, "gap": g, "forfeiture": frac})
    write_companion_meta(out_csv, {"kind": "gap_profile_curve"})
    summary = provenance({
        "kind": "gap_profile_summary",
        "midpoint_gap": profile.midpoint_gap,
        "peak_gap": profile.peak_gap,
        "peak_level": profile.peak_level,
        "area": profile.area,
        "centroid": profile.centroid,
    })
    Path(out_json).write_text(json.dumps(summary, indent=2), encoding="utf-8")
