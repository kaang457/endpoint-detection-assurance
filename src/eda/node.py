"""The monitored host: one place where sensors watch and rules fire.

A Node is deliberately the only path from a real Observation to recorded Events
and Alerts. Everything an attack does on the host flows through `observe`, so
the stores it holds are the complete, auditable record of a run. Keeping it
synchronous makes each scenario reproducible instead of timing-dependent.
"""

from __future__ import annotations

from .detection import DetectionEngine, default_rules
from .events import Alert, Event, Observation
from .sensors import Sensor, default_sensors


class Node:
    def __init__(
        self,
        sensors: list[Sensor] | None = None,
        engine: DetectionEngine | None = None,
    ) -> None:
        self.sensors = sensors if sensors is not None else default_sensors()
        self.engine = engine if engine is not None else DetectionEngine(default_rules())
        self.events: list[Event] = []
        self.alerts: list[Alert] = []

    def observe(self, obs: Observation) -> None:
        """Offer one real host observation to every sensor, then to the rules."""
        for sensor in self.sensors:
            event = sensor.record(obs)
            if event is None:
                continue
            self.events.append(event)
            self.alerts.extend(self.engine.evaluate(event))

    def sensor(self, name: str) -> Sensor:
        for sensor in self.sensors:
            if sensor.name == name:
                return sensor
        raise KeyError(f"no sensor named {name!r}")
