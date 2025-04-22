# tests/test_mock.py

import pytest
from datetime import date, datetime

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
from src.tasks import (
    load_tasks,
    save_tasks,
    filter_tasks_by_completion,
    search_tasks,
    get_overdue_tasks,
)

# Dummy context manager for UI stubs
class DummyCM:
    def __enter__(self): return self
    def __exit__(self, *args): pass

# --- App logic tests -----------------------------------

def test_handle_new_task_calls_save(tmp_path, monkeypatch):
    fp = tmp_path / "tasks.json"
    monkeypatch.setenv("DEFAULT_TASKS_FILE", str(fp))
    monkeypatch.setattr(tasks_module, "DEFAULT_TASKS_FILE", str(fp))
    monkeypatch.setattr(app_module, "save_tasks",
        lambda tasks_list: tasks_module.save_tasks(tasks_list, file_path=str(fp)))
    monkeypatch.setattr(app_module, "load_tasks",
        lambda: tasks_module.load_tasks(file_path=str(fp)))

    tasks = []
    new = handle_new_task(tasks, True, "T", "D", "M", "C", date(2025, 3, 3))
    assert new in tasks
    saved = tasks_module.load_tasks(file_path=str(fp))
    assert saved and saved[0]["title"] == "T"

def test_handle_new_task_rejects_empty_title():
    result = handle_new_task([], True, "", "desc", "Low", "Cat", date(2025, 1, 1))
    assert result is None

def test_build_task_and_id(monkeypatch):
    fake_now = datetime(2025, 4, 21, 8, 0, 0)
    class FakeDT:
        @classmethod
        def now(cls): return fake_now
    monkeypatch.setattr(app_module, "datetime", FakeDT)
    t = build_task([{"id":5}], "X", "Y", "High", "Z", date(2025, 1, 1))
    assert t["id"] == 6
    assert t["due_date"] == "2025-01-01"
    assert t["created_at"].startswith("2025-04-21")

def test_get_filter_options_variants():
    cats, pris = get_filter_options(
        [{"category":"Z"}, {"category":"A"}, {"category":"Z"}]
    )
    assert cats == ["A", "Z"]
    assert pris == ["High", "Medium", "Low"]

def test_compute_and_decide_actions():
    assert compute_filters("A","B",False) == ("A","B",False)
    assert decide_task_action({"completed":False}, True, False) == "complete"
    assert decide_task_action({"completed":True}, True, False) == "undo"
    assert decide_task_action({"completed":False}, False, True) == "delete"
    assert decide_task_action({"completed":False}, False, False) is None

# --- Task module tests -------------------------------

def test_load_tasks_file_not_found(tmp_path):
    fp = tmp_path / "nofile.json"
    assert load_tasks(file_path=str(fp)) == []

def test_load_tasks_invalid_json(tmp_path, capsys):
    fp = tmp_path / "bad.json"
    fp.write_text("###")
    out = load_tasks(file_path=str(fp))
    captured = capsys.readouterr().out
    assert "invalid JSON" in captured
    assert out == []

def test_save_then_load(tmp_path):
    fp = tmp_path / "t.json"
    data = [{"id":1,"title":"x"}]
    save_tasks(data, file_path=str(fp))
    assert load_tasks(file_path=str(fp)) == data

def test_filter_completion_and_search():
    tasks = [
        {"completed":True, "title":"foo", "description":"bar"},
        {"completed":False, "title":"baz", "description":"qux"},
    ]
    assert filter_tasks_by_completion(tasks, True) == [tasks[0]]
    assert filter_tasks_by_completion(tasks, False) == [tasks[1]]
    assert search_tasks(tasks, "QUX") == [tasks[1]]
    assert search_tasks(tasks, "none") == []

