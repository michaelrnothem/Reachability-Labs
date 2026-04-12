from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Protocol, Sequence

from .metadata import provenance, write_companion_meta


@dataclass(frozen=True)
class JudgeOutcome:
    valid: bool
    score: float
    reason: str = ""
    telemetry: Dict[str, float] = field(default_factory=dict)


class Adapter(Protocol):
    name: str

    def make_instance(self, n: int, alpha: float, seed: int) -> Any: ...
    def init_state(self, instance: Any) -> Any: ...
    def step_index(self, state: Any) -> int: ...
    def all_local_moves(self, instance: Any, state: Any) -> List[Any]: ...
    def sample_moves(self, instance: Any, state: Any, rng: random.Random, budget: int) -> List[Any]: ...
    def judge_move(self, instance: Any, state: Any, move: Any) -> JudgeOutcome: ...
    def apply_move(self, instance: Any, state: Any, move: Any) -> Any: ...
    def is_complete(self, instance: Any, state: Any) -> bool: ...
    def is_success(self, instance: Any, state: Any) -> bool: ...
    def receipt_extras(self, instance: Any, state: Any) -> Dict[str, Any]: ...


@dataclass
class TrialResult:
    alpha: float
    n: int
    instance_index: int
    branch_index: int
    trial_index: int
    instance_seed: int
    process_seed: int
    success: bool
    death_step: int | None
    final_step: int
    receipts: List[Dict[str, Any]]


@dataclass
class SweepConfig:
    n: int
    alphas: Sequence[float]
    trials: int = 24
    branches_per_instance: int = 3
    pool_size: int = 64
    exact_local: bool = True
    base_seed: int = 1


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1.0 + z * z / total
    centre = p + z * z / (2 * total)
    radius = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total)
    return ((centre - radius) / denom, (centre + radius) / denom)


def _choose_best(candidates: List[tuple[Any, JudgeOutcome]], rng: random.Random) -> tuple[Any, JudgeOutcome]:
    best_score = min(j.score for _, j in candidates)
    ties = [(m, j) for m, j in candidates if j.score == best_score]
    return rng.choice(ties)


def run_trial_on_instance(
    adapter: Adapter,
    instance: Any,
    alpha: float,
    trial_index: int,
    instance_index: int,
    branch_index: int,
    *,
    pool_size: int,
    exact_local: bool,
    process_seed: int,
) -> TrialResult:
    rng = random.Random(process_seed)
    state = adapter.init_state(instance)
    receipts: List[Dict[str, Any]] = []

    while True:
        step = adapter.step_index(state)
        if adapter.is_complete(instance, state):
            success = adapter.is_success(instance, state)
            return TrialResult(
                alpha,
                instance.n,
                instance_index,
                branch_index,
                trial_index,
                instance.seed,
                process_seed,
                success,
                None if success else step,
                step,
                receipts,
            )

        moves = adapter.all_local_moves(instance, state) if exact_local else adapter.sample_moves(instance, state, rng, pool_size)
        judged = [(mv, adapter.judge_move(instance, state, mv)) for mv in moves]
        valid = [(mv, jr) for mv, jr in judged if jr.valid]

        row = {
            "alpha": alpha,
            "n": instance.n,
            "trial_index": trial_index,
            "instance_index": instance_index,
            "branch_index": branch_index,
            "instance_seed": instance.seed,
            "process_seed": process_seed,
            "step": step,
            "pool_size": len(moves),
            "valid_moves": len(valid),
            "exact_local": int(exact_local),
        }
        row.update(adapter.receipt_extras(instance, state))

        if not valid:
            row.update({
                "chosen_move": "",
                "chosen_score": "",
                "stop_reason": "no_legal_move",
                "success": 0,
            })
            receipts.append(row)
            return TrialResult(
                alpha,
                instance.n,
                instance_index,
                branch_index,
                trial_index,
                instance.seed,
                process_seed,
                False,
                step,
                step,
                receipts,
            )

        move, best = _choose_best(valid, rng)
        state = adapter.apply_move(instance, state, move)
        row.update({
            "chosen_move": repr(move),
            "chosen_score": best.score,
            "stop_reason": "",
            "success": "",
        })
        row.update({f"judge_{k}": v for k, v in best.telemetry.items()})
        receipts.append(row)


def _variance_rows_for_alpha(alpha: float, rows: List[TrialResult]) -> Dict[str, Any]:
    groups: Dict[int, List[int]] = {}
    for r in rows:
        groups.setdefault(r.instance_index, []).append(1 if r.success else 0)
    weights = []
    means = []
    within_terms = []
    total = len(rows)
    for vals in groups.values():
        w = len(vals) / total
        p = sum(vals) / len(vals)
        weights.append(w)
        means.append(p)
        within_terms.append(w * p * (1 - p))
    overall = sum(w * p for w, p in zip(weights, means))
    within_var = sum(within_terms)
    between_var = sum(w * (p - overall) ** 2 for w, p in zip(weights, means))
    total_var = within_var + between_var
    return {
        "alpha": alpha,
        "instances": len(groups),
        "trials": total,
        "overall_success_rate": overall,
        "within_var": within_var,
        "between_var": between_var,
        "total_var": total_var,
        "within_share": (within_var / total_var) if total_var > 0 else "",
        "between_share": (between_var / total_var) if total_var > 0 else "",
    }


