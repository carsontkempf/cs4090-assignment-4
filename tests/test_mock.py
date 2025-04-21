import pytest
from src.app import handle_new_task
from datetime import date
from src.tasks import save_tasks

def test_handle_new_task_calls_save(tmp_path, mocker):
    tasks = []
    save_spy = mocker.patch("src.app.save_tasks")
    new = handle_new_task(tasks, True, "T", "D", "M", "C", date(2025,3,3))
    save_spy.assert_called_once_with(tasks)
    assert new["title"] == "T"