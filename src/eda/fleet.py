"""The fleet: the target's hosts as the tool sees them, and the sandbox they share.

A fleet is built from a `FleetSource` — the inventory of a target environment —
so the tool is never the thing that decides what hosts exist; it only observes
whatever the source presents. `build` keeps a convenience path for tests and the
default simulated fleet; any other backend arrives through `from_source`.
"""

from __future__ import annotations

from .agent import Agent
from .source import FleetSource, SimulatedCitrixSource
from .workspace import Workspace, build_workspace


class Fleet:
    def __init__(self, agents: list[Agent], workspace: Workspace, source_name: str,
                 reachability: dict[str, set[str]]) -> None:
        self.agents = agents
        self.workspace = workspace
        self.source_name = source_name
        self._reachability = reachability

    @classmethod
    def from_source(cls, source: FleetSource, workspace: Workspace | None = None) -> "Fleet":
        workspace = workspace if workspace is not None else build_workspace()
        agents = [Agent(spec) for spec in source.inventory()]
        return cls(agents, workspace, source.name, source.reachability())

    @classmethod
    def build(
        cls,
        composition: dict[str, int] | None = None,
        workspace: Workspace | None = None,
    ) -> "Fleet":
        return cls.from_source(SimulatedCitrixSource(composition), workspace)

    def of_role(self, role_name: str) -> list[Agent]:
        return [a for a in self.agents if a.role.name == role_name]

    def first(self, role_name: str) -> Agent:
        agents = self.of_role(role_name)
        if not agents:
            raise KeyError(f"no agent with role {role_name!r} in the fleet")
        return agents[0]

    def can_reach(self, source: Agent, target: Agent) -> bool:
        """Whether source's subnet is allowed to open a connection to target's.
        Lateral movement that ignores this is not modelled; the campaign follows
        the real edges the source declares."""
        return target.subnet in self._reachability.get(source.subnet, set())

    @property
    def size(self) -> int:
        return len(self.agents)
