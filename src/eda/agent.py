"""An agent stands in for one monitored machine in the target fleet.

It is deliberately light: a real VM is not needed to study what sensors see. An
agent is built from a `HostSpec` the source handed us (its management facts) and
owns a Node — its sensors and the rules watching them — and a canary checker.
The host actions an attack performs on the agent are real OS operations through
`host`, so the sensors are measured against things that truly happened.
"""

from __future__ import annotations

from .node import Node
from .roles import ROLES, Role
from .sensors import CanaryChecker, make_sensors
from .source import HostSpec


class Agent:
    def __init__(self, spec: HostSpec) -> None:
        self.spec = spec
        self.id = spec.id
        self.role: Role = ROLES[spec.role]
        self.node = Node(sensors=make_sensors(list(spec.sensors)))
        self.canary = CanaryChecker(self.node.sensors)

    @property
    def workload(self) -> str:
        return self.spec.workload

    @property
    def subnet(self) -> str:
        return self.spec.subnet

    def __repr__(self) -> str:
        return f"Agent({self.id}, {self.role.name}, sensors={self.spec.sensors})"
