"""The control plane: the service that owns the fleet and serves the result.

It is the "realistic backend" the fleet reports to — a SOC console, not another
bank app. Two faces:

- `/` is the **operator console**: the built React app in `webui/`, which drives
  the fleet and the kill chain through the `/live/*` JSON below (`live.LiveCampaign`,
  held in memory).
- `/report.html` renders a full non-interactive run as the static dashboard, and
  `/report` returns it as JSON.

The heavy lifting is all in `harness.run` and `live.LiveCampaign`; the handlers
stay thin. The web UI is built separately (`cd frontend && npm run build`); if it
has not been built, `/` says so instead of 500-ing.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .catalog import catalog_as_dicts
from .fleet import Fleet
from .harness import run
from .live import LiveCampaign
from .report import render_html
from .roles import default_composition

app = FastAPI(title="Endpoint Detection Assurance")

_WEBUI = Path(__file__).parent / "webui"
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


if (_WEBUI / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=_WEBUI / "assets"), name="assets")


@app.get("/", response_class=HTMLResponse)
def console() -> HTMLResponse:
    index = _WEBUI / "index.html"
    if index.is_file():
        return HTMLResponse(index.read_text(encoding="utf-8"))
    return HTMLResponse(
        "<h1>Web UI not built</h1><p>Run <code>cd frontend &amp;&amp; npm install &amp;&amp; "
        "npm run build</code>, then reload. The JSON API and <a href='/report.html'>/report.html</a> "
        "work without it.</p>",
        status_code=200,
    )


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
