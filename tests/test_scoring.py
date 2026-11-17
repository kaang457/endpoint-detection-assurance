"""The scoring layer's one job is to keep visibility and detection apart. These
tests pin that: the same events with and without an alert must score differently,
and an event of the wrong kind must not count as seeing the attack."""

from __future__ import annotations

from eda.events import Alert, Event, EventKind, Technique
from eda.scenarios import AttackStep
from eda.scoring import Outcome, StepResult, capability_matrix


def _step(effect_kind: EventKind) -> AttackStep:
    return AttackStep(
        id="t", tactic="Test", name="test step",
        technique=Technique("T0000", "Test"), effect_kind=effect_kind,
        owasp="A00", course="Day 0", narrative="",
        perform=lambda agent, ctx: None,
    )


def _event(kind: EventKind, sensor: str = "edr") -> Event:
    return Event(sensor=sensor, kind=kind, actor="nginx", target="x", detail={}, ts=0.0)


def _result(step: AttackStep, events: list[Event], alerts: list[Alert]) -> StepResult:
    return StepResult(step=step, agent_id="a", sensors_present=("edr",), events=events, alerts=alerts)


def test_alert_makes_the_step_detected():
    step = _step(EventKind.PROCESS_SPAWN)
    event = _event(EventKind.PROCESS_SPAWN)
    alert = Alert("R1", Technique("T1059", "x"), "edr", "high", "", event)
    assert _result(step, [event], [alert]).outcome is Outcome.DETECTED


def test_trace_without_alert_is_visible_only():
    step = _step(EventKind.PROCESS_SPAWN)
    assert _result(step, [_event(EventKind.PROCESS_SPAWN)], []).outcome is Outcome.VISIBLE_ONLY


def test_no_event_of_the_effect_kind_is_blind():
    step = _step(EventKind.NETWORK_CONNECT)
    # An app-request log entry is present but it is not the attack's host effect.
    assert _result(step, [_event(EventKind.APP_REQUEST, "applog")], []).outcome is Outcome.BLIND


def test_capability_matrix_rows_disagree_h1():
    step = _step(EventKind.NETWORK_CONNECT)
    row = capability_matrix([step])["T0000 Test"]
    assert row["edr"] is True and row["auditd"] is False
