from __future__ import annotations

from datetime import datetime, timezone

from airflow.sdk import Asset, dag, task

from aml_detective import engine, store

CASE_BATCHES = Asset("aml_case_batches")


@dag(
    dag_id="aml_detective_case_factory",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    doc_md=__doc__,
    tags=["aml-detective", "hackathon"],
)
def aml_detective_case_factory():
    @task
    def generate_activity(dag_run=None) -> dict:
        as_of = datetime.now(timezone.utc).date()
        activity = engine.generate_activity(seed=dag_run.run_id, as_of=as_of)
        print(f"Generated {len(activity['accounts'])} accounts and "
              f"{len(activity['transactions'])} transactions for {as_of}.")
        return activity

    @task
    def screen_transactions(activity: dict) -> list[dict]:
        alerts = engine.screen(activity)
        for a in alerts:
            codes = ", ".join(h["code"] for h in a["hits"])
            print(f"{a['account_id']}: risk {a['risk_score']} ({codes})")
        print(f"{len(alerts)} alerts raised from {len(activity['accounts'])} accounts.")
        return alerts

    @task(outlets=[CASE_BATCHES])
    def publish_case_batch(activity: dict, alerts: list[dict], dag_run=None) -> dict:
        batch_id = store.safe_id(f"shift-{dag_run.run_id}")
        batch = engine.assemble_batch(activity, alerts, batch_id=batch_id, source="dag",
                                      run_id=dag_run.run_id)
        path = store.save_batch(batch)
        print(f"Published {len(batch['cases'])} cases to {path}")
        return {"batch_id": batch_id, "cases": len(batch["cases"]), "path": str(path)}

    activity = generate_activity()
    alerts = screen_transactions(activity)
    publish_case_batch(activity, alerts)


aml_detective_case_factory()
