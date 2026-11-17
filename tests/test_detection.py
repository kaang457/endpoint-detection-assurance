"""Each rule is tested at the engine boundary with events we construct, so the
assertions are independent of how the attack produced them."""

from __future__ import annotations

from eda.detection import DetectionEngine, default_rules
from eda.events import Event, EventKind


def _event(kind: EventKind, target: str, actor: str = "nginx") -> Event:
    return Event(sensor="edr", kind=kind, actor=actor, target=target, detail={}, ts=0.0)


def _fired(event: Event) -> list[str]:
    return [a.rule_id for a in DetectionEngine(default_rules()).evaluate(event)]


def test_service_spawning_shell_is_detected_as_t1059():
    alerts = DetectionEngine(default_rules()).evaluate(
        _event(EventKind.PROCESS_SPAWN, "sh")
    )
    assert [a.technique.id for a in alerts] == ["T1059"]


def test_non_shell_process_spawn_has_no_rule():
    # A recon binary is visible but matches nothing: the VISIBLE_ONLY case.
    assert _fired(_event(EventKind.PROCESS_SPAWN, "hostname")) == []


def test_reading_a_secret_file_is_detected():
    assert _fired(_event(EventKind.FILE_READ, "/app/secrets/master.key")) == [
        "R2-secret-file-read"
    ]


def test_reading_an_ordinary_file_is_not_flagged():
    assert _fired(_event(EventKind.FILE_READ, "/app/data/statement.txt")) == []


def test_allowlisted_egress_is_not_flagged():
    assert _fired(_event(EventKind.NETWORK_CONNECT, "db:5432")) == []


def test_unexpected_egress_is_detected_as_exfil():
    assert _fired(_event(EventKind.NETWORK_CONNECT, "127.0.0.1:4444")) == [
        "R3-unexpected-egress"
    ]


def test_log_tampering_uses_the_v19_technique_id():
    alerts = DetectionEngine(default_rules()).evaluate(
        _event(EventKind.LOG_TAMPER, "/var/log/app.log")
    )
    assert [a.technique.id for a in alerts] == ["T1685.004"]
