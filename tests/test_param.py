import sys, os
import pytest
from datetime import datetime, date
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import src.tasks as tasks_module
from src.tasks import (
    load_tasks,
    save_tasks,
    generate_unique_id,
    filter_tasks_by_priority,
    filter_tasks_by_category,
    filter_tasks_by_completion,
    search_tasks,
    get_overdue_tasks,
)
import src.app as app_module
from src.app import (
    build_task,
    compute_filters,
    decide_task_action,
    handle_new_task,
    complete_task,
    delete_task,
)

# --- tasks.py parameterized logic tests ---

@pytest.mark.parametrize("tasks_list,expected", [
    ([], 1),
    ([{"id":2},{"id":7}], 8),
])
def test_generate_unique_id(tasks_list, expected):
    assert generate_unique_id(tasks_list) == expected

@pytest.mark.parametrize("tasks_list,priority,expected", [
    ([{"priority":"High"},{"priority":"Low"}], "High", [{"priority":"High"}]),
    ([{"priority":"X"},{"priority":"X"}], "X", [{"priority":"X"},{"priority":"X"}]),
])
def test_filter_tasks_by_priority(tasks_list, priority, expected):
    assert filter_tasks_by_priority(tasks_list, priority) == expected

@pytest.mark.parametrize("tasks_list,category,expected", [
    ([{"category":"A"},{"category":"B"}], "B", [{"category":"B"}]),
])
def test_filter_tasks_by_category(tasks_list, category, expected):
    assert filter_tasks_by_category(tasks_list, category) == expected

@pytest.mark.parametrize("tasks_list,completed,expected", [
    ([{"completed":True},{"completed":False}], True, [{"completed":True}]),
    ([{"completed":True},{"completed":False}], False, [{"completed":False}]),
])
def test_filter_tasks_by_completion(tasks_list, completed, expected):
    assert filter_tasks_by_completion(tasks_list, completed) == expected

@pytest.mark.parametrize("tasks_list,query,expected", [
    ([{"title":"Foo","description":"Bar"}], "foo", [{"title":"Foo","description":"Bar"}]),
    ([{"title":"X","description":"Y"}], "z", []),
])
def test_search_tasks(tasks_list, query, expected):
    assert search_tasks(tasks_list, query) == expected

def test_get_overdue_tasks(monkeypatch):
    class FakeDT:
        @classmethod
        def now(cls):
            return datetime(2025, 1, 2)
    monkeypatch.setattr(tasks_module, "datetime", FakeDT)
    tasks = [
        {"due_date":"2025-01-01","completed":False},
        {"due_date":"2025-01-03","completed":False},
        {"due_date":"2025-01-00","completed":True},
    ]
    assert get_overdue_tasks(tasks) == [tasks[0]]

def test_load_and_save_tasks(tmp_path):
    fp = tmp_path / "t.json"
    data = [{"id":1,"title":"x"}]
    save_tasks(data, file_path=str(fp))
    assert load_tasks(file_path=str(fp)) == data

def test_load_tasks_file_not_found(tmp_path):
    missing = tmp_path / "no.json"
    assert load_tasks(file_path=str(missing)) == []

