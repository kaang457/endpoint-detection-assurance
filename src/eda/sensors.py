"""Sensors: the layer whose honesty the project is built to test.

A sensor records an Observation as an Event only when two things hold: the
observation's kind is within the sensor's coverage, and the sensor is healthy.
That is the whole model, and both halves carry a hypothesis.

- Coverage differs between sensors (H1). The three here mirror the proposal's
  auditd / osquery / Falco-Tracee: a syscall tracer sees almost everything, a
  periodic query tool sees coarse process facts, an audit daemon sits between.
- Health can fail silently (H2). `blind()` stops a sensor from recording while
  its own status check keeps reporting healthy, which is exactly how a disabled
  sensor lies. The canary below is what catches that lie.
"""

from __future__ import annotations

from .events import Event, EventKind, Observation


class Sensor:
    """One endpoint sensor with a fixed coverage set and a health state."""

    def __init__(self, name: str, covers: set[EventKind], role: str) -> None:
        self.name = name
        self.covers = covers
        self.role = role
        self._blinded = False

    def record(self, obs: Observation) -> Event | None:
        """Return an Event if this sensor can and does see the observation."""
        if self._blinded:
            return None
        if obs.kind not in self.covers:
            return None
        return Event.seen_by(self.name, obs)

    def blind(self) -> None:
        """Silence the sensor without changing what its status check reports.

        A real disabled agent keeps answering 'running' while emitting nothing;
        separating `_blinded` from `reports_healthy` is what reproduces that.
        """
        self._blinded = True

    def reports_healthy(self) -> bool:
        """What a naive 'is the sensor up?' status check would see. Always True,
        because a blinded sensor does not know it has been blinded."""
        return True


# The telemetry sources from Day 15, each with the coverage it realistically
# has. The gaps between rows are hypothesis H1 and are deliberate.
SENSOR_SPECS: dict[str, tuple[str, set[EventKind]]] = {
    "edr": (
        "EDR agent (syscall + network + file, Falco/Sysmon-class)",
        {
            EventKind.PROCESS_SPAWN,
            EventKind.FILE_READ,
            EventKind.NETWORK_CONNECT,
            EventKind.LOG_TAMPER,
        },
    ),
    "auditd": (
        "Linux audit daemon (syscalls, no network)",
        {EventKind.PROCESS_SPAWN, EventKind.FILE_READ, EventKind.LOG_TAMPER},
    ),
    "osquery": (
        "periodic query agent (coarse, process-only)",
        {EventKind.PROCESS_SPAWN},
    ),
    "applog": (
        "application's own request log",
        {EventKind.APP_REQUEST},
    ),
}


def make_sensors(names: list[str]) -> list[Sensor]:
    """Fresh Sensor instances for one agent. Per-agent instances matter: blinding
    one host's EDR must not silence another's."""
    return [Sensor(name, covers, role) for name in names for role, covers in [SENSOR_SPECS[name]]]


def default_sensors() -> list[Sensor]:
    return make_sensors(list(SENSOR_SPECS))


# A canary is a benign observation we inject on purpose and expect every
# covering sensor to echo back. Its kind is one every host sensor should see.
CANARY_ACTOR = "canary"


def canary_observation() -> Observation:
    return Observation(
        kind=EventKind.PROCESS_SPAWN,
        actor=CANARY_ACTOR,
        target="eda-canary",
        detail={"synthetic": "true"},
    )


class CanaryChecker:
    """Probes sensor health by result, not by self-report.

    Each round it injects a canary and notes which sensors echoed it. A sensor
    that covers the canary's kind but stays silent is reported SILENT, even
    while its own status still says healthy. That contrast is hypothesis H2.
    """

    def __init__(self, sensors: list[Sensor]) -> None:
        self._expected = [s for s in sensors if canary_observation().kind in s.covers]
        self._sensors = sensors

    def probe(self) -> dict[str, str]:
        obs = canary_observation()
        echoed = {s.name for s in self._sensors if s.record(obs) is not None}
        return {
            s.name: ("alive" if s.name in echoed else "SILENT")
            for s in self._expected
        }

    def status_check_view(self) -> dict[str, str]:
        """What the dumb check believes: everyone is fine."""
        return {
            s.name: ("healthy" if s.reports_healthy() else "down")
            for s in self._expected
        }
