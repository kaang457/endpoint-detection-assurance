"""The seam between the EDA tool and the environment it measures.

The tool — sensors, detection rules, scoring, the assurance console — is pointed
at a *target* it did not create and only observes. A `FleetSource` is that
target: the inventory of hosts, their management state the way a VM-management
system (Citrix/vSphere-class) would present it, and the trust boundaries between
them. The simulated company fleet is one implementation; a different backend (a
real inventory pulled from a hypervisor API, another lab) is a drop-in behind the
same interface, selected with `EDA_SOURCE`.

Keeping this boundary explicit is the point: the fleet is the thing under test,
not part of the tool, so the tool stays reusable against a different fleet.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

from .roles import REACHABILITY, ROLES, default_composition


@dataclass(frozen=True)
class HostSpec:
    """One host as the management plane sees it: identity, placement, and the
    virtual-hardware facts a VM console shows, plus which sensors it runs."""

    id: str
    role: str
    subnet: str
    workload: str
    sensors: tuple[str, ...]
    os: str
    ip: str
    vcpu: int
    mem_gb: int
    disk_gb: int
    power: str  # running | stopped | suspended | maintenance
    uptime_s: int
    pool: str


class FleetSource(Protocol):
    """A target environment the tool can be pointed at."""

    name: str

    def inventory(self) -> list[HostSpec]: ...

    def reachability(self) -> dict[str, set[str]]: ...


# What a VM-management panel would show per role: OS image, virtual hardware,
# and the resource pool the role lives in. Drawn from the role, not invented per
# host, so the fleet reads as a real deployment rather than random noise.
_PROFILE: dict[str, tuple[str, int, int, int, str]] = {
    "edge-web": ("Ubuntu Server 22.04 LTS", 2, 4, 40, "pool-dmz"),
    "app": ("Ubuntu Server 22.04 LTS", 4, 8, 80, "pool-app"),
    "db": ("Debian 12", 8, 32, 500, "pool-data"),
    "workstation": ("Windows 11 Pro 23H2", 4, 16, 256, "pool-corp"),
    "domain-controller": ("Windows Server 2022", 4, 16, 120, "pool-data"),
    "jump": ("Rocky Linux 9", 2, 4, 40, "pool-app"),
}
_SUBNET_CIDR: dict[str, str] = {
    "dmz": "10.0.10",
    "corp": "10.0.20",
    "app-tier": "10.0.30",
    "data-tier": "10.0.40",
}


class SimulatedCitrixSource:
    """A ~50-VM company fleet, presented the way a Citrix/vSphere panel would.

    No real hypervisor: each VM's management facts are derived deterministically
    from its role and index, so the inventory is stable across runs and the
    console looks like a real deployment under management.
    """

    name = "simulated-citrix"

    def __init__(self, composition: dict[str, int] | None = None) -> None:
        self._composition = composition if composition is not None else default_composition()

    def inventory(self) -> list[HostSpec]:
        hosts: list[HostSpec] = []
        next_octet: dict[str, int] = {}
        for role_name, count in self._composition.items():
            role = ROLES[role_name]
            os_name, vcpu, mem_gb, disk_gb, pool = _PROFILE[role_name]
            for index in range(count):
                idx = index + 1
                octet = next_octet.get(role.subnet, 11)
                next_octet[role.subnet] = octet + 1
                # a stable, plausible uptime between ~2 and ~60 days
                uptime_days = 2 + (idx * 7 + len(role_name) * 3) % 58
                hosts.append(
                    HostSpec(
                        id=f"{role_name}-{idx:02d}",
                        role=role_name,
                        subnet=role.subnet,
                        workload=role.workload,
                        sensors=role.sensors,
                        os=os_name,
                        ip=f"{_SUBNET_CIDR.get(role.subnet, '10.0.0')}.{octet}",
                        vcpu=vcpu,
                        mem_gb=mem_gb,
                        disk_gb=disk_gb,
                        power="running",
                        uptime_s=uptime_days * 86400,
                        pool=pool,
                    )
                )
        return hosts

    def reachability(self) -> dict[str, set[str]]:
        return {subnet: set(targets) for subnet, targets in REACHABILITY.items()}


SOURCES: dict[str, type[SimulatedCitrixSource]] = {
    SimulatedCitrixSource.name: SimulatedCitrixSource,
}


def source_from_env(composition: dict[str, int] | None = None) -> FleetSource:
    """Pick the target backend from EDA_SOURCE (default: the simulated fleet).
    An unknown name is a configuration error, not something to paper over."""
    name = os.environ.get("EDA_SOURCE", SimulatedCitrixSource.name)
    if name not in SOURCES:
        raise ValueError(f"unknown EDA_SOURCE {name!r}; known: {sorted(SOURCES)}")
    return SOURCES[name](composition)
