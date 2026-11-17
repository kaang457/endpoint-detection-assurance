# Endpoint Detection Assurance: What Do Sensors Really See?
### From Classic Attacks to a Monitored Fleet, Beyond the Logs

**Author:** Kaan ⟨Soyad⟩ · Student No: ⟨Öğrenci No⟩
**Course:** BİL 420/520 — Introduction to Cybersecurity
**Type:** Practical application

> NOT: Soyad ve öğrenci numarası yer tutucu olarak bırakıldı (`⟨Soyad⟩`,
> `⟨Öğrenci No⟩`). Teslimden önce doldurulmalı.

---

## Motivation

Defenders deploy sensors and rules and then *assume* they work, while attackers
live in the gaps: uncovered techniques, silent failures, disabled logging
(ATT&CK **T1685** *Disable or Modify Tools*). I treat detection as a control
that must itself be monitored — "you cannot defend what you do not monitor, and
you cannot trust monitoring you never measure."

This is exactly the point the course makes twice. **Day 15 (Endpoint Security &
Telemetry)** separates *prevention*, *visibility*, *detection* and *forensics*
as four different things and warns that prevention eventually fails, so
detection is what remains. **Day 8 (OWASP Top 10:2025)** makes **A09 Security
Logging & Alerting Failures** its own category with the line *"great logging
with no alerting has minimal value."* The project turns that sentence into a
measurement.

## The distinction this project is built to measure

Following the proposal feedback, the two are kept strictly apart and never
conflated:

- **Visibility** — an attack left a trace that *some sensor recorded*.
- **Detection** — a *rule fired an alert* about it.

Every attack step is scored into one of three outcomes:

| Outcome | Meaning |
|---|---|
| `DETECTED` | a rule fired |
| `VISIBLE_ONLY` | a sensor recorded it, but no rule matched — the dangerous gap |
| `BLIND` | no sensor recorded it at all |

## System under test

A **simulated company fleet of ~50 hosts**, each a lightweight *agent* (no real
VMs or hypervisor needed). Agents are heterogeneous by **role** — edge web
servers, internal app servers, databases, workstations, a jump host and a
domain controller — spread across **subnets that act as trust boundaries**
(Day 2/3). Each role runs a *different* set of sensors drawn from the real
telemetry sources in Day 15 (**EDR**, **auditd**, **osquery**, the
**application log**), so coverage genuinely differs across the fleet.

The fleet carries **intentional vulnerabilities**, each tagged with its
OWASP:2025 category and the ATT&CK technique used against it (see
`src/eda/catalog.py`). A **multi-stage kill chain** (Day 2; shaped after the
Uber 2022 breach in Day 6) walks from a web-tier foothold to credential theft,
reconnaissance, lateral movement across subnets, reading the database's canary
secret, disabling logging, and exfiltration to a C2 endpoint. Because the
harness runs every step, **ground truth is known**.

Everything is packaged with **Docker** so the fleet size scales from one env
var; detection rules are written as code (the Day 14 *policy-as-code* idea), and
the images are hardened (non-root, read-only root fs, dropped capabilities).

## Hypotheses

- **H1** — Open-source sensors (auditd, osquery, EDR/Falco-class) differ
  strongly in which ATT&CK techniques they can see, so one sensor's coverage
  claim does not speak for the fleet. *Shown as scored steps: the same
  exfiltration lands `DETECTED` on the EDR edge host and `BLIND` on the
  auditd-only app host, and the same credential read is `DETECTED` on the
  EDR/auditd hosts but `BLIND` on the osquery-only workstation.*
- **H2** — A silently failed or blinded sensor is caught sooner by a **canary
  event** than by a status check. *Shown after the log-tamper step: the status
  check still reports the EDR "healthy" while the canary reports it `SILENT`.*
- **H3** — The effects of the intrusion (process, file, network) are missing
  from application logs but visible to endpoint sensors. *Shown by the app log
  holding only benign requests while the host effects appear only in EDR/auditd.*

## Method

In an isolated environment, each kill-chain step performs a **real but benign**
host action (a real child process, a real read of a planted dummy secret, a
real socket to a canary C2, a real log truncation). Sensors record what they
cover while healthy; a canary probes their health by result. Each sensor's
output is scored against ground truth. Normal activity is scripted to establish
a false-alarm baseline. (Prometheus/Loki/Grafana remain *instruments*, not the
contribution; the current build reports directly.)

## Evaluation

Per-sensor technique coverage (H1 matrix), detected / visible-only / blind
counts, **false alarms** (currently 0 against an 88-event scripted baseline),
detection vs. silent-failure latency, and whether the intrusion can be
reconstructed from the logs. The current build scores a 12-step kill chain
across 50 hosts as **8 detected · 1 visible-only · 3 blind**, with all 3 beacons
still reaching C2 (see `BENCHMARKS.md`). Metrics follow the Day 13 principle:
*measure to improve, not to punish.*

## Scope and ethics

Defensive only; isolated sandbox; no real malware and no new exploit code. The
attacks touch only planted dummy files and a **canary secret**, never anything
real (Day 12).

## Timeline

15 Oct pitch; 2 Nov core measurements; 19 Nov mid review (core only); 29 Nov
extension; 1 and 3 Dec demo; 5 Dec report. Fallback: if a sensor will not run,
drop to auditd + osquery. The LLM-agent extension (a hijacked RAG agent as one
more host in the fleet, its effects visible to the endpoint sensor but missing
from application logs) is cut first if it lags on 20 Nov.

---

*Build status and how to run: see `README.md`. Lecture-by-lecture mapping of the
design: see `docs/course-mapping.md`.*
