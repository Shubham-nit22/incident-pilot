import pytest

import app.tools.simulated_tools as tools

def test_every_action_has_a_valid_risk_label():
    assert all(info["risk"] in ("low","high") for info in tools.ACTIONS.values())


def test_exactly_the_disruptive_actions_are_high_risk():
    high = {name for name, info in tools.ACTIONS.items() if info["risk"] == "high"}
    assert high == {"restart_service","rollback_deploy","block_ip"}


def test_unknown_action_is_rejected():
    with pytest.raises(KeyError):
        tools.get_risk("delete_everything")

def test_run_action_only_writes_a_log_line(tmp_path,monkeypatch):
    log = tmp_path / "actions.log"
    monkeypatch.setattr(tools,"LOG_FILE",log)

    result = tools.run_action("clear_cache","orders-db")

    assert result["ok"] is True
    assert "clear_cache | orders-db" in log.read_text(encoding="utf-8")
