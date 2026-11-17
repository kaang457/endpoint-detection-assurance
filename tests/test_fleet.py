"""One integration test that runs the real campaign on a minimal fleet, so the
end-to-end claims in the report are exercised, not just the units."""

from __future__ import annotations

from eda.fleet import Fleet
from eda.harness import run


def _small_fleet() -> Fleet:
    return Fleet.build({"edge-web": 1, "workstation": 1, "app": 1, "db": 1})


def _step(report: dict, step_id: str) -> dict:
    return next(s for s in report["steps"] if s["id"] == step_id)


def test_fleet_build_honours_composition():
    fleet = Fleet.build({"workstation": 3, "db": 2})
    assert fleet.size == 5
    assert len(fleet.of_role("workstation")) == 3


def test_campaign_shows_all_three_outcomes():
    report = run(_small_fleet())
    tally = report["tally"]
    assert tally["detected"] >= 1
    assert tally["visible_only"] == 1  # the recon step, by construction
    assert tally["blind"] >= 1


def test_same_exfil_technique_is_detected_on_edr_host_but_blind_on_app_h1():
    # H1 as a scored contrast, not just a static matrix: identical beacon,
    # DETECTED where an EDR covers the network (s3, edge), BLIND where no sensor
    # does (s8, app tier).
    report = run(_small_fleet())
    assert _step(report, "s3")["outcome"] == "detected"
    assert _step(report, "s8")["outcome"] == "blind"


def test_secret_read_is_blind_on_the_osquery_only_workstation_h1():
    # The same credential read the EDR hosts detect is invisible on a laptop
    # whose only sensor is process-granularity osquery.
    report = run(_small_fleet())
    assert _step(report, "s2")["outcome"] == "detected"
    assert _step(report, "s6")["outcome"] == "blind"


def test_normal_activity_raises_no_alarms():
    report = run(_small_fleet())
    assert report["false_alarms"] == 0


def test_blinded_edr_lies_to_the_status_check_but_not_the_canary():
    report = run(_small_fleet())
    h2 = report["silent_failure_h2"]
    assert h2["status_check"]["edr"] == "healthy"
    assert h2["canary_probe"]["edr"] == "SILENT"


def test_app_log_holds_requests_but_no_host_effects():
    report = run(_small_fleet())
    h3 = report["applog_blindness_h3"]
    assert h3["requests_logged"] >= 1
    assert h3["host_effects_in_app_log"] == 0
