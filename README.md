# Endpoint Detection Assurance (EDA)

**Do your sensors actually see the attacks that hit your hosts?** This project
measures that instead of assuming it, and it keeps two questions strictly apart:

- **Visibility** — did any sensor record a trace of what happened?
- **Detection** — did a rule fire an alert about it?

An attack can be visible and still undetected. That gap is the whole subject.
It is the point of OWASP:2025 **A09 — "great logging with no alerting has
minimal value"** (Day 8) and of the prevention/visibility/detection split in
Day 15.

## What it does

It stands up a **simulated company fleet of ~50 hosts** — each a lightweight
agent, no real VMs — with **heterogeneous roles** (edge-web, app, db,
workstation, jump, domain-controller) on **subnets that act as trust
boundaries**. Each role runs a different mix of sensors (**EDR / auditd /
osquery / app-log**), so coverage genuinely differs across the fleet.

A **multi-stage kill chain** then walks from a web foothold through a phished
laptop to the database and out to a C2 endpoint. Every step performs a **real
but benign** host action (a real child process, a real read of a planted dummy
secret, a real socket, a real log truncation), so the sensors are measured
against things that actually happened. Each step is scored:

| Outcome | Meaning |
|---|---|
| `DETECTED` | a rule fired |
| `VISIBLE_ONLY` | a sensor saw it, no rule matched — the gap |
| `BLIND` | no sensor saw it |

A current run: **50 agents · 12 steps · 8 detected · 1 visible-only · 3 blind ·
0 false alarms**, and all **3 beacons still reached C2**. The three blind steps
are blind for *different* reasons — an osquery-only laptop can't see a file read
(H1), an app host has no network sensor (H1), and the database's EDR was just
disabled (H2). Full figures in [`BENCHMARKS.md`](BENCHMARKS.md).

### Watch it live

The control plane's home page is an **operator console** (React): its home is
the **fleet** — every simulated VM as a tile grouped by the trust boundary it
sits behind, expandable to what the sensors on it saw. The kill chain lights a
path from the edge inward, and a host breached with no alarm is flagged
`silent`. An *Attack chain* view fires steps one at a time; because state is
kept, you can fire the database beacon (s12), see it **DETECTED**, disable
logging (s11), and fire it again to watch the same action go **BLIND** — H2 by
hand. `Ctrl/Cmd+K` opens a command palette.

## Run it

```bash
# 1) Unit + integration tests (no extra services needed)
pip install -e ".[dev]"
python -m pytest                 # 21 passed

# 2) Build the web UI once (React + Vite; output lands in src/eda/webui)
cd frontend && npm install && npm run build && cd ..

# 3) Serve the control plane — one process serves the UI and the API
uvicorn eda.controlplane:app --reload
# GET /                the operator console (fleet, attack chain, hypotheses)
# GET /live/state      current campaign + per-host fleet state as JSON
# POST /live/fire/{id} fire one step   |  POST /live/reset  |  POST /live/fire-all
# GET /report          the full non-interactive run as JSON
# GET /report.html     the static dashboard
# GET /catalog         the planted vulnerabilities (OWASP:2025 + ATT&CK + lecture)

# Frontend dev with hot reload (optional): proxies the API to :8000
cd frontend && npm run dev       # http://localhost:5173

# Headless measurement without a browser, and the static dashboard:
python -m eda.harness --out report   # -> report/index.html + report.json

# Containerized + scalable
docker compose up --build        # EDA_FLEET_SIZE scales the fleet (default 50)
```

## How the hypotheses show up

- **H1 — coverage differs by sensor.** Shown as scored steps: the same exfil is
  `DETECTED` on the EDR edge host (s3) but `BLIND` on the auditd-only app host
  (s8); the same credential read is `DETECTED` on EDR/auditd hosts but `BLIND`
  on the osquery-only workstation (s6). See the capability matrix in the
  dashboard / `capability_matrix_h1` in the JSON.
- **H2 — silent failure beats the status check.** After logging is disabled on
  the database, the status check still reports the EDR `healthy` while the
  canary reports it `SILENT` (`silent_failure_h2`).
- **H3 — the app log is not detection.** The application logs its requests and
  *none* of the host effects the attack caused (`applog_blindness_h3`).

## Layout

```
src/eda/
  events.py       Observation -> Event -> Alert: the shared vocabulary
  host.py         real, benign host actions (process / file / socket / log)
  sensors.py      sensors with per-type coverage (H1) and a canary health probe (H2)
  detection.py    detection rules + the engine that runs them (policy-as-code)
  node.py         one monitored host: sensors + rules + the event/alert record
  roles.py        roles, their sensor profiles, subnets and reachability
  agent.py        one simulated machine = a node with a role
  fleet.py        the ~50-host fleet and its sandbox
  scenarios.py    the kill chain: real steps tagged with ATT&CK / OWASP / lecture
  scoring.py      visibility-vs-detection scoring (the measurement)
  report.py       report.json + the static dashboard
  harness.py      run the campaign end to end
  live.py         the step-at-a-time campaign + per-host fleet state
  controlplane.py FastAPI service: serves the web UI and the JSON API
  catalog.py      the planted vulnerabilities, indexed to the course
  webui/          the built React console (generated by `npm run build`)
frontend/         the React + Vite source for the console (Vaul, cmdk, sonner,
                  Radix, Base UI, NumberFlow)
docs/course-mapping.md   how each piece maps to a lecture
tests/                    unit + one integration test
```

## Roadmap (easy next iterations)

The code is structured so these are additive, not rewrites:

1. **Real sensors.** `sensors.py` is an interface; swap the coverage model for
   actual auditd / Falco / osquery adapters behind the same `record()`.
2. **One container per agent.** Today the fleet is simulated in one process;
   each agent can become its own hardened container reporting to the control
   plane.
3. **More scenarios.** Add an `AttackStep` (IDOR/BOLA privilege escalation from
   Day 9, a supply-chain tampered image from Day 14, a weak-TLS beacon from
   Day 4). Each new step is one function + one catalog entry.
4. **LLM-agent host.** The proposal's extension: add a hijacked RAG agent as one
   more role whose host effects the endpoint sensor sees but the app log misses.
5. **Real telemetry stack.** Feed events into Prometheus/Loki/Grafana as
   instruments (they are not the contribution).

See `420_proposal.md` for the full proposal and `docs/course-mapping.md` for the
lecture-by-lecture mapping.
