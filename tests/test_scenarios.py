"""Each scenario should tell a genuinely different story, not the same run with
new labels. These pin the distinguishing shape of each one at the public
boundary (a scored LiveCampaign), so a scenario can't quietly collapse into
another."""

from __future__ import annotations

from eda.live import LiveCampaign
from eda.scenarios import SCENARIOS

_COMPOSITION = {
    "edge-web": 3,
    "workstation": 2,
    "app": 2,
    "db": 1,
    "domain-controller": 1,
    "jump": 1,
}


def _run(scenario: str) -> dict:
    campaign = LiveCampaign(_COMPOSITION, scenario=scenario)
    campaign.fire_all()
    state = campaign.state()
    campaign.close()
    return state


def test_every_scenario_builds_and_scores():
    for scenario_id in SCENARIOS:
        state = _run(scenario_id)
        assert state["total"] >= 3
        assert sum(state["tally"].values()) == state["total"]


def test_web_injection_is_fully_covered():
    # A well-watched edge host: nothing should go blind, which is the point.
    assert _run("web-injection")["tally"]["blind"] == 0


def test_phished_laptop_reaches_the_domain_controller():
    hits = {a["role"] for a in _run("phished-laptop")["agents"] if a["on_path"]}
    assert "domain-controller" in hits and "edge-web" not in hits


def test_ddos_smokescreen_hides_one_silent_exfil_under_the_alerts():
    tally = _run("ddos-smokescreen")["tally"]
    assert tally["detected"] >= 2 and tally["blind"] == 1


def test_random_resolves_to_a_real_scenario():
    assert _run("random")["scenario"]["id"] in SCENARIOS
