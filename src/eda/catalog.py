"""The planted vulnerabilities, as a catalog tied back to the course.

Each entry is a weakness the fleet carries on purpose, named with its
OWASP:2025 category (Day 8), the ATT&CK technique an attacker uses against it,
and the lecture it comes from. The scenarios exercise these; this list is the
readable index a reviewer can check the project's coverage against.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Vulnerability:
    id: str
    name: str
    owasp_2025: str
    attack: str
    course: str
    where: str
    note: str


CATALOG: list[Vulnerability] = [
    Vulnerability(
        "V1", "Command injection in a report endpoint",
        "A05 Injection", "T1059 Command and Scripting Interpreter", "Day 8/10/15",
        "edge-web workload",
        "User input reaches a shell, so the web process spawns a child shell.",
    ),
    Vulnerability(
        "V2", "Credentials in a world-readable file",
        "A04 Cryptographic Failures", "T1552.001 Credentials In Files", "Day 6/11/12",
        "edge-web and db hosts",
        "A secret is stored on disk, weakly protected; reading it is trivial.",
    ),
    Vulnerability(
        "V3", "No alerting on reconnaissance",
        "A09 Security Logging & Alerting Failures", "T1057 Process Discovery", "Day 2/15",
        "detection ruleset",
        "A recon binary is logged by sensors but matches no rule — visible, no alarm.",
    ),
    Vulnerability(
        "V4", "Flat network allows lateral movement",
        "A01 Broken Access Control", "T1021 Remote Services", "Day 2/3",
        "subnet reachability",
        "Trust boundaries are crossable from the DMZ inward to the data tier.",
    ),
    Vulnerability(
        "V5", "Unmonitored egress on the app tier",
        "A01 Broken Access Control (SSRF)", "T1041 Exfiltration Over C2 Channel", "Day 3/10",
        "app role sensors",
        "App hosts run no network sensor, so outbound C2 traffic is a blind spot.",
    ),
    Vulnerability(
        "V6", "Logging can be disabled locally",
        "A09 Security Logging & Alerting Failures", "T1685.004 Disable or Modify Tools", "Day 15",
        "node log + EDR health",
        "Clearing logs and blinding the agent is detectable only if something "
        "probes by result (the canary), not by self-reported status.",
    ),
    Vulnerability(
        "V7", "Coarse telemetry on employee laptops",
        "A09 Security Logging & Alerting Failures", "T1552.001 Credentials In Files", "Day 15",
        "workstation role sensors",
        "Workstations run only process-granularity osquery, so a credential "
        "file read that an EDR host detects is completely blind here (H1).",
    ),
]


def catalog_as_dicts() -> list[dict]:
    return [asdict(v) for v in CATALOG]
