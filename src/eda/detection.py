"""Detection rules and the engine that runs them over recorded Events.

A rule reads only the shape of an Event, never the ground-truth technique the
scenario planted, and assigns its own technique. So a scenario that produces a
visible Event no rule matches comes out VISIBLE_ONLY: a trace in the logs with
no alarm. That case is the one the proposal's feedback asks us to show plainly.

The ruleset is intentionally incomplete. Process-discovery recon (a benign
binary spawned by the web app) is left uncovered on purpose so the gap is real.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import PurePath

from .events import Alert, Event, EventKind, Technique

Rule = Callable[[Event], Alert | None]

SHELL_EXES = {"sh", "bash", "cmd", "powershell", "pwsh", "dash", "zsh"}
SECRET_DIR = "secrets"
# Destinations the org allows outbound. The LLM provider is here because the
# AI-agent hosts talk to it constantly — which is exactly why exfil smuggled
# through that channel does not trip the egress rule (seen, but not detected).
EGRESS_ALLOWLIST = {"db:5432", "llm-gw:443"}


def _rule_service_spawned_shell(event: Event) -> Alert | None:
    # A long-running service workload has no reason to launch a shell; when one
    # appears as a child of the workload it is the classic sign of command
    # execution through an injection flaw (Day 15: anomalous process ancestry).
    if event.kind is not EventKind.PROCESS_SPAWN:
        return None
    if (event.target or "").lower() not in SHELL_EXES:
        return None
    return Alert(
        rule_id="R1-service-spawned-shell",
        technique=Technique("T1059", "Command and Scripting Interpreter"),
        sensor=event.sensor,
        severity="high",
        message=f"{event.actor} spawned a shell: {event.detail.get('argv', event.target)}",
        event=event,
    )


def _rule_secret_file_read(event: Event) -> Alert | None:
    if event.kind is not EventKind.FILE_READ or not event.target:
        return None
    parts = {p.lower() for p in PurePath(event.target).parts}
    if SECRET_DIR not in parts:
        return None
    return Alert(
        rule_id="R2-secret-file-read",
        technique=Technique("T1552.001", "Unsecured Credentials: Credentials In Files"),
        sensor=event.sensor,
        severity="high",
        message=f"read of a credential file: {event.target}",
        event=event,
    )


def _rule_unexpected_egress(event: Event) -> Alert | None:
    if event.kind is not EventKind.NETWORK_CONNECT or not event.target:
        return None
    if event.target in EGRESS_ALLOWLIST:
        return None
    return Alert(
        rule_id="R3-unexpected-egress",
        technique=Technique("T1041", "Exfiltration Over C2 Channel"),
        sensor=event.sensor,
        severity="medium",
        message=f"outbound connection outside the egress allowlist: {event.target}",
        event=event,
    )


def _rule_log_tamper(event: Event) -> Alert | None:
    if event.kind is not EventKind.LOG_TAMPER:
        return None
    return Alert(
        rule_id="R4-log-tamper",
        # ATT&CK v19 (Apr 2026) moved sensor/log tampering here from T1562.
        technique=Technique("T1685.004", "Disable or Modify Tools: Logging"),
        sensor=event.sensor,
        severity="high",
        message=f"logging cleared or disabled: {event.target}",
        event=event,
    )


class DetectionEngine:
    """Runs every rule against each Event. Thin by design: the policy lives in
    the rules, which stay individually testable."""

    def __init__(self, rules: list[Rule]) -> None:
        self._rules = rules

    def evaluate(self, event: Event) -> list[Alert]:
        return [alert for rule in self._rules if (alert := rule(event)) is not None]


def default_rules() -> list[Rule]:
    return [
        _rule_service_spawned_shell,
        _rule_secret_file_read,
        _rule_unexpected_egress,
        _rule_log_tamper,
    ]
