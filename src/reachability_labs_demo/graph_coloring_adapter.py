from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

from .runtime import JudgeOutcome

Move = Tuple[int, int]


@dataclass(frozen=True)
class GraphColorInstance:
    n: int
    alpha: float
    seed: int
    k: int
    edges: Tuple[Tuple[int, int], ...]
    neighbors: Tuple[Tuple[int, ...], ...]
    instance_id: str


@dataclass
class GraphColorState:
    colors: List[int]
    step: int = 0

    def copy(self) -> "GraphColorState":
        return GraphColorState(self.colors.copy(), self.step)


class GraphColoringAdapter:
    name = "graph_coloring"

    def __init__(self, k: int = 3):
        self.k = k

    def make_instance(self, n: int, alpha: float, seed: int) -> GraphColorInstance:
        rng = random.Random(seed)
        max_edges = n * (n - 1) // 2
        m = min(max_edges, max(0, round(alpha * n / 2)))
        all_edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        rng.shuffle(all_edges)
        edges = tuple(sorted(all_edges[:m]))
        nbrs = [[] for _ in range(n)]
        for u, v in edges:
            nbrs[u].append(v)
            nbrs[v].append(u)
        digest = hashlib.sha1(f"{n}|{alpha}|{seed}|{edges}".encode()).hexdigest()[:16]
        return GraphColorInstance(n=n, alpha=alpha, seed=seed, k=self.k, edges=edges, neighbors=tuple(tuple(x) for x in nbrs), instance_id=digest)

    def init_state(self, instance: GraphColorInstance) -> GraphColorState:
        return GraphColorState(colors=[-1] * instance.n, step=0)

    def step_index(self, state: GraphColorState) -> int:
        return state.step

    def _available_colors(self, instance: GraphColorInstance, state: GraphColorState, v: int) -> List[int]:
        used = {state.colors[u] for u in instance.neighbors[v] if state.colors[u] != -1}
        return [c for c in range(instance.k) if c not in used]

    def _unit_vertices(self, instance: GraphColorInstance, state: GraphColorState) -> List[Move]:
        out: List[Move] = []
        for v, c in enumerate(state.colors):
            if c != -1:
                continue
            avail = self._available_colors(instance, state, v)
            if len(avail) == 1:
                out.append((v, avail[0]))
        return out

    def all_local_moves(self, instance: GraphColorInstance, state: GraphColorState) -> List[Move]:
        moves: List[Move] = []
        for v, c in enumerate(state.colors):
            if c != -1:
                continue
            for color in self._available_colors(instance, state, v):
                moves.append((v, color))
        return moves

    def sample_moves(self, instance: GraphColorInstance, state: GraphColorState, rng: random.Random, budget: int) -> List[Move]:
        if budget <= 0:
            return []
        chosen: List[Move] = []
        seen = set()
        unit_moves = self._unit_vertices(instance, state)
        rng.shuffle(unit_moves)
        unit_quota = max(1, budget // 2)
        for mv in unit_moves[:unit_quota]:
            chosen.append(mv)
            seen.add(mv)
        pool = [mv for mv in self.all_local_moves(instance, state) if mv not in seen]
        rng.shuffle(pool)
        for mv in pool:
            if len(chosen) >= budget:
                break
            chosen.append(mv)
        return chosen

    def judge_move(self, instance: GraphColorInstance, state: GraphColorState, move: Move) -> JudgeOutcome:
        v, color = move
        if state.colors[v] != -1:
            return JudgeOutcome(False, float('inf'), 'vertex_already_colored')
        if color not in self._available_colors(instance, state, v):
            return JudgeOutcome(False, float('inf'), 'immediate_conflict')
        trial = state.copy()
        trial.colors[v] = color
        trial.step += 1
        forced_count = 0
        for u, current in enumerate(trial.colors):
            if current != -1:
                continue
            avail = self._available_colors(instance, trial, u)
            if len(avail) == 0:
                return JudgeOutcome(False, float('inf'), 'prefilter_no_color_left', {'vertex': float(u)})
            if len(avail) == 1:
                forced_count += 1
        return JudgeOutcome(True, float(forced_count), telemetry={'unit_after': float(forced_count), 'colored_after': float(trial.step)})

    def apply_move(self, instance: GraphColorInstance, state: GraphColorState, move: Move) -> GraphColorState:
        v, color = move
        new = state.copy()
        new.colors[v] = color
        new.step += 1
        return new

    def is_complete(self, instance: GraphColorInstance, state: GraphColorState) -> bool:
        return state.step >= instance.n

    def is_success(self, instance: GraphColorInstance, state: GraphColorState) -> bool:
        for u, v in instance.edges:
            if state.colors[u] == state.colors[v]:
                return False
        return all(c != -1 for c in state.colors)

    def receipt_extras(self, instance: GraphColorInstance, state: GraphColorState) -> Dict[str, Any]:
        unit_vertices = 0
        legal_total = 0
        for v, color in enumerate(state.colors):
            if color != -1:
                continue
            avail = self._available_colors(instance, state, v)
            legal_total += len(avail)
            if len(avail) == 1:
                unit_vertices += 1
        return {
            'colored_count': state.step,
            'uncolored_count': instance.n - state.step,
            'unit_vertex_count': unit_vertices,
            'available_moves_now': legal_total,
            'instance_id': instance.instance_id,
        }
