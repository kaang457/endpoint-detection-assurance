# STYLE

How this codebase is written. The first version was set by me (the assistant)
while you were away, so treat §"Decisions made without asking" as a checklist
you can correct in one pass — change any of it and I'll apply the change
everywhere.

## Language & layout
- Python 3.11, `src/` layout, package `eda`. One concept per module, small files.
- `from __future__ import annotations`; modern type hints (`X | None`, `list[...]`).

## Naming
- Domain names, not generic ones: `Observation`, `Event`, `Alert`, `Scoreboard`,
  `seeing_sensors` — never `data`, `result`, `handler`, `manager`.
- Functions are short verb phrases: `observe`, `record`, `blind`, `tally`.

## Structure
- Dataclasses for records (`Event`, `Alert`, `Role`, `AttackStep`); plain classes
  where there is behaviour and state (`Sensor`, `Node`, `Agent`, `Fleet`).
- Detection rules are plain functions `(Event) -> Alert | None`; the engine just
  runs them. Policy lives in the rules, so each is testable alone.
- Handlers stay thin: the FastAPI control plane delegates to `harness.run`.

## Control flow & errors
- Early return / guard clauses over nested `if`. No deep pyramids.
- No swallowed exceptions, no catch-and-rethrow with no context, no universal
  fallbacks. Let real failures surface.

## Comments
- Comment the *why* — a constraint, a hypothesis, a tradeoff — not the *what*.
  Module docstrings say what the file is for and which lecture/hypothesis it
  serves. No narration of what the next line obviously does.

## Tests
- Assert behaviour at the public boundary (the engine, the scoreboard), with
  values known independently — never by recomputing the code's own formula.
- One integration test runs the real campaign on a 3-host fleet.

## Decisions made without asking (please confirm or correct)
1. **Everything in English** (code, comments, docstrings), matching the proposal
   and course materials. Say the word if you want Turkish comments.
2. **Sensors modelled as a coverage+health filter over real observations**,
   rather than integrating real auditd/Falco now. The host *actions* are real;
   the sensor *differences* are modelled. This keeps iteration 1 cross-platform
   and testable; real adapters are roadmap item 1.
3. **Fleet simulated in one process** (not one container per agent yet). Docker
   scales the simulated fleet via `EDA_FLEET_SIZE`; per-agent containers are
   roadmap item 2.
4. **ATT&CK v19 numbering** for log/sensor tampering: `T1685.004` (per your
   feedback; old `T1562.001`/`.012`).
5. **No web framework in the hot path** beyond FastAPI for the control plane;
   the measurement runs as plain Python so tests need no server.
6. **The interactive console is one self-contained HTML string** (`console.py`)
   with vanilla `fetch` against `/live/*` — no bundler, no frontend framework.
   The point is the data, not the toolchain; say the word for a React build.
7. **The live campaign keeps server-side state** (`live.LiveCampaign`, one
   global instance) so firing steps out of order is meaningful (fire the beacon,
   then disable logging, then fire it again). A single global fits a one-user
   demo; per-session state is the move if it ever goes multi-user.
