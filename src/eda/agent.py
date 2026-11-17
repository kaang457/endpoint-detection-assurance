"""An agent stands in for one monitored machine.

It is deliberately light: a real VM is not needed to study what sensors see.
An agent owns a Node (its sensors and the rules watching them) and a canary
checker (its own health probe). The host actions an attack performs on the
agent are real OS operations through `host`, so the sensors are measured
against things that truly happened on this machine.
"""

from __future__ import annotations

from .node import Node
from .roles import Role
from .sensors import CanaryChecker, make_sensors


class Agent:
    def __init__(self, agent_id: str, role: Role) -> None:
        self.id = agent_id
        self.role = role
        self.node = Node(sensors=make_sensors(list(role.sensors)))
        self.canary = CanaryChecker(self.node.sensors)

    @property
    def workload(self) -> str:
        return self.role.workload

    @property
    def subnet(self) -> str:
        return self.role.subnet

    def __repr__(self) -> str:
        return f"Agent({self.id}, {self.role.name}, sensors={self.role.sensors})"
