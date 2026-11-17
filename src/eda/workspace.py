"""The sandbox a monitored node runs inside: dummy data and a canary secret.

Per the proposal's ethics scope, the attacks only ever touch planted dummy
files and a canary secret, never anything real. This module builds that sandbox
so a scenario's file read or log tamper hits something safe and known.

Each agent gets its *own* log file (`log_for`): "disable logging on the
database" must clear that one host's log, not a single file shared by the whole
fleet. The shared secret stands in for a credential every tier can reach.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

CANARY_SECRET = "CANARY-SECRET-" + "do-not-exfiltrate-0xBADC0FFEE"


@dataclass
class Workspace:
    root: Path
    data_dir: Path
    secrets_dir: Path
    log_dir: Path

    @property
    def canary_secret_file(self) -> Path:
        return self.secrets_dir / "master.key"

    def log_for(self, agent_id: str) -> Path:
        """The log file for one host. Per-agent so tampering is local to the
        host under attack, the way a real intruder clears only the box they own."""
        return self.log_dir / f"{agent_id}.log"


def build_workspace(base: str | Path | None = None) -> Workspace:
    """Create the sandbox tree and plant its files. If no base is given, use a
    fresh temp directory so repeated local runs never collide."""
    root = Path(base) if base is not None else Path(tempfile.mkdtemp(prefix="eda-node-"))
    data_dir = root / "data"
    secrets_dir = root / "secrets"
    log_dir = root / "logs"
    for directory in (data_dir, secrets_dir, log_dir):
        directory.mkdir(parents=True, exist_ok=True)

    (data_dir / "records-2026-10.csv").write_text(
        "account,closing_balance\n100200,4210.75\n", encoding="utf-8"
    )
    secrets_file = secrets_dir / "master.key"
    secrets_file.write_text(CANARY_SECRET + "\n", encoding="utf-8")

    return Workspace(
        root=root,
        data_dir=data_dir,
        secrets_dir=secrets_dir,
        log_dir=log_dir,
    )


def workspace_from_env() -> Workspace:
    """Used by the containerized app: honor EDA_WORKDIR if the image set one."""
    return build_workspace(os.environ.get("EDA_WORKDIR"))