def test_load_tasks_invalid_json(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("###")
    out = load_tasks(file_path=str(bad))
    captured = capsys.readouterr().out
    assert "invalid JSON" in captured
    assert out == []

# --- app.py parameterized logic tests ---

@pytest.mark.parametrize("tasks_list,title,desc,pri,cat,due,expected_id", [
    ([], "A","B","High","Work", date(2025,1,1), 1),
    ([{"id":1}], "X","Y","Low","Other", date(2025,2,2), 2),
])
def test_build_task_param(tasks_list, title, desc, pri, cat, due, expected_id):
    task = build_task(tasks_list, title, desc, pri, cat, due)
    assert task["id"] == expected_id
    assert task["priority"] == pri
    assert task["due_date"] == due.strftime("%Y-%m-%d")

@pytest.mark.parametrize("cat,pri,show,expected", [
    ("A","B",True, ("A","B",True)),
    ("All","Low",False, ("All","Low",False)),
])
def test_compute_filters(cat, pri, show, expected):
    assert compute_filters(cat, pri, show) == expected

@pytest.mark.parametrize("completed,cp,dp,expected", [
    (False, True, False, "complete"),
    (True,  True, False, "undo"),
    (False, False, True, "delete"),
    (False, False, False, None),
])
def test_decide_task_action(completed, cp, dp, expected):
    assert decide_task_action({"completed":completed}, cp, dp) == expected

def test_handle_new_task_pure():
    tasks = []
    due = date(2025,3,3)
    new = handle_new_task(tasks, True, "T","D","M","C", due)
    assert new in tasks
    assert new["title"] == "T"
    assert handle_new_task(tasks, False, "T2","D2","L","O", due) is None

def test_complete_and_delete_pure(monkeypatch):
    out = []
    monkeypatch.setattr(app_module, "load_tasks", lambda: [{"id":10,"completed":False}])
    monkeypatch.setattr(app_module, "save_tasks", lambda lst: out.append(lst))
    complete_task(10)
    assert out and out[0][0]["completed"] is True
    out.clear()
    delete_task(10)
    assert out and out[0] == []

def test_display_tasks_buttons(monkeypatch):
    # from src.app import display_tasks
    out = []
    monkeypatch.setattr(app_module.st, "columns", lambda *a, **k: (DummyCM(), DummyCM()))
    monkeypatch.setattr(app_module.st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(app_module.st, "write", lambda *a, **k: None)
    monkeypatch.setattr(app_module.st, "caption", lambda *a, **k: None)
    # Simulate complete and delete button
    def fake_button(label, key, on_click=None, args=None):
        if key.startswith("complete_"):
            out.append(f"complete {args[0]}")
            return True
        if key.startswith("delete_"):
            out.append(f"delete {args[0]}")
            return True
        return False
    monkeypatch.setattr(app_module.st, "button", fake_button)
    tasks = [
        {
            "id": 1,
            "title": "Task 1",
            "description": "Desc 1",
            "priority": "High",
            "category": "Work",
            "due_date": "2025-01-01",
            "completed": False,
        },
        {
            "id": 2,
            "title": "Task 2",
            "description": "Desc 2",
            "priority": "Low",
            "category": "Personal",
            "due_date": "2025-01-02",
            "completed": True,
        },
    ]
    app_module.display_tasks(tasks)
    assert "complete 1" in out
    assert "delete 2" in out

# --- UI and main execution tests for app.py ---

import runpy
import streamlit as st_mod
import subprocess as real_subprocess
import src.tasks as real_tasks

# Dummy context manager
class DummyCM:
    def __enter__(self): return self
    def __exit__(self, *args): pass

def test_show_sidebar_ui(monkeypatch):
    calls = []
    monkeypatch.setattr(st_mod.sidebar, "header", lambda *a,**k: None)
    monkeypatch.setattr(st_mod.sidebar, "form", lambda *a,**k: DummyCM())
    monkeypatch.setattr(st_mod.sidebar, "success", lambda msg: calls.append(msg))
    # stub st functions inside form
    monkeypatch.setattr(st_mod, "text_input", lambda *a, **k: "T")
    monkeypatch.setattr(st_mod, "text_area", lambda *a, **k: "D")
    monkeypatch.setattr(st_mod, "selectbox", lambda *a, **k: "Low")
    monkeypatch.setattr(st_mod, "date_input", lambda *a, **k: date(2025,5,5))
    monkeypatch.setattr(st_mod, "form_submit_button", lambda *a, **k: True)
    from src.app import show_sidebar
    show_sidebar([])
    assert "Task added!" in calls

def test_show_filters_ui(monkeypatch):
    monkeypatch.setattr(st_mod, "columns", lambda *a,**k: (DummyCM(),DummyCM()))
    monkeypatch.setattr(st_mod, "selectbox", lambda *a, **k: "Other")
    monkeypatch.setattr(st_mod, "checkbox", lambda *a, **k: True)
    from src.app import show_filters
    assert show_filters([]) == ("Other","Other",True)

def test_display_tasks_buttons_ui(monkeypatch):
    # stub UI render
    monkeypatch.setattr(app_module.st, "columns", lambda *a, **k: (DummyCM(),DummyCM()))
    monkeypatch.setattr(app_module.st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(app_module.st, "write", lambda *a, **k: None)
    monkeypatch.setattr(app_module.st, "caption", lambda *a, **k: None)
    # capture calls
    calls = []
    monkeypatch.setattr(app_module, "complete_task", lambda tid: calls.append(("C",tid)))
    monkeypatch.setattr(app_module, "delete_task", lambda tid: calls.append(("D",tid)))
    # simulate complete button
    monkeypatch.setattr(app_module.st, "button",
        lambda label, key, on_click=None, args=None: (on_click(*args), True)[1] if key.startswith("complete_") else False)
    task = {"id":5,"title":"X","description":"Y","priority":"P","category":"C","due_date":"2025-01-01","completed":False}
    app_module.display_tasks([task])
    assert ("C",5) in calls
    # simulate delete
    calls.clear()
    monkeypatch.setattr(app_module.st, "button",
        lambda label, key, on_click=None, args=None: (on_click(*args), True)[1] if key.startswith("delete_") else False)
    app_module.display_tasks([task])
    assert ("D",5) in calls

def test_main_execution(monkeypatch, tmp_path):
    # stub streamlit functions
    monkeypatch.setenv("DEFAULT_TASKS_FILE", str(tmp_path/"tasks.json"))
    monkeypatch.setattr(real_tasks, "DEFAULT_TASKS_FILE", str(tmp_path/"tasks.json"))
    monkeypatch.setattr(st_mod, "title", lambda *a,**k: None)
    monkeypatch.setattr(st_mod.sidebar, "header", lambda *a,**k: None)
    monkeypatch.setattr(st_mod.sidebar, "form", lambda *a,**k: DummyCM())
    monkeypatch.setattr(st_mod.sidebar, "success", lambda *a,**k: None)
    monkeypatch.setattr(st_mod, "header", lambda *a,**k: None)
    monkeypatch.setattr(st_mod, "columns", lambda *a,**k: (DummyCM(),DummyCM()))
    monkeypatch.setattr(st_mod, "selectbox", lambda *a,**k: "All")
    monkeypatch.setattr(st_mod, "checkbox", lambda *a,**k: False)
    monkeypatch.setattr(st_mod, "markdown", lambda *a,**k: None)
    monkeypatch.setattr(st_mod, "button", lambda *a, **k: False)
    # stub subprocess.run
    monkeypatch.setattr(real_subprocess, "run", lambda *a,**k: None)
    import sys
    sys.modules.pop("src.app", None)
    runpy.run_module("src.app", run_name="__main__")