def summarize_results(results: Sequence[TrialResult]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    by_alpha: Dict[float, List[TrialResult]] = {}
    for r in results:
        by_alpha.setdefault(r.alpha, []).append(r)

    summary_rows: List[Dict[str, Any]] = []
    hazard_rows: List[Dict[str, Any]] = []
    variance_rows: List[Dict[str, Any]] = []

    for alpha in sorted(by_alpha):
        rs = by_alpha[alpha]
        successes = sum(1 for r in rs if r.success)
        lo, hi = wilson_interval(successes, len(rs))
        death_steps = [r.death_step for r in rs if r.death_step is not None]
        summary_rows.append({
            "alpha": alpha,
            "n": rs[0].n,
            "trials": len(rs),
            "successes": successes,
            "success_rate": successes / len(rs),
            "ci_low": lo,
            "ci_high": hi,
            "mean_death_step": sum(death_steps) / len(death_steps) if death_steps else "",
        })
        variance_rows.append(_variance_rows_for_alpha(alpha, rs))

        max_step = max(r.final_step for r in rs)
        for step in range(max_step + 1):
            alive = sum(1 for r in rs if (r.death_step is None or r.death_step >= step))
            died = sum(1 for r in rs if r.death_step == step)
            if alive == 0:
                continue
            hazard_rows.append({
                "alpha": alpha,
                "step": step,
                "alive": alive,
                "died": died,
                "hazard": died / alive,
            })

    return summary_rows, hazard_rows, variance_rows


def write_csv(rows: Sequence[Dict[str, Any]], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_receipts(results: Sequence[TrialResult], outdir: str | Path) -> None:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for r in results:
        name = f"alpha_{r.alpha:.3f}_inst_{r.instance_index:03d}_branch_{r.branch_index:02d}.csv"
        write_csv(r.receipts, outdir / name)
    (outdir / "_directory.meta.json").write_text(
        json.dumps(provenance({"kind": "receipt_directory", "files": len(list(outdir.glob('*.csv')))}), indent=2),
        encoding="utf-8",
    )


def run_sweep(adapter: Adapter, config: SweepConfig, outdir: str | Path) -> tuple[List[TrialResult], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    outdir = Path(outdir)
    results: List[TrialResult] = []
    for alpha in config.alphas:
        alpha_trial_index = 0
        instance_count = math.ceil(config.trials / max(1, config.branches_per_instance))
        for instance_index in range(instance_count):
            instance_seed = config.base_seed + 10_000 * instance_index + int(round(float(alpha) * 1000))
            instance = adapter.make_instance(n=config.n, alpha=float(alpha), seed=instance_seed)
            for branch_index in range(config.branches_per_instance):
                if instance_index * config.branches_per_instance + branch_index >= config.trials:
                    break
                process_seed = (
                    config.base_seed
                    + 100_000 * instance_index
                    + 1_000 * branch_index
                    + int(round(float(alpha) * 1000))
                    + 7
                )
                results.append(
                    run_trial_on_instance(
                        adapter,
                        instance,
                        float(alpha),
                        alpha_trial_index,
                        instance_index,
                        branch_index,
                        pool_size=config.pool_size,
                        exact_local=config.exact_local,
                        process_seed=process_seed,
                    )
                )
                alpha_trial_index += 1

    summary_rows, hazard_rows, variance_rows = summarize_results(results)
    write_receipts(results, outdir / "receipts")
    write_csv(summary_rows, outdir / "summary_by_alpha.csv")
    write_companion_meta(outdir / "summary_by_alpha.csv", {"kind": "summary_by_alpha"})
    write_csv(hazard_rows, outdir / "hazard_by_alpha.csv")
    write_companion_meta(outdir / "hazard_by_alpha.csv", {"kind": "hazard_by_alpha"})
    write_csv(variance_rows, outdir / "variance_by_alpha.csv")
    write_companion_meta(outdir / "variance_by_alpha.csv", {"kind": "variance_by_alpha"})
    manifest = provenance({
        "adapter": adapter.name,
        "config": asdict(config),
        "results": len(results),
        "sampled_mode_note": (
            "--sampled uses a mixed proposer approximation (unit-clause aware + random local moves); "
            "default exact-local mode is the recommended paper-facing demo."
            if not config.exact_local else "default exact-local mode"
        ),
    })
    (outdir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return results, summary_rows, hazard_rows, variance_rows
