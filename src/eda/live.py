"""A live, step-at-a-time campaign for the interactive console.

The harness runs the whole kill chain at once and reports. This runs the same
steps, but one at a time and on demand, so the console can answer the question
the project is really about: you fire one malicious action and watch whether an
alarm comes back, or whether it stays silent.

State is deliberately kept: firing the log-tamper step blinds the database's
EDR, so firing the exfiltration step *before* versus *after* it gives different
outcomes. That ordering is the H2 demonstration made interactive — fire the
beacon, see DETECTED; disable logging; fire the same beacon, see BLIND.
"""

from __future__ import annotations

from .agent import Agent
from .canary_net import CanaryListener
from .fleet import Fleet
from .harness import _run_benign_baseline
from .scenarios import AttackStep, StepContext, build_killchain
from .scoring import Scoreboard, StepResult, capability_matrix


def _agent_status(steps: list[dict]) -> str:
    """A VM's state, worst-case over the attack steps that targeted it. The order
    matters: a host where the attack went unseen ("silent") outranks one that
    merely raised alerts, because an undetected breach is the dangerous state."""
    if not steps:
        return "nominal"
    outcomes = {s["outcome"] for s in steps if s["fired"]}
    if not outcomes:
        return "targeted"
    if "blind" in outcomes:
        return "silent"
    if "detected" in outcomes:
        return "alerting"
    if "visible_only" in outcomes:
        return "observed"
    return "targeted"


class LiveCampaign:
    """One running fleet plus the ordered kill chain, fired on demand."""

    def __init__(self, composition: dict[str, int] | None = None) -> None:
        self.fleet = Fleet.build(composition)
        self.false_alarms, self.benign_events = _run_benign_baseline(self.fleet)
        # One C2 endpoint stays open for the whole session; the beacon steps open
        # real sockets to it, and its receive count proves data left the host.
        self._c2 = CanaryListener()
        self._c2.__enter__()
        self.ctx = StepContext(self.fleet.workspace, self._c2.host, self._c2.port)
        self.ordered = build_killchain(self.fleet, self.ctx)
        self._index: dict[str, tuple[Agent, AttackStep]] = {
            step.id: (agent, step) for agent, step in self.ordered
        }
        self.results: dict[str, StepResult] = {}

    def fire(self, step_id: str) -> dict:
        """Perform one step for real and record what the sensors made of it."""
        if step_id not in self._index:
            raise KeyError(step_id)
        agent, step = self._index[step_id]
        start_events = len(agent.node.events)
        start_alerts = len(agent.node.alerts)
        step.perform(agent, self.ctx)
        self.results[step_id] = StepResult(
            step=step,
            agent_id=agent.id,
            sensors_present=agent.role.sensors,
            events=agent.node.events[start_events:],
            alerts=agent.node.alerts[start_alerts:],
        )
        return self._step_view(step_id)

    def fire_all(self) -> dict:
        for agent, step in self.ordered:
            self.fire(step.id)
        return self.state()

    def state(self) -> dict:
        board = Scoreboard(
            results=list(self.results.values()),
            false_alarms=self.false_alarms,
            benign_events=self.benign_events,
        )
        db = self.fleet.first("db")
        return {
            "fleet": self._fleet_summary(),
            "steps": [self._step_view(sid) for sid, _ in self._ordered_ids()],
            "tally": board.tally(),
            "fired": len(self.results),
            "total": len(self.ordered),
            "false_alarms": self.false_alarms,
            "benign_events": self.benign_events,
            "beacons_reached_c2": len(self._c2.received),
            "silent_failure_h2": {
                "status_check": db.canary.status_check_view(),
                "canary_probe": db.canary.probe(),
            },
            "applog_blindness_h3": board.h3_applog_blindness(),
            "capability_matrix_h1": capability_matrix([s for _a, s in self.ordered]),
            "agents": self.fleet_agents(),
            "subnets": self._subnet_order(),
        }

    def fleet_agents(self) -> list[dict]:
        """One record per simulated VM, with the state the fleet view shows: its
        role and sensors, how much telemetry it has produced, and the worst thing
        the attack did to it. Most hosts stay nominal; the kill chain lights up a
        path, and a host breached with no alarm is the state that matters."""
        targeted: dict[str, list[str]] = {}
        for agent, step in self.ordered:
            targeted.setdefault(agent.id, []).append(step.id)
        agents = []
        for agent in self.fleet.agents:
            steps = [self._step_view(sid) for sid in targeted.get(agent.id, [])]
            agents.append({
                "id": agent.id,
                "role": agent.role.name,
                "subnet": agent.subnet,
                "workload": agent.workload,
                "sensors": list(agent.role.sensors),
                "events": len(agent.node.events),
                "alerts": len(agent.node.alerts),
                "on_path": bool(steps),
                "status": _agent_status(steps),
                "steps": steps,
            })
        return agents

    def _subnet_order(self) -> list[str]:
        """Subnets in kill-chain order, so the fleet view can stack them the way
        the intrusion travels: dmz -> corp -> app-tier -> data-tier."""
        order: list[str] = []
        for agent in self.fleet.agents:
            if agent.subnet not in order:
                order.append(agent.subnet)
        preferred = ["dmz", "corp", "app-tier", "data-tier"]
        return sorted(order, key=lambda s: preferred.index(s) if s in preferred else len(preferred))

    def close(self) -> None:
        self._c2.close()

    def _ordered_ids(self) -> list[tuple[str, AttackStep]]:
        return [(step.id, step) for _agent, step in self.ordered]

    def _fleet_summary(self) -> dict:
        by_role: dict[str, int] = {}
        for agent in self.fleet.agents:
            by_role[agent.role.name] = by_role.get(agent.role.name, 0) + 1
        return {"size": self.fleet.size, "by_role": by_role}

    def _step_view(self, step_id: str) -> dict:
        agent, step = self._index[step_id]
        result = self.results.get(step_id)
        view = {
            "id": step.id,
            "tactic": step.tactic,
            "name": step.name,
            "agent": agent.id,
            "role": agent.role.name,
            "subnet": agent.subnet,
            "technique": f"{step.technique.id} {step.technique.name}",
            "owasp": step.owasp,
            "course": step.course,
            "effect_kind": step.effect_kind.value,
            "sensors_present": list(agent.role.sensors),
            "narrative": step.narrative,
            "fired": result is not None,
            "outcome": result.outcome.value if result else "armed",
            "seen_by": sorted(result.seeing_sensors) if result else [],
            "alerts": [
                {"rule_id": a.rule_id, "technique": a.technique.id, "message": a.message}
                for a in (result.alerts if result else [])
            ],
        }
        return view
