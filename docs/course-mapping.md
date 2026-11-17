# Course mapping — how this project operationalizes BİL 420/520

The project is not a side topic: it is a working instance of the semester,
centered on Day 15. Each row says which lecture a piece of the system comes
from, so the design can be defended against the course, not just asserted.

| Lecture | Concept taken | Where it lives in the project |
|---|---|---|
| **Day 15 — Endpoint Security, Hardening & Telemetry** | Prevention / Visibility / Detection / Forensics are four different things; `auditd`, Sysmon, EDR telemetry; "prevention fails eventually, detection is essential"; tampered local logs must be forwarded; detection engineering | The whole spine. Sensor fleet is named after real telemetry sources; `scoring.py` separates visibility from detection; the log-tamper scenario and canary come straight from "local logs can be tampered with or lost" |
| **Day 8 — OWASP Top 10:2025** | **A09 Security Logging & Alerting Failures** — "great logging with no alerting has minimal value"; A01 (Broken Access Control incl. SSRF, path traversal), A04 Cryptographic Failures, A05 Injection, A10 Mishandling of Exceptional Conditions (fail-open) | The thesis (visibility ≠ detection) *is* A09. Every planted vulnerability in `catalog.py` carries its OWASP:2025 id |
| **Day 2 — Adversary, STRIDE, DFD, ATT&CK, Kill Chain** | Trust boundaries, kill-chain stages, lateral movement, STRIDE→ATT&CK mapping | The fleet is a DFD with trust boundaries between subnets; the campaign walks the kill chain across agents; scenarios carry ATT&CK ids |
| **Day 6 — Identity I (MFA)** | Uber 2022: stolen credential → creds found in shares / PowerShell → lateral movement; password hashing (Argon2/bcrypt/scrypt) | The kill-chain's initial access and credential-access stages; an agent stores credentials, one role hashes them weakly on purpose (a crypto failure to find) |
| **Day 3 — Networking for Defenders** | Egress / C2 beaconing is where compromise shows; lateral movement crosses subnet boundaries; SMB 445, DNS exfil | The network sensor and the unexpected-egress rule; the fleet has subnets and a reachability model |
| **Day 9 — Authorization** | IDOR / BOLA / BFLA, mass assignment (`isAdmin=true`) | A privilege-escalation scenario against a role's workload |
| **Day 4 / 5 / 11 — TLS, PKI, Applied Crypto** | Deprecated algorithms, hardcoded keys, "crypto errors don't fail safe — failures stay silent"; mTLS service-to-service | A planted crypto-failure vulnerability; "fails silently" is the same shape as a blinded sensor, which the canary is built to catch |
| **Day 12 — Secrets & Key Management** | Canary secret, secret scanning, SIEM anomaly detection on secret access, assume-breach | The planted canary secret and the credential-file-read rule |
| **Day 13 — Secure SDLC & DevSecOps** | Metrics that measure, not punish: MTTF, false-positive triage, scan coverage | The evaluation metrics: detection latency, false alarms per hour, coverage per sensor |
| **Day 14 — Software Supply Chain** | SBOM, Sigstore/Cosign signing, SLSA, Policy-as-Code (OPA/Rego), pin-by-digest, non-root containers | Detection rules are policy-as-code; the Docker images are hardened; a tampered-image scenario is on the roadmap |

## The one distinction the whole project is built to show

Day 8 (A09) and Day 15 make the same point from two directions, and the
proposal feedback asks for it explicitly:

> A trace in the logs is **visibility**. A rule firing is **detection**. They
> are not the same measurement, and the gap between them is where attackers
> live.

So the system records them as separate facts and reports three outcomes per
attack step: `BLIND` (no sensor saw it), `VISIBLE_ONLY` (a sensor saw it, no
rule fired), `DETECTED` (a rule fired).
