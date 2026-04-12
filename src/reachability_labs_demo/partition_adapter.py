from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .runtime import JudgeOutcome

Move = Tuple[int, int]


@dataclass(frozen=True)
class PartitionInstance:
    n: int
    alpha: float
    seed: int
    values: Tuple[int, ...]


@dataclass
class PartitionState:
    side: List[int]
    left_sum: int = 0
    right_sum: int = 0
    step: int = 0


class PartitionAdapter:
    """Lightweight control adapter scaffold.

    This stub exists to make the next adapter step concrete. It is not yet wired
    into a public demo CLI in this release.
    """

    name = 'partition_stub'

    def make_instance(self, n: int, alpha: float, seed: int) -> PartitionInstance:
        raise NotImplementedError('Partition adapter scaffold only; implementation planned in a later release.')

    def init_state(self, instance: PartitionInstance) -> PartitionState:
        return PartitionState(side=[-1] * instance.n)

    def step_index(self, state: PartitionState) -> int:
        return state.step

    def all_local_moves(self, instance: PartitionInstance, state: PartitionState) -> List[Move]:
        raise NotImplementedError

    def sample_moves(self, instance: PartitionInstance, state: PartitionState, rng, budget: int) -> List[Move]:
        raise NotImplementedError

    def judge_move(self, instance: PartitionInstance, state: PartitionState, move: Move) -> JudgeOutcome:
        raise NotImplementedError

    def apply_move(self, instance: PartitionInstance, state: PartitionState, move: Move) -> PartitionState:
        raise NotImplementedError

    def is_complete(self, instance: PartitionInstance, state: PartitionState) -> bool:
        return False

    def is_success(self, instance: PartitionInstance, state: PartitionState) -> bool:
        return False

    def receipt_extras(self, instance: PartitionInstance, state: PartitionState) -> Dict[str, Any]:
        return {'left_sum': state.left_sum, 'right_sum': state.right_sum}
