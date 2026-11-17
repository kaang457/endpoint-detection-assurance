"""The core vocabulary shared by every layer.

The chain is deliberate and one-directional:

    Observation  -> what really happened on the host (ground truth, because we
                    are the ones who ran the attack)
    Event        -> an Observation as a specific sensor recorded it (visibility)
    Alert        -> a detection rule firing on an Event (detection)

Rules never read an Observation's ground-truth label; they infer a technique
from the event's shape. Otherwise a "detection" would just be reading back the
answer we planted, which measures nothing.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class EventKind(str, Enum):
    """The kinds of host activity a sensor may or may not be able to record.

    Sensors differ in which of these they cover; that difference is hypothesis
    H1 and is the reason a single sensor's coverage claim is overstated.
    """

    PROCESS_SPAWN = "process_spawn"
    FILE_READ = "file_read"
    NETWORK_CONNECT = "network_connect"
    LOG_TAMPER = "log_tamper"
    APP_REQUEST = "app_request"


@dataclass(frozen=True)
class Technique:
    """An ATT&CK technique. Frozen so it can key the coverage matrix."""

    id: str
    name: str

    def __str__(self) -> str:
        return f"{self.id} ({self.name})"


@dataclass
class Observation:
    """A real thing that happened on the host, recorded at the source.

    This is ground truth: the harness caused it, so it knows the actor and the
    target exactly. Sensors are then measured against this, never fed from it.
    """

    kind: EventKind
    actor: str
    target: str | None
    detail: dict[str, str] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)


@dataclass
class Event:
    """An Observation as one sensor recorded it. The unit of visibility."""

    sensor: str
    kind: EventKind
    actor: str
    target: str | None
    detail: dict[str, str]
    ts: float

    @classmethod
    def seen_by(cls, sensor: str, obs: Observation) -> "Event":
        return cls(
            sensor=sensor,
            kind=obs.kind,
            actor=obs.actor,
            target=obs.target,
            detail=dict(obs.detail),
            ts=obs.ts,
        )


@dataclass
class Alert:
    """A detection rule firing on an Event. The unit of detection."""

    rule_id: str
    technique: Technique
    sensor: str
    severity: str
    message: str
    event: Event
