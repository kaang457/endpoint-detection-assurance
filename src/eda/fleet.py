"""The fleet: a company's worth of agents, and the sandbox they share.

Building it from a composition keeps the demo honest about scale — the same
code makes a 6-host test fleet or a 50-host company by changing one dict — and
keeps the heterogeneity visible, since agents are grouped by role.
"""

from __future__ import annotations

from .agent import Agent
from .roles import REACHABILITY, ROLES, default_composition
from .workspace import Workspace, build_workspace


class Fleet:
    def __init__(self, agents: list[Agent], workspace: Workspace) -> None:
        self.agents = agents
        self.workspace = workspace

    @classmethod
    def build(
        cls,
        composition: dict[str, int] | None = None,
        workspace: Workspace | None = None,
    ) -> "Fleet":
        composition = composition if composition is not None else default_composition()
        workspace = workspace if workspace is not None else build_workspace()
        agents: list[Agent] = []
        for role_name, count in composition.items():
            role = ROLES[role_name]
            for index in range(count):
                agents.append(Agent(f"{role_name}-{index + 1:02d}", role))
        return cls(agents, workspace)

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
        the real edges."""
        return target.subnet in REACHABILITY.get(source.subnet, set())

    @property
    def size(self) -> int:
        return len(self.agents)
