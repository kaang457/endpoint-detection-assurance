"""Real, benign host actions that attacks perform through the app's vulnerabilities.

Every function here causes a genuine OS effect (a real child process, a real
file read, a real socket) and returns the Observation describing it. Nothing is
faked: the point of the project is that sensors are measured against things that
actually occurred. The effects are kept harmless and sandboxed, per the
proposal's ethics scope: no real malware, only dummy files and a canary secret.
"""

from __future__ import annotations

import os
import socket
import subprocess
from pathlib import Path

from .events import EventKind, Observation


def _basename(path: str) -> str:
    return Path(path).name


def shell_command(inner: str) -> list[str]:
    """The platform shell invocation. The exe name is honest so a 'shell spawned
    by the web process' rule matches the thing that truly ran."""
    if os.name == "nt":
        return ["cmd", "/c", inner]
    return ["/bin/sh", "-c", inner]


def spawn(argv: list[str], actor: str) -> Observation:
    """Start a real child process and wait briefly for it. Used by scenarios
    that reach code execution (shell spawn) or recon (a benign binary)."""
    proc = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    exe = _basename(argv[0])
    return Observation(
        kind=EventKind.PROCESS_SPAWN,
        actor=actor,
        target=exe,
        detail={"argv": " ".join(argv), "exit_code": str(proc.returncode)},
    )


def read_file(path: str | Path, actor: str) -> Observation:
    """Read a real file (a planted dummy secret) and record the access."""
    path = Path(path)
    content = path.read_text(encoding="utf-8", errors="replace")
    return Observation(
        kind=EventKind.FILE_READ,
        actor=actor,
        target=str(path),
        detail={"bytes": str(len(content))},
    )


def connect(host: str, port: int, payload: bytes, actor: str) -> Observation:
    """Open a real TCP connection to an endpoint (the canary listener standing in
    for an attacker's C2) and send bytes. Models exfiltration."""
    with socket.create_connection((host, port), timeout=5) as sock:
        sock.sendall(payload)
    return Observation(
        kind=EventKind.NETWORK_CONNECT,
        actor=actor,
        target=f"{host}:{port}",
        detail={"bytes_sent": str(len(payload))},
    )


def truncate_log(path: str | Path, actor: str) -> Observation:
    """Blank a log file the way an intruder disabling logging would. Real write;
    the Observation is how an endpoint sensor would still catch the tampering
    even though the log itself now shows nothing."""
    path = Path(path)
    had = path.stat().st_size if path.exists() else 0
    path.write_text("", encoding="utf-8")
    return Observation(
        kind=EventKind.LOG_TAMPER,
        actor=actor,
        target=str(path),
        detail={"cleared_bytes": str(had)},
    )
