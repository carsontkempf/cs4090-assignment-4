# tests/test_mock.py

import pytest
from datetime import date

import src.app as app_module
from src.app import (
    handle_new_task,
    build_task,
    complete_task,
    delete_task,
    get_filter_options,
    compute_filters,
    decide_task_action,
)
import src.tasks as tasks_module
from src.tasks import load_tasks, save_tasks

def test_handle_new_task_calls_save(tmp_path, monkeypatch):
    fp = tmp_path / "tasks.json"

    # 1) Redirect DEFAULT_TASKS_FILE in tasks_module
    monkeypatch.setenv("DEFAULT_TASKS_FILE", str(fp))
    monkeypatch.setattr(tasks_module, "DEFAULT_TASKS_FILE", str(fp))

    # 2) Patch app_module.save_tasks & load_tasks to force file_path=fp
    monkeypatch.setattr(
        app_module,
        "save_tasks",
        lambda tasks_list: tasks_module.save_tasks(tasks_list, file_path=str(fp))
    )
    monkeypatch.setattr(
        app_module,
        "load_tasks",
        lambda: tasks_module.load_tasks(file_path=str(fp))
    )

    # Run handle_new_task
    tasks = []
    new = handle_new_task(tasks, True, "T", "D", "M", "C", date(2025, 3, 3))
    assert new in tasks

    # Saved file should now contain our new task
    saved = tasks_module.load_tasks(file_path=str(fp))
    if not saved or saved[0].get("title") != "T":
        pytest.fail(f"Expected saved task title 'T', got {saved}")

def test_build_task_and_filters():
    base = [{"id": 1}]
    bt = build_task(base, "X", "Y", "High", "Z", date(2025, 1, 1))
    assert bt["id"] == 2

    cats, pris = get_filter_options([{"category": "A"}, {"category": "B"}])
    assert cats == ["A", "B"]
    assert pris == ["High", "Medium", "Low"]

    assert compute_filters("A", "H", True) == ("A", "H", True)
    assert decide_task_action({"completed": False}, True, False) == "complete"

def test_complete_and_delete_task(tmp_path, monkeypatch):
    fp = tmp_path / "tasks.json"

    # 1) Same redirects
    monkeypatch.setenv("DEFAULT_TASKS_FILE", str(fp))
    monkeypatch.setattr(tasks_module, "DEFAULT_TASKS_FILE", str(fp))
    monkeypatch.setattr(
        app_module,
        "save_tasks",
        lambda tasks_list: tasks_module.save_tasks(tasks_list, file_path=str(fp))
    )
    monkeypatch.setattr(
        app_module,
        "load_tasks",
        lambda: tasks_module.load_tasks(file_path=str(fp))
    )

    # Write initial tasks via tasks_module
    tasks_module.save_tasks([{"id": 10, "completed": False}], file_path=str(fp))

    # Complete
    complete_task(10)
    result1 = tasks_module.load_tasks(file_path=str(fp))
    if not result1 or result1[0].get("completed") is not True:
        pytest.fail(f"Expected task marked completed, got {result1}")

    # Delete
    delete_task(10)
    result2 = tasks_module.load_tasks(file_path=str(fp))
    if result2:
        pytest.fail(f"Expected task deleted, got {result2}")