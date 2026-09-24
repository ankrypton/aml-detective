from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from airflow.plugins_manager import AirflowPlugin

from aml_detective import engine, store

URL_PREFIX = "/aml-detective"
BUNDLE = Path(__file__).parent / "aml_detective" / "static" / "aml-detective.js"
API_BASE_TOKEN = "__AMLD_API_BASE__"

app = FastAPI(title="AML Detective", version="1.0.0")


class Verdict(BaseModel):
    batch_id: str
    case_id: str
    disposition: Literal["sar", "close"]
    typology: Optional[str] = None
    player: str = Field(min_length=1, max_length=40)
    seconds: float = Field(ge=0, le=86400)


@app.get("/")
def root() -> dict:
    return {"plugin": "AML Detective", "bundle": f"{URL_PREFIX}/aml-detective.js", "docs": f"{URL_PREFIX}/docs"}


@app.get("/aml-detective.js")
def bundle(request: Request) -> Response:
    # Inject the mount path so the bundle calls the right URLs behind any proxy prefix.
    root_path = request.scope.get("root_path") or URL_PREFIX
    js = BUNDLE.read_text().replace(API_BASE_TOKEN, root_path.rstrip("/"), 1)
    return Response(js, media_type="application/javascript", headers={"Cache-Control": "no-store"})


@app.get("/api/shift")
def shift() -> dict:
    return engine.public_view(store.latest_batch())


@app.get("/api/progress")
def progress(batch_id: str, player: str) -> dict:
    return store.player_state(batch_id, player.strip())


@app.post("/api/verdict")
def verdict(v: Verdict) -> dict:
    batch = store.get_batch(v.batch_id)
    if batch is None:
        raise HTTPException(404, f"Shift {v.batch_id} was not found. Reload to get the latest shift.")
    truth = batch["truth"].get(v.case_id)
    if truth is None:
        raise HTTPException(404, f"Case {v.case_id} is not part of shift {v.batch_id}.")
    if v.typology is not None and v.typology not in engine.TYPOLOGIES:
        raise HTTPException(422, f"Unknown typology {v.typology}.")
    result = engine.score_verdict(truth, v.disposition, v.typology, v.seconds)
    result["disposition"] = v.disposition
    stored, is_new = store.record_verdict(v.batch_id, v.player.strip(), v.case_id, result)
    total = store.player_state(v.batch_id, v.player.strip())["score"]
    return {**stored, "already_scored": not is_new, "player_total": total}


@app.get("/api/leaderboard")
def leaderboard(batch_id: str) -> dict:
    return {"batch_id": batch_id, "rows": store.leaderboard(batch_id)}


class AMLDetectivePlugin(AirflowPlugin):
    name = "aml_detective"

    fastapi_apps = [{"app": app, "url_prefix": URL_PREFIX, "name": "AML Detective API"}]

    react_apps = [
        {
            "name": "AML Detective",
            "bundle_url": f"{URL_PREFIX}/aml-detective.js",
            "destination": "nav",
            "category": "browse",
            "url_route": "aml-detective",
        }
    ]
