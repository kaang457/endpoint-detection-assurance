# Benchmarks & statistics

Numbers from a full run of the default fleet:

```bash
PYTHONPATH=src python -m eda.harness --out report
```

Reproducible and deterministic — every step is driven by the harness, so ground
truth is known and the outcomes do not vary between runs. Figures below are the
current build (12-step kill chain, 50-host fleet).

## Fleet under test

| Role | Count | Subnet | Sensors |
|---|---|---|---|
| workstation | 24 | corp | osquery, applog |
| app | 12 | app-tier | auditd, applog |
| edge-web | 8 | dmz | edr, applog |
| db | 4 | data-tier | edr, auditd |
| jump | 1 | app-tier | auditd |
| domain-controller | 1 | data-tier | edr, auditd |
| **Total** | **50** | 4 subnets | 4 sensor types |

## Headline result

| Metric | Value |
|---|---|
| Kill-chain steps scored | 12 |
| **DETECTED** (a rule fired) | **8** |
| **VISIBLE_ONLY** (seen, no alarm) | **1** |
| **BLIND** (no sensor saw it) | **3** |
| False alarms (on 88 benign events) | **0** |
| Beacons that really reached C2 | **3** |

Detection rate is 8/12 = 67%, but the number that matters is the other 4: one
action was visible with no rule to catch it, and three left **no sensor trace at
all** — yet all three beacons still delivered data to the C2 listener. Visibility
is not detection, and detection is not prevention.

## Per-step outcome

| Step | Host | Technique | Saw the effect | Alarm | Outcome |
|---|---|---|---|---|---|
| s1 Initial Access | edge-web | T1059 | edr | R1 | DETECTED |
| s2 Credential Access | edge-web | T1552.001 | edr | R2 | DETECTED |
| s3 Exfiltration | edge-web | T1041 | edr | R3 | DETECTED |
| s4 Discovery | edge-web | T1057 | edr | — | VISIBLE_ONLY |
| s5 Initial Access | workstation | T1059 | osquery | R1 | DETECTED |
| s6 Credential Access | workstation | T1552.001 | — | — | **BLIND** |
| s7 Lateral Movement | app | T1021 | auditd | R1 | DETECTED |
| s8 Exfiltration | app | T1041 | — | — | **BLIND** |
| s9 Lateral Movement | db | T1021 | auditd, edr | R1 | DETECTED |
| s10 Collection | db | T1552.001 | auditd, edr | R2 | DETECTED |
| s11 Defense Evasion | db | T1685.004 | auditd, edr | R4 | DETECTED |
| s12 Exfiltration | db | T1041 | — | — | **BLIND** |

## H1 — coverage differs by sensor

Technique × sensor-type coverage. The rows disagree, so one sensor's coverage
claim never speaks for the fleet.

| Technique | edr | auditd | osquery | applog |
|---|:--:|:--:|:--:|:--:|
| T1059 Command & Scripting | ✓ | ✓ | ✓ | — |
| T1552.001 Credentials in Files | ✓ | ✓ | — | — |
| T1041 Exfiltration over C2 | ✓ | — | — | — |
| T1057 Process Discovery | ✓ | ✓ | ✓ | — |
| T1021 Remote Services | ✓ | ✓ | ✓ | — |
| T1685.004 Disable/Modify Tools | ✓ | ✓ | — | — |

**Shown as scored steps, not only in the matrix:**
- Same exfiltration (T1041): **DETECTED** on the EDR edge host (s3), **BLIND** on
  the auditd-only app host (s8) and the EDR-blinded db (s12).
- Same credential read (T1552.001): **DETECTED** on EDR/auditd hosts (s2, s10),
  **BLIND** on the osquery-only workstation (s6).

## H2 — silent failure beats the status check

After s11 clears logs and blinds the database's EDR:

| Sensor | Status check | Canary probe |
|---|---|---|
| edr | healthy | **SILENT** |
| auditd | healthy | alive |

The naive "is the agent up?" check still trusts the EDR; only probing by result
catches that it has gone dark. In the live console you can watch this happen:
fire s12 before s11 → DETECTED, then fire s11 and s12 again → BLIND.

## H3 — the app log is not detection

| Fact | Count |
|---|---|
| Requests the application logged | 5 |
| Those requests carrying a host effect | 0 |
| Beacons that reached C2 | 3 |

The application log has entries — just none of the host effects (process, file,
network) the intrusion actually caused.

## False-alarm baseline

88 benign events are scripted across the fleet before the attack (ordinary
requests, reads outside the secrets directory, egress to the allowlisted
database). The ruleset fires **0** alarms on them, so every alarm above is a true
positive.

## Test suite

```bash
python -m pytest        # 20 passed
```

20 tests: detection rules, visibility-vs-detection scoring, the H1 contrasts as
scored steps, the H2 silent-failure assertion, the H3 app-log blindness, fleet
composition, and catalog/scenario consistency.
