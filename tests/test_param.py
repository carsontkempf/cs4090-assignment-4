import pytest
from src.app import compute_filters, build_task

@pytest.mark.parametrize(
    "tasks,title,desc,pri,cat,due,expected_id",
    [
        ([], "A", "B", "High", "Work", date(2025,1,1), 1),
        ([{"id":1}], "X", "Y", "Low", "Other", date(2025,2,2), 2),
    ]
)
def test_build_task_param(tasks, title, desc, pri, cat, due, expected_id):
    task = build_task(tasks, title, desc, pri, cat, due)
    assert task["id"] == expected_id
    assert task["priority"] == pri