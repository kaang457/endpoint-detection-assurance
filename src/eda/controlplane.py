"""The control plane: the service that owns the fleet and serves the result.

It is the "realistic backend" the fleet reports to — a SOC console, not another
bank app. Two faces:

- `/` is the **interactive** console: fire one attack step at a time and watch
  whether an alarm comes back (`live.LiveCampaign`, held in memory).
- `/report` is a full non-interactive run, and `/report.html` renders it as the
  static dashboard.

The heavy lifting is all in `harness.run` and `live.LiveCampaign`; the handlers
stay thin.
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from .catalog import catalog_as_dicts
from .console import render_console
from .fleet import Fleet
from .harness import run
from .live import LiveCampaign
from .report import render_html
from .roles import default_composition

app = FastAPI(title="Endpoint Detection Assurance")

_FIXED_ROLES = {k: v for k, v in default_composition().items() if k != "workstation"}
_MIN_WORKSTATIONS = 1
_last_report: dict | None = None
_live: LiveCampaign | None = None


def _composition() -> dict[str, int]:
    """Fleet size comes from EDA_FLEET_SIZE; the extra hosts are workstations,
    the way a real company grows. The server roles are fixed (the campaign needs
    one of each), so sizes below their count are floored, not silently wrong."""
    requested = int(os.environ.get("EDA_FLEET_SIZE", "50"))
    fixed = sum(_FIXED_ROLES.values())
    workstations = max(_MIN_WORKSTATIONS, requested - fixed)
    return {"workstation": workstations, **_FIXED_ROLES}


def _run_once() -> dict:
    global _last_report
    _last_report = run(Fleet.build(_composition()))
    return _last_report


def _live_campaign() -> LiveCampaign:
    global _live
    if _live is None:
        _live = LiveCampaign(_composition())
    return _live


def _reset_live() -> LiveCampaign:
    global _live
    if _live is not None:
        _live.close()
    _live = LiveCampaign(_composition())
    return _live


@app.on_event("startup")
def _warm() -> None:
    _live_campaign()


@app.get("/", response_class=HTMLResponse)
def console() -> str:
    return render_console()


@app.get("/live/state")
def live_state() -> JSONResponse:
    return JSONResponse(_live_campaign().state())


@app.post("/live/reset")
def live_reset() -> JSONResponse:
    return JSONResponse(_reset_live().state())


@app.post("/live/fire/{step_id}")
def live_fire(step_id: str) -> JSONResponse:
    try:
        _live_campaign().fire(step_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"no step {step_id!r}")
    return JSONResponse(_live_campaign().state())


@app.post("/live/fire-all")
def live_fire_all() -> JSONResponse:
    return JSONResponse(_live_campaign().fire_all())


@app.get("/report")
def report() -> JSONResponse:
    return JSONResponse(_last_report or _run_once())


@app.get("/report.html", response_class=HTMLResponse)
def report_html() -> str:
    return render_html(_last_report or _run_once())


@app.get("/fleet")
def fleet() -> JSONResponse:
    return JSONResponse((_last_report or _run_once())["fleet"])


@app.get("/catalog")
def catalog() -> JSONResponse:
    """The planted vulnerabilities, tagged with OWASP:2025, ATT&CK and lecture."""
    return JSONResponse(catalog_as_dicts())
