"""Turn a run into the measurement the project exists to produce.

The one rule that matters here: visibility and detection are scored from
different facts. Visibility is whether any sensor recorded an event of the
step's host-effect kind. Detection is whether a rule fired. A step can be
visible and undetected; that is not an error in the data, it is the finding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .events import Alert, Event, EventKind
from .scenarios import AttackStep
from .sensors import SENSOR_SPECS


class Outcome(str, Enum):
    DETECTED = "detected"
    VISIBLE_ONLY = "visible_only"
    BLIND = "blind"


@dataclass
class StepResult:
    step: AttackStep
    agent_id: str
    sensors_present: tuple[str, ...]
    events: list[Event]
    alerts: list[Alert]

    @property
    def seeing_sensors(self) -> set[str]:
        """Sensors that recorded the attack's host effect — not its cover-noise
        APP_REQUEST, the effect itself."""
        return {e.sensor for e in self.events if e.kind is self.step.effect_kind}

    @property
    def outcome(self) -> Outcome:
        if self.alerts:
            return Outcome.DETECTED
        if self.seeing_sensors:
            return Outcome.VISIBLE_ONLY
        return Outcome.BLIND

    @property
    def app_logged_a_request(self) -> bool:
        return any(e.kind is EventKind.APP_REQUEST for e in self.events)


@dataclass
class Scoreboard:
    results: list[StepResult] = field(default_factory=list)
    false_alarms: int = 0
    benign_events: int = 0

    def tally(self) -> dict[str, int]:
        counts = {outcome.value: 0 for outcome in Outcome}
        for result in self.results:
            counts[result.outcome.value] += 1
        return counts

    def gaps(self) -> list[StepResult]:
        """The steps a defender would wrongly believe are handled: real activity
        that left a trace but raised no alarm, or none at all."""
        return [r for r in self.results if r.outcome is not Outcome.DETECTED]

    def h3_applog_blindness(self) -> dict[str, int]:
        """H3: the application log carries requests but none of the host effects
        that the attack actually caused."""
        requests = sum(1 for r in self.results if r.app_logged_a_request)
        host_effects_in_applog = sum(
            1
            for r in self.results
            for e in r.events
            if e.sensor == "applog" and e.kind is r.step.effect_kind
        )
        return {
            "requests_logged": requests,
            "host_effects_in_app_log": host_effects_in_applog,
        }


def capability_matrix(steps: list[AttackStep]) -> dict[str, dict[str, bool]]:
    """H1: for each technique in the campaign, which sensor types could even see
    it. The rows differ, which is the whole point — one sensor's coverage claim
    does not speak for the fleet."""
    matrix: dict[str, dict[str, bool]] = {}
    for step in steps:
        row = matrix.setdefault(f"{step.technique.id} {step.technique.name}", {})
        for sensor_name, (_role, covers) in SENSOR_SPECS.items():
            row[sensor_name] = step.effect_kind in covers
    return matrix