def test_get_overdue_tasks(monkeypatch):
    class FakeDT:
        @classmethod
        def now(cls): return datetime(2025,1,2)
    monkeypatch.setattr(tasks_module, "datetime", FakeDT)
    tasks = [
        {"due_date":"2025-01-01","completed":False},
        {"due_date":"2025-01-02","completed":False},
        {"due_date":"2025-01-00","completed":True},
    ]
    assert get_overdue_tasks(tasks) == [tasks[0]]

# --- Run-button integration tests ---------------------

@pytest.mark.parametrize("label,args,link", [
    ("Run Unit Tests", ["pytest","-q"], None),
    ("Run Coverage", ["pytest","--cov=src","--cov-report=html","-q"], "[View Coverage Report](htmlcov/index.html)"),
    ("Run Param Tests", ["pytest","tests/test_param.py","-q"], None),
    ("Run Mock Tests", ["pytest","tests/test_mock.py","-q"], None),
    ("Run HTML Report", ["pytest","--html=report.html","--self-contained-html","-q"], "[View HTML Report](report.html)"),
])
def test_run_button_commands(monkeypatch, label, args, link):
    calls = []
    monkeypatch.setattr(app_module.subprocess, "run", lambda cmd: calls.append(cmd))
    monkeypatch.setattr(app_module, "load_tasks", lambda: [])
    monkeypatch.setattr(app_module.st, "title", lambda *a,**k: None)
    monkeypatch.setattr(app_module.st, "sidebar", type("SB", (), {
        "header": lambda *a,**k: None,
        "form": lambda *a,**k: DummyCM()
    }))
    monkeypatch.setattr(app_module.st, "header", lambda *a,**k: None)
    monkeypatch.setattr(app_module.st, "columns", lambda *a,**k: (DummyCM(), DummyCM()))
    monkeypatch.setattr(app_module.st, "selectbox", lambda *a,**k: "All")
    monkeypatch.setattr(app_module.st, "checkbox", lambda *a,**k: False)
    md = []
    monkeypatch.setattr(app_module.st, "markdown", lambda txt: md.append(txt))
    monkeypatch.setattr(app_module.st, "button", lambda lbl, **kw: lbl == label)
    app_module.main()
    assert calls[0] == args
    if link:
        assert link in md


# Additional tests for filters, pure functions, and UI flows
def test_filter_priority_and_category():
    tasks = [{"priority":"High","category":"A"},{"priority":"Low","category":"B"}]
    assert tasks_module.filter_tasks_by_priority(tasks, "High") == [tasks[0]]
    assert tasks_module.filter_tasks_by_category(tasks, "B") == [tasks[1]]

def test_delete_task_pure(monkeypatch):
    calls = []
    monkeypatch.setattr(app_module, "load_tasks", lambda: [{"id":1},{"id":2}])
    monkeypatch.setattr(app_module, "save_tasks", lambda tasks_list: calls.append(tasks_list))
    delete_task(1)
    assert calls and calls[0] == [{"id":2}]

def test_complete_task_pure(monkeypatch):
    calls = []
    monkeypatch.setattr(app_module, "load_tasks", lambda: [{"id":3,"completed":False},{"id":4,"completed":True}])
    monkeypatch.setattr(app_module, "save_tasks", lambda tasks_list: calls.append(tasks_list))
    complete_task(3)
    assert calls and calls[0][0]["completed"] is True

def test_show_sidebar_adds_task(monkeypatch):
    calls = []
    monkeypatch.setattr(app_module.st.sidebar, "header", lambda *a,**k: None)
    class DummyForm:
        def __enter__(self): return self
        def __exit__(self, *a): pass
    monkeypatch.setattr(app_module.st.sidebar, "form", lambda *a,**k: DummyForm())
    monkeypatch.setattr(app_module.st.sidebar, "success", lambda msg: calls.append(msg))
    # Monkeypatch top-level st functions used in show_sidebar
    monkeypatch.setattr(app_module.st, "text_input", lambda *a, **k: "Title")
    monkeypatch.setattr(app_module.st, "text_area", lambda *a, **k: "Desc")
    monkeypatch.setattr(app_module.st, "selectbox", lambda *a, **k: "Work")
    monkeypatch.setattr(app_module.st, "date_input", lambda *a, **k: date(2025,5,5))
    monkeypatch.setattr(app_module.st, "form_submit_button", lambda *a, **k: True)
    app_module.show_sidebar([])
    assert "Task added!" in calls

