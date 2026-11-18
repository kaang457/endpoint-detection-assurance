"""The source is the seam between the tool and the target it measures. These
tests pin that a source hands over a management-grade inventory, and that an
unknown backend fails loudly instead of silently falling back."""

from __future__ import annotations

import pytest

from eda.source import SimulatedCitrixSource, source_from_env


def test_inventory_carries_management_facts():
    hosts = SimulatedCitrixSource({"edge-web": 2, "db": 1}).inventory()
    assert [h.id for h in hosts] == ["edge-web-01", "edge-web-02", "db-01"]
    edge = hosts[0]
    assert edge.os and edge.pool == "pool-dmz" and edge.vcpu >= 1
    # hosts on the same subnet get distinct addresses in its range
    assert edge.ip.startswith("10.0.10.") and hosts[1].ip != edge.ip


def test_db_is_provisioned_heavier_than_a_web_host():
    hosts = {h.role: h for h in SimulatedCitrixSource({"edge-web": 1, "db": 1}).inventory()}
    assert hosts["db"].mem_gb > hosts["edge-web"].mem_gb
    assert hosts["db"].disk_gb > hosts["edge-web"].disk_gb


def test_unknown_source_is_a_loud_error(monkeypatch):
    monkeypatch.setenv("EDA_SOURCE", "no-such-backend")
    with pytest.raises(ValueError):
        source_from_env()


def test_default_source_is_the_simulated_fleet(monkeypatch):
    monkeypatch.delenv("EDA_SOURCE", raising=False)
    assert source_from_env().name == "simulated-citrix"
