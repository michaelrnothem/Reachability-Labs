from __future__ import annotations

import json
import random
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Dict, List, Tuple

from .runtime import JudgeOutcome


def _lit_satisfied(val01: int, lit: int) -> bool:
    return val01 == 1 if lit > 0 else val01 == 0


@dataclass(frozen=True)
class KSatInstance:
    n: int
    m: int
    alpha: float
    seed: int
    clauses: Tuple[Tuple[int, int, int], ...]
    var_occ: Tuple[Tuple[Tuple[int, int], ...], ...]
    instance_id: str


@dataclass
class KSatState:
    assignment: List[int]
    clause_num_unassigned: List[int]
    clause_num_true: List[int]
    satisfied_count: int
    unit_unsat_count: int
    step: int

    def copy(self) -> "KSatState":
        return KSatState(
            assignment=list(self.assignment),
            clause_num_unassigned=list(self.clause_num_unassigned),
            clause_num_true=list(self.clause_num_true),
            satisfied_count=self.satisfied_count,
            unit_unsat_count=self.unit_unsat_count,
            step=self.step,
        )


class KSatDemoAdapter:
    name = "ksat_paper_demo"

    def make_instance(self, n: int, alpha: float, seed: int) -> KSatInstance:
        rng = random.Random(seed)
        m = max(1, int(round(alpha * n)))
        clauses: List[Tuple[int, int, int]] = []
        for _ in range(m):
            vs = rng.sample(range(1, n + 1), 3)
            clauses.append(tuple((1 if rng.random() < 0.5 else -1) * v for v in vs))
        occ: List[List[Tuple[int, int]]] = [[] for _ in range(n)]
        for ci, clause in enumerate(clauses):
            for lit in clause:
                occ[abs(lit) - 1].append((ci, lit))
        payload = json.dumps({"n": n, "m": m, "seed": seed, "clauses": clauses}, sort_keys=True).encode("utf-8")
        return KSatInstance(n, m, alpha, seed, tuple(clauses), tuple(tuple(x) for x in occ), sha256(payload).hexdigest()[:16])

    def init_state(self, instance: KSatInstance) -> KSatState:
        return KSatState(
            assignment=[-1] * instance.n,
            clause_num_unassigned=[3] * instance.m,
            clause_num_true=[0] * instance.m,
            satisfied_count=0,
            unit_unsat_count=0,
            step=0,
        )

    def step_index(self, state: KSatState) -> int:
        return state.step

    def all_local_moves(self, instance: KSatInstance, state: KSatState) -> List[Tuple[int, int]]:
        out: List[Tuple[int, int]] = []
        for i, val in enumerate(state.assignment):
            if val == -1:
                out.append((i, 0))
                out.append((i, 1))
        return out

    def _unit_clause_moves(self, instance: KSatInstance, state: KSatState) -> List[Tuple[int, int]]:
        moves: List[Tuple[int, int]] = []
        seen = set()
        for ci, clause in enumerate(instance.clauses):
            if state.clause_num_true[ci] > 0 or state.clause_num_unassigned[ci] != 1:
                continue
            forced_lit = None
            for lit in clause:
                vi = abs(lit) - 1
                if state.assignment[vi] == -1:
                    forced_lit = lit
                    break
            if forced_lit is None:
                continue
            move = (abs(forced_lit) - 1, 1 if forced_lit > 0 else 0)
            if move not in seen:
                seen.add(move)
                moves.append(move)
        return moves

    def sample_moves(self, instance: KSatInstance, state: KSatState, rng: random.Random, budget: int) -> List[Tuple[int, int]]:
        # Public-demo simplification: we enumerate all local moves before sampling from them.
        # This preserves the mixed proposer idea (unit-clause-aware + random local moves)
        # without optimizing for large-n performance.
        if budget <= 0:
            return []
        chosen: List[Tuple[int, int]] = []
        seen = set()
        unit_moves = self._unit_clause_moves(instance, state)
        rng.shuffle(unit_moves)
        unit_quota = max(1, budget // 2)
        for mv in unit_moves[:unit_quota]:
            chosen.append(mv)
            seen.add(mv)
        random_pool = [mv for mv in self.all_local_moves(instance, state) if mv not in seen]
        rng.shuffle(random_pool)
        for mv in random_pool:
            if len(chosen) >= budget:
                break
            chosen.append(mv)
        return chosen

    def judge_move(self, instance: KSatInstance, state: KSatState, move: Tuple[int, int]) -> JudgeOutcome:
        var_idx0, val01 = move
        if state.assignment[var_idx0] != -1:
            return JudgeOutcome(False, float("inf"), "var_already_assigned")
        for ci, lit in instance.var_occ[var_idx0]:
            if state.clause_num_true[ci] > 0:
                continue
            if state.clause_num_unassigned[ci] == 1 and not _lit_satisfied(val01, lit):
                return JudgeOutcome(False, float("inf"), "prefilter_unit_clause_falsified", {"clause_idx": float(ci)})

        delta_unit = 0
        delta_satisfied = 0
        for ci, lit in instance.var_occ[var_idx0]:
            before_true = state.clause_num_true[ci]
            before_un = state.clause_num_unassigned[ci]
            before_sat = before_true > 0
            before_unit = before_true == 0 and before_un == 1
            after_un = before_un - 1
            after_true = before_true + (1 if _lit_satisfied(val01, lit) else 0)
            after_sat = after_true > 0
            after_unit = after_true == 0 and after_un == 1
            delta_unit += (1 if after_unit else 0) - (1 if before_unit else 0)
            delta_satisfied += (1 if after_sat else 0) - (1 if before_sat else 0)

        unit_after = state.unit_unsat_count + delta_unit
        sat_after = state.satisfied_count + delta_satisfied
        return JudgeOutcome(True, float(unit_after), telemetry={
            "unit_after": float(unit_after),
            "unit_delta": float(delta_unit),
            "satisfied_after": float(sat_after),
            "occurrences": float(len(instance.var_occ[var_idx0])),
        })

    def apply_move(self, instance: KSatInstance, state: KSatState, move: Tuple[int, int]) -> KSatState:
        var_idx0, val01 = move
        new = state.copy()
        new.assignment[var_idx0] = val01
        new.step += 1
        for ci, lit in instance.var_occ[var_idx0]:
            before_true = new.clause_num_true[ci]
            before_un = new.clause_num_unassigned[ci]
            before_sat = before_true > 0
            before_unit = before_true == 0 and before_un == 1
            new.clause_num_unassigned[ci] = before_un - 1
            if _lit_satisfied(val01, lit):
                new.clause_num_true[ci] = before_true + 1
            after_true = new.clause_num_true[ci]
            after_un = new.clause_num_unassigned[ci]
            after_sat = after_true > 0
            after_unit = after_true == 0 and after_un == 1
            new.unit_unsat_count += (1 if after_unit else 0) - (1 if before_unit else 0)
            new.satisfied_count += (1 if after_sat else 0) - (1 if before_sat else 0)
        return new

    def is_complete(self, instance: KSatInstance, state: KSatState) -> bool:
        return state.step >= instance.n

    def is_success(self, instance: KSatInstance, state: KSatState) -> bool:
        return state.satisfied_count == instance.m

    def receipt_extras(self, instance: KSatInstance, state: KSatState) -> Dict[str, Any]:
        return {
            "assigned_count": state.step,
            "unassigned_count": instance.n - state.step,
            "satisfied_fraction": state.satisfied_count / instance.m,
            "unit_unsat_count": state.unit_unsat_count,
            "instance_id": instance.instance_id,
        }
