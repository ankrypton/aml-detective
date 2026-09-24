import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "plugins"))

from aml_detective import engine  


@pytest.mark.parametrize("seed", [f"seed-{i}" for i in range(50)])
def test_rules_engine_finds_exactly_the_planted_accounts(seed):
    activity = engine.generate_activity(seed)
    alerted = {a["account_id"] for a in engine.screen(activity)}
    assert alerted == set(activity["planted"])


def test_signature_rules():
    signature = {"structuring": "R01", "funnel": "R02", "rapid_movement": "R03", "escrow_false_positive": "R03",
                 "high_risk": "R04", "sanctions": "R05", "name_false_positive": "R05",
                 "seasonal_false_positive": "R06"}
    activity = engine.generate_activity("signature")
    for alert in engine.screen(activity):
        scenario = activity["planted"][alert["account_id"]]["scenario"]
        assert signature[scenario] in {h["code"] for h in alert["hits"]}


def test_public_view_hides_answer_key():
    activity = engine.generate_activity("hidden")
    batch = engine.assemble_batch(activity, engine.screen(activity), "b1")
    assert "truth" not in engine.public_view(batch)
    assert "planted" not in str(engine.public_view(batch))


def test_scoring_penalizes_missed_sars_most():
    sar = {"disposition": "sar", "typology": "structuring", "debrief": ""}
    fp = {"disposition": "close", "typology": None, "debrief": ""}
    assert engine.score_verdict(sar, "sar", "structuring", 200)["points"] == 150
    assert engine.score_verdict(sar, "sar", "funnel_account", 200)["points"] == 100
    assert engine.score_verdict(sar, "close", None, 5)["points"] == -150
    assert engine.score_verdict(fp, "sar", "structuring", 5)["points"] == -50
    assert engine.score_verdict(fp, "close", None, 0)["points"] == 130


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("AML_DETECTIVE_DATA_DIR", str(tmp_path))
    pytest.importorskip("airflow")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import aml_detective_plugin as plugin

    host = FastAPI()
    host.mount("/aml-detective", plugin.app)  # mounted the way Airflow mounts plugin apps
    return TestClient(host)


def test_bundle_gets_mount_path_injected(client):
    js = client.get("/aml-detective/aml-detective.js").text
    assert '"/aml-detective"' in js and "__AMLD_API_BASE__" not in js


def test_full_verdict_flow(client):
    shift = client.get("/aml-detective/api/shift").json()
    assert shift["source"] == "practice" and "truth" not in shift
    case = shift["cases"][0]
    body = {"batch_id": shift["batch_id"], "case_id": case["case_id"], "disposition": "close",
            "player": "tester", "seconds": 30}
    first = client.post("/aml-detective/api/verdict", json=body).json()
    again = client.post("/aml-detective/api/verdict", json={**body, "disposition": "sar",
                                                             "typology": "structuring"}).json()
    assert again["already_scored"] and again["points"] == first["points"]
    board = client.get("/aml-detective/api/leaderboard", params={"batch_id": shift["batch_id"]}).json()
    assert board["rows"][0] == {"player": "tester", "score": first["points"], "cases": 1, "missed_sars":
                                int(first["outcome"] == "missed_sar")}


def test_verdict_rejects_unknown_case(client):
    shift = client.get("/aml-detective/api/shift").json()
    r = client.post("/aml-detective/api/verdict", json={"batch_id": shift["batch_id"], "case_id": "NOPE",
                                                        "disposition": "close", "player": "x", "seconds": 1})
    assert r.status_code == 404
