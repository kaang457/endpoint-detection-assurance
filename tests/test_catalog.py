"""The catalog is the reviewer-facing index of planted weaknesses. This checks
it stays honest: every technique the campaign actually uses is listed, so the
catalog can't drift out of sync with what the scenarios do."""

from __future__ import annotations

from eda.catalog import CATALOG
from eda.scenarios import StepContext, build_killchain
from eda.fleet import Fleet


def _campaign_technique_ids() -> set[str]:
    fleet = Fleet.build({"edge-web": 1, "workstation": 1, "app": 1, "db": 1})
    ctx = StepContext(workspace=fleet.workspace, c2_host="127.0.0.1", c2_port=1)
    steps = build_killchain(fleet, ctx)
    return {step.technique.id for _agent, step in steps}


def test_catalog_covers_every_campaign_technique():
    catalog_ids = {v.attack.split()[0] for v in CATALOG}
    assert _campaign_technique_ids() <= catalog_ids


def test_every_vulnerability_names_an_owasp_2025_category():
    assert all(v.owasp_2025.startswith("A") for v in CATALOG)
