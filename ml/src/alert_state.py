"""T18 — Persistence/hysteresis alert state machine (docs/ section 4.6):
a level changes only after N consecutive windows above/below the threshold
for that level, so a single noisy minute can't flip the displayed alert
state back and forth (alert fatigue). Reusable by the dashboard/assistant
later (WS6/WS8), not just this evaluation.
"""

import numpy as np
import pandas as pd


class AlertStateMachine:
    LEVELS = ["GREEN", "YELLOW", "ORANGE", "RED"]

    def __init__(self, thresholds: dict, persist_n: int = 15):
        """thresholds: {"yellow": x, "orange": y, "red": z}, strictly increasing."""
        assert thresholds["yellow"] < thresholds["orange"] < thresholds["red"]
        self.thresholds = thresholds
        self.persist_n = persist_n
        self.current_idx = 0
        self._candidate_idx = 0
        self._run_length = 0

    def _level_for_score(self, score: float) -> int:
        if score >= self.thresholds["red"]:
            return 3
        if score >= self.thresholds["orange"]:
            return 2
        if score >= self.thresholds["yellow"]:
            return 1
        return 0

    def update(self, score: float) -> str:
        candidate = self._level_for_score(score)
        if candidate == self._candidate_idx:
            self._run_length += 1
        else:
            self._candidate_idx = candidate
            self._run_length = 1

        if self._run_length >= self.persist_n and candidate != self.current_idx:
            self.current_idx = candidate
            self._run_length = 0

        return self.LEVELS[self.current_idx]


def run_over_series(scores: np.ndarray, thresholds: dict, persist_n: int = 15) -> list[str]:
    machine = AlertStateMachine(thresholds, persist_n)
    return [machine.update(s) for s in scores]


def _self_test():
    """Synthetic sanity check: flat normal -> single noisy spike (should NOT
    escalate) -> sustained rise (SHOULD escalate through the levels)."""
    thresholds = {"yellow": 0.3, "orange": 0.6, "red": 0.85}
    rng = np.random.default_rng(0)

    normal = rng.uniform(0.0, 0.1, size=200)
    single_spike = normal.copy()
    single_spike[100] = 0.95  # one noisy minute — must not flip the alert state

    levels = run_over_series(single_spike, thresholds, persist_n=15)
    assert set(levels) == {"GREEN"}, f"single spike incorrectly escalated: {set(levels)}"

    sustained = np.concatenate([
        np.full(50, 0.05),
        np.full(50, 0.4),
        np.full(50, 0.7),
        np.full(50, 0.95),
    ])
    levels2 = run_over_series(sustained, thresholds, persist_n=15)
    assert levels2[-1] == "RED", f"sustained rise failed to reach RED: {levels2[-1]}"
    assert levels2[0] == "GREEN"
    print("alert_state self-test passed:")
    print(f"  single noisy spike -> stayed {set(levels)} (correct: hysteresis absorbed it)")
    print(f"  sustained rise -> final level {levels2[-1]} (correct: escalated through all levels)")


if __name__ == "__main__":
    _self_test()