def test_show_filters_ui(monkeypatch):
    monkeypatch.setattr(app_module.st, "columns", lambda n: (DummyCM(), DummyCM()))
    monkeypatch.setattr(app_module.st, "selectbox", lambda *a,**k: "Other")
    monkeypatch.setattr(app_module.st, "checkbox", lambda *a,**k: True)
    # Import show_filters from app_module
    from src.app import show_filters
    assert show_filters([]) == ("Other", "Other", True)


# --- Additional coverage: display_tasks and __main__ execution ---
import runpy
import streamlit as real_st
import subprocess as real_subprocess
import src.tasks as real_tasks

def test_display_tasks_flow(monkeypatch):
    # stub UI rendering calls
    monkeypatch.setattr(app_module.st, "columns", lambda *args, **kwargs: (DummyCM(), DummyCM()))
    monkeypatch.setattr(app_module.st, "markdown", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module.st, "write", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module.st, "caption", lambda *args, **kwargs: None)
    # capture calls
    calls = []
    monkeypatch.setattr(app_module, "complete_task", lambda task_id: calls.append(("complete", task_id)))
    monkeypatch.setattr(app_module, "delete_task", lambda task_id: calls.append(("delete", task_id)))
    # simulate pressing "Complete"
    monkeypatch.setattr(app_module.st, "button",
        lambda label, key, on_click=None, args=None: (on_click(*args), True)[1] if key.startswith("complete_") else False)
    task = {"id": 1, "title": "T", "description": "D",
            "priority": "P", "category": "C", "due_date": "2025-01-01", "completed": False}
    app_module.display_tasks([task])
    assert ("complete", 1) in calls

    # simulate pressing "Delete"
    calls.clear()
    monkeypatch.setattr(app_module.st, "button",
        lambda label, key, on_click=None, args=None: (on_click(*args), True)[1] if key.startswith("delete_") else False)
    app_module.display_tasks([task])
    assert ("delete", 1) in calls


def test_run_module_main(monkeypatch, tmp_path):
    # stub streamlit functions globally
    import streamlit as st_mod
    monkeypatch.setattr(st_mod, "title", lambda *args, **kwargs: None)
    monkeypatch.setattr(st_mod, "sidebar", type("SB", (), {
        "header": lambda *args, **kwargs: None,
        "form": lambda *args, **kwargs: DummyCM(),
        "success": lambda *args, **kwargs: None
    }))
    monkeypatch.setattr(st_mod, "header", lambda *args, **kwargs: None)
    monkeypatch.setattr(st_mod, "columns", lambda *args, **kwargs: (DummyCM(), DummyCM()))
    monkeypatch.setattr(st_mod, "selectbox", lambda *args, **kwargs: "All")
    monkeypatch.setattr(st_mod, "checkbox", lambda *args, **kwargs: False)
    monkeypatch.setattr(st_mod, "markdown", lambda *args, **kwargs: None)
    monkeypatch.setattr(st_mod, "button", lambda *args, **kwargs: False)
    # stub subprocess.run
    monkeypatch.setattr(real_subprocess, "run", lambda *args, **kwargs: None)
    # stub tasks load/save paths
    fp = tmp_path / "tasks.json"
    monkeypatch.setenv("DEFAULT_TASKS_FILE", str(fp))
    monkeypatch.setattr(real_tasks, "DEFAULT_TASKS_FILE", str(fp))
    # run module as script
    import sys
    sys.modules.pop("src.app", None)
    runpy.run_module("src.app", run_name="__main__")