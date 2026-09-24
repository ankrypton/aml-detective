from __future__ import annotations

import json
import os
import re
import tempfile
import threading
from datetime import date
from pathlib import Path

from aml_detective import engine

_lock = threading.Lock()
_practice_cache: dict | None = None
PRACTICE_PREFIX = "practice-"


def data_dir() -> Path:
    default = Path(os.environ.get("AIRFLOW_HOME", "/usr/local/airflow")) / "include" / "aml_detective"
    path = Path(os.environ.get("AML_DETECTIVE_DATA_DIR", default))
    (path / "batches").mkdir(parents=True, exist_ok=True)
    return path


def safe_id(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "-", raw)[:120]


def _atomic_write(path: Path, payload: dict) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(payload, f, indent=1)
    os.replace(tmp, path)


def save_batch(batch: dict) -> Path:
    path = data_dir() / "batches" / f"{safe_id(batch['batch_id'])}.json"
    _atomic_write(path, batch)
    return path


def _read(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def practice_batch() -> dict:
    global _practice_cache
    if _practice_cache is None:
        today = date.today()
        seed = f"practice-{today.isoformat()}"
        activity = engine.generate_activity(seed, today)
        alerts = engine.screen(activity)
        _practice_cache = engine.assemble_batch(activity, alerts, batch_id=seed, source="practice")
    return _practice_cache


def latest_batch() -> dict:
    files = sorted((data_dir() / "batches").glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for f in files:
        batch = _read(f)
        if batch and batch.get("cases") is not None:
            return batch
    return practice_batch()


def get_batch(batch_id: str) -> dict | None:
    if batch_id.startswith(PRACTICE_PREFIX):
        practice = practice_batch()
        return practice if practice["batch_id"] == batch_id else None
    return _read(data_dir() / "batches" / f"{safe_id(batch_id)}.json")


# Leaderboard 

def _board_path() -> Path:
    return data_dir() / "leaderboard.json"


def record_verdict(batch_id: str, player: str, case_id: str, result: dict) -> tuple[dict, bool]:
    with _lock:
        board = _read(_board_path()) or {}
        entry = board.setdefault(batch_id, {}).setdefault(player, {"score": 0, "cases": {}})
        if case_id in entry["cases"]:
            return entry["cases"][case_id], False
        entry["cases"][case_id] = result
        entry["score"] += result["points"]
        _atomic_write(_board_path(), board)
        return result, True


def player_state(batch_id: str, player: str) -> dict:
    board = _read(_board_path()) or {}
    return board.get(batch_id, {}).get(player, {"score": 0, "cases": {}})


def leaderboard(batch_id: str) -> list[dict]:
    board = (_read(_board_path()) or {}).get(batch_id, {})
    rows = []
    for player, entry in board.items():
        outcomes = [c["outcome"] for c in entry["cases"].values()]
        rows.append({"player": player, "score": entry["score"], "cases": len(outcomes),
                     "missed_sars": outcomes.count("missed_sar")})
    return sorted(rows, key=lambda r: (-r["score"], r["missed_sars"]))
