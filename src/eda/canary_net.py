"""A throwaway TCP listener that plays the attacker's C2 endpoint.

Exfiltration steps open a real socket to it, so the network sensor is measured
against a connection that genuinely happened rather than a mock. It binds an
ephemeral port on loopback and records what it received, which doubles as proof
the beacon left the host.
"""

from __future__ import annotations

import socket
import threading


class CanaryListener:
    def __init__(self, host: str = "127.0.0.1") -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((host, 0))
        self._sock.listen(8)
        self.host, self.port = self._sock.getsockname()
        self.received: list[bytes] = []
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._running = True

    def __enter__(self) -> "CanaryListener":
        self._thread.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def _serve(self) -> None:
        while self._running:
            try:
                conn, _addr = self._sock.accept()
            except OSError:
                return
            with conn:
                chunk = conn.recv(4096)
                if chunk:
                    self.received.append(chunk)

    def close(self) -> None:
        self._running = False
        try:
            self._sock.close()
        except OSError:
            pass
