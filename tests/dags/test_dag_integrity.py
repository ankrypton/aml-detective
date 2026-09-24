from airflow.models.dagbag import DagBag


def test_no_import_errors():
    bag = DagBag(include_examples=False)
    assert bag.import_errors == {}


def test_case_factory_shape():
    dag = DagBag(include_examples=False).dags["aml_detective_case_factory"]
    assert [t.task_id for t in dag.tasks] == ["generate_activity", "screen_transactions", "publish_case_batch"]
    publish = dag.get_task("publish_case_batch")
    assert any(getattr(o, "name", None) == "aml_case_batches" for o in publish.outlets)
