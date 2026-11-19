"""Roles give the fleet its heterogeneity.

Each role runs a different workload and, crucially, a different set of sensors.
That second part is hypothesis H1 made concrete: an EDR host and an
osquery-only workstation see the same attack very differently, so "our fleet is
monitored" is never one claim. Subnets mark the trust boundaries (Day 2/3) the
kill chain has to cross.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Role:
    name: str
    workload: str
    subnet: str
    sensors: tuple[str, ...]
    note: str


ROLES: dict[str, Role] = {
    "edge-web": Role(
        name="edge-web",
        workload="nginx",
        subnet="dmz",
        sensors=("edr", "applog"),
        note="internet-facing; the fleet's front door and usual initial access point",
    ),
    "app": Role(
        name="app",
        workload="gunicorn",
        subnet="app-tier",
        sensors=("auditd", "applog"),
        note="internal app server; no network sensor, so egress here is a blind spot",
    ),
    "db": Role(
        name="db",
        workload="postgres",
        subnet="data-tier",
        sensors=("edr", "auditd"),
        note="holds the canary secret; the crown jewels",
    ),
    "workstation": Role(
        name="workstation",
        workload="outlook",
        subnet="corp",
        sensors=("osquery", "applog"),
        note="employee laptop; coarse telemetry, the weakest-watched role",
    ),
    "domain-controller": Role(
        name="domain-controller",
        workload="lsass",
        subnet="data-tier",
        sensors=("edr", "auditd"),
        note="identity authority; one per fleet",
    ),
    "jump": Role(
        name="jump",
        workload="sshd",
        subnet="app-tier",
        sensors=("auditd",),
        note="bastion used to pivot between tiers",
    ),
    "ai-agent": Role(
        name="ai-agent",
        workload="rag-gateway",
        subnet="app-tier",
        sensors=("edr", "applog"),
        note="an LLM-backed service: holds a provider API key and egresses to "
        "the model all day, so a hijacked agent can hide exfil in that channel",
    ),
}

# Which subnet can open connections into which, i.e. where lateral movement is
# even possible. The kill chain follows these edges: dmz -> app-tier -> data-tier.
REACHABILITY: dict[str, set[str]] = {
    "dmz": {"app-tier"},
    "corp": {"app-tier"},
    "app-tier": {"data-tier"},
    "data-tier": set(),
}


def default_composition() -> dict[str, int]:
    """A ~50-host company. Mostly workstations, a handful of servers, a pair of
    AI-agent gateways, one DC."""
    return {
        "workstation": 22,
        "app": 12,
        "edge-web": 8,
        "db": 4,
        "ai-agent": 2,
        "jump": 1,
        "domain-controller": 1,
    }
