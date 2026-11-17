"""Run the whole thing: drive the kill chain across the fleet and measure it.

This is the single-process path the proposal calls "I run the tests, so ground
truth is known." It needs no server: it builds the fleet in memory, performs
real host actions through the agents, and writes a report plus a dashboard. The
containerized control plane reuses exactly these functions.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .canary_net import CanaryListener
from .events import EventKind, Observation
from .fleet import Fleet
from .report import render
from .scenarios import StepContext, build_killchain
from .scoring import Scoreboard, StepResult, capability_matrix


def _run_benign_baseline(fleet: Fleet) -> tuple[int, int]:
    """Exercise the rules with normal activity they must not fire on: ordinary
    requests, reads outside the secrets dir, egress to the allowlisted database.
    Returns (false_alarms, benign_events). A specific ruleset scores zero here."""
    records = fleet.workspace.data_dir / "records-2026-10.csv"
    false_alarms = 0
    benign_events = 0
    for agent in fleet.agents:
        before_alerts = len(agent.node.alerts)
        before_events = len(agent.node.events)
        agent.node.observe(Observation(EventKind.APP_REQUEST, agent.workload, "/api/home"))
        agent.node.observe(Observation(EventKind.FILE_READ, agent.workload, str(records)))
        agent.node.observe(Observation(EventKind.NETWORK_CONNECT, agent.workload, "db:5432"))
        false_alarms += len(agent.node.alerts) - before_alerts
        benign_events += len(agent.node.events) - before_events
    return false_alarms, benign_events


def run(fleet: Fleet | None = None) -> dict:
    fleet = fleet if fleet is not None else Fleet.build()
    false_alarms, benign_events = _run_benign_baseline(fleet)

    with CanaryListener() as c2:
        ctx = StepContext(workspace=fleet.workspace, c2_host=c2.host, c2_port=c2.port)
        campaign = build_killchain(fleet, ctx)
        db = fleet.first("db")

        board = Scoreboard(false_alarms=false_alarms, benign_events=benign_events)
        for agent, step in campaign:
            start_events = len(agent.node.events)
            start_alerts = len(agent.node.alerts)
            step.perform(agent, ctx)
            board.results.append(
                StepResult(
                    step=step,
                    agent_id=agent.id,
                    sensors_present=agent.role.sensors,
                    events=agent.node.events[start_events:],
                    alerts=agent.node.alerts[start_alerts:],
                )
            )
        beacons_received = len(c2.received)

    # H2: after the log-tamper step blinded the database's EDR, compare the two
    # health views. The status check still trusts it; only the canary caught on.
    silent_failure = {
        "status_check": db.canary.status_check_view(),
        "canary_probe": db.canary.probe(),
    }

    steps = [step for _agent, step in campaign]
    return {
        "fleet": _fleet_summary(fleet),
        "tally": board.tally(),
        "steps": [_step_summary(r) for r in board.results],
        "gaps": [r.step.id for r in board.gaps()],
        "capability_matrix_h1": capability_matrix(steps),
        "silent_failure_h2": silent_failure,
        "applog_blindness_h3": board.h3_applog_blindness(),
        "false_alarms": false_alarms,
        "benign_events": benign_events,
        "beacons_reached_c2": beacons_received,
    }


def _fleet_summary(fleet: Fleet) -> dict:
    by_role: dict[str, int] = {}
    for agent in fleet.agents:
        by_role[agent.role.name] = by_role.get(agent.role.name, 0) + 1
    return {"size": fleet.size, "by_role": by_role}


def _step_summary(result: StepResult) -> dict:
    step = result.step
    return {
        "id": step.id,
        "tactic": step.tactic,
        "name": step.name,
        "agent": result.agent_id,
        "technique": f"{step.technique.id} {step.technique.name}",
        "owasp": step.owasp,
        "course": step.course,
        "effect_kind": step.effect_kind.value,
        "sensors_present": list(result.sensors_present),
        "outcome": result.outcome.value,
        "seen_by": sorted(result.seeing_sensors),
        "alerts": [
            {"rule_id": a.rule_id, "technique": a.technique.id, "message": a.message}
            for a in result.alerts
        ],
        "narrative": step.narrative,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the EDA kill-chain measurement.")
    parser.add_argument("--out", default="report", help="directory for report.json and index.html")
    args = parser.parse_args()

    report = run()
    out_dir = Path(args.out)
    render(report, out_dir)

    tally = report["tally"]
    print(f"fleet: {report['fleet']['size']} agents")
    print(
        f"detected={tally['detected']}  "
        f"visible_only={tally['visible_only']}  "
        f"blind={tally['blind']}  "
        f"false_alarms={report['false_alarms']}"
    )
    print(f"report written to {out_dir / 'index.html'}")


if __name__ == "__main__":
    main()
