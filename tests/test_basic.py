import sys, os
import pytest
from datetime import datetime, date
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import src.app as app_module
import streamlit as st
from src.tasks import (
    load_tasks, save_tasks, generate_unique_id,
    filter_tasks_by_priority, filter_tasks_by_category,
    filter_tasks_by_completion, search_tasks, get_overdue_tasks
)
from src.app import (
    build_task, get_filter_options, handle_new_task,
    compute_filters, decide_task_action,
    show_filters, show_sidebar,
    complete_task, delete_task, display_tasks, main
)
import subprocess

# Minimal context‑manager stub for any 'with' blocks
class DummyCM:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): pass

# --- tasks.py tests --------------------------------------

def test_generate_unique_id_empty():
    assert generate_unique_id([]) == 1

def test_generate_unique_id_non_empty():
    assert generate_unique_id([{"id":2},{"id":7}]) == 8

def test_filter_and_search_and_completion():
    tasks = [
        {"priority":"H","category":"A","completed":False, "title":"","description":""},
        {"priority":"L","category":"B","completed":True,  "title":"","description":""},
    ]
    assert filter_tasks_by_priority(tasks,"H") == [tasks[0]]
    assert filter_tasks_by_category(tasks,"B") == [tasks[1]]
    assert filter_tasks_by_completion(tasks,True) == [tasks[1]]
    # search
    tasks2 = [{"title":"Foo","description":"Bar"}]
    assert search_tasks(tasks2,"foo") == tasks2

def test_load_and_save(tmp_path):
    fp = tmp_path/"t.json"
    data = [{"id":1,"title":"x"}]
    save_tasks(data, file_path=str(fp))
    assert load_tasks(file_path=str(fp)) == data

def test_load_file_not_found(tmp_path):
    assert load_tasks(file_path=str(tmp_path/"nofile.json")) == []

def test_load_invalid_json(tmp_path, capsys):
    bad = tmp_path/"b.json"
    bad.write_text("###")
    out = load_tasks(file_path=str(bad))
    captured = capsys.readouterr().out
    assert "invalid JSON" in captured
    assert out == []

def test_get_overdue(monkeypatch):
    # freeze time in tasks module
    class FakeDT:
        @classmethod
        def now(cls): return datetime(2025,1,2)
    import src.tasks as mod
    monkeypatch.setattr(mod, "datetime", FakeDT)
    tasks = [
        {"due_date":"2025-01-01","completed":False},
        {"due_date":"2025-01-03","completed":False},
    ]
    assert get_overdue_tasks(tasks) == [tasks[0]]


# --- app.py pure‑logic tests -----------------------------

def test_build_task_and_id(monkeypatch):
    base = [{"id":5}]
    fake_now = datetime(2025,4,21,8,0,0)
    class FakeDT:
        @classmethod
        def now(cls): return fake_now
    # patch module datetime
    monkeypatch.setattr(app_module, "datetime", FakeDT)
    t = build_task(base, "T","D","High","C", date(2025,6,6))
    assert t["id"] == 6
    assert t["due_date"] == "2025-06-06"
    assert t["created_at"].startswith("2025-04-21")

def test_filters_and_compute():
    cats, pris = get_filter_options([{"category":"Z"},{"category":"A"}])
    assert cats == ["A","Z"]
    assert pris == ["High","Medium","Low"]
    assert compute_filters("X","Y",True) == ("X","Y",True)

@pytest.mark.parametrize("comp,cp,dp,exp", [
    (False, True, False, "complete"),
    (True,  True, False, "undo"),
    (False, False, True, "delete"),
    (False, False, False, None),
])
def test_decide(comp,cp,dp,exp):
    assert decide_task_action({"completed":comp}, cp, dp) == exp

def test_handle_new_task_and_callbacks(tmp_path, monkeypatch):
    # point DEFAULT_TASKS_FILE to tmp file
    fp = tmp_path/"tasks.json"
    monkeypatch.setenv("DEFAULT_TASKS_FILE", str(fp))
    tasks = []
    new = handle_new_task(tasks, True, "A","B","M","C", date(2025,7,7))
    assert new in tasks
    # complete_task
    fp.write_text("[]")
    complete_task(new["id"])
    # delete_task
    delete_task(new["id"])
    assert load_tasks(file_path=str(fp)) == []


# --- Streamlit UI tests ----------------------------------

def test_show_filters_ui(monkeypatch):
    monkeypatch.setattr(st, "columns", lambda n: (DummyCM(), DummyCM()))
    monkeypatch.setattr(st, "selectbox", lambda *a,**k: "All")
    monkeypatch.setattr(st, "checkbox", lambda *a,**k: False)
    assert show_filters([]) == ("All","All",False)

def test_show_sidebar_does_not_crash(monkeypatch):
    class FormStub:
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def text_input(self,*a): return ""
        def text_area(self,*a): return ""
        def selectbox(self,*a): return ""
        def date_input(self,*a): return date.today()
        def form_submit_button(self,*a): return False
    monkeypatch.setattr(st.sidebar, "form", lambda *a,**k: FormStub())
    show_sidebar([])  # no exception


# --- display_tasks: isolate callbacks --------------------

def test_display_tasks_complete_and_delete(monkeypatch):
    # Full task dict
    full_task = {
        "id": 1,
        "title": "T",
        "description": "D",
        "priority": "High",
        "category": "C",
        "due_date": "2025-01-01",
        "completed": False
    }

    # Prepare shared task_list for stubs
    task_list = [full_task.copy()]

    # Stub complete_task to toggle in-memory task_list
    def stub_complete(task_id):
        for t in task_list:
            if t["id"] == task_id:
                t["completed"] = not t["completed"]
    monkeypatch.setattr(app_module, "complete_task", stub_complete)

    # Stub delete_task to remove from in-memory task_list
    def stub_delete(task_id):
        nonlocal task_list
        task_list = [t for t in task_list if t["id"] != task_id]
    monkeypatch.setitem(locals(), 'task_list', task_list)  # ensure closure capture
    monkeypatch.setattr(app_module, "delete_task", stub_delete)

    # Phase 1: only Complete fires
    class Cst:
        def columns(self,s): return (DummyCM(), DummyCM())
        def markdown(self,*a): pass
        def write(self,*a): pass
        def caption(self,*a): pass
        def button(self,label,key,**kw):
            if key.startswith("complete_"):
                kw["on_click"](task_list[0]["id"])
                return True
            return False

    monkeypatch.setattr(st, "columns", Cst().columns)
    monkeypatch.setattr(st, "button", Cst().button)

    display_tasks(task_list)
    try:
        assert task_list and task_list[0]["completed"] is True
    except AssertionError:
        pytest.fail("Complete button did not toggle 'completed' flag as expected")

    # Phase 2: only Delete fires
    class Dst(Cst):
        def button(self,label,key,**kw):
            if key.startswith("delete_"):
                kw["on_click"](task_list[0]["id"])
                return True
            return False

    monkeypatch.setattr(st, "button", Dst().button)

    task_list[0]["completed"] = True
    display_tasks(task_list)
    try:
        assert task_list == []
    except AssertionError:
        pytest.fail("Delete button did not remove the task as expected")


def test_main_runs_without_error(monkeypatch):
    monkeypatch.setattr(st, "title", lambda *a,**k: None)
    monkeypatch.setattr(st, "button", lambda *a,**k: False)
    monkeypatch.setattr(st, "columns", lambda *a,**k: (DummyCM(), DummyCM()))
    monkeypatch.setattr(st, "selectbox", lambda *a,**k: "All")
    monkeypatch.setattr(st, "checkbox", lambda *a,**k: False)
    assert main() is None

def test_start_and_save_edit(monkeypatch):
    # prepare session state
    st.session_state.clear()
    st.session_state.tasks = [{
        "id": 1,
        "title": "A",
        "description": "D",
        "priority": "Low",
        "category": "C",
        "due_date": "2025-01-01",
        "completed": False,
        "created_at": "t"
    }]
    monkeypatch.setattr(app_module, "save_tasks", lambda tasks: None)
    # start edit
    app_module.start_edit(1)
    assert st.session_state.edit_id == 1
    assert st.session_state.tasks == []
    # set edited fields
    prefix = "edit_1_"
    st.session_state[prefix + "title"] = "X"
    st.session_state[prefix + "description"] = "Y"
    st.session_state[prefix + "category"] = "C2"
    st.session_state[prefix + "priority"] = "High"
    st.session_state[prefix + "due_date"] = "2025-02-02"
    # save edit
    app_module.save_edit(1)
    assert st.session_state.edit_id is None
    assert all(t["title"] == "X" for t in st.session_state.tasks)

def test_render_task_branches(monkeypatch):
    calls = []
    monkeypatch.setattr(st, "columns", lambda *a, **k: (DummyCM(), DummyCM()))
    monkeypatch.setattr(st, "markdown", lambda txt, **kw: calls.append(txt))
    monkeypatch.setattr(st, "write", lambda *a, **k: calls.append("write"))
    monkeypatch.setattr(st, "caption", lambda txt: calls.append(txt))
    # overdue True
    app_module.render_task({
        "id": 1, "title": "T", "description": "D",
        "priority": "P", "category": "C", "due_date": "d", "completed": False
    }, overdue=True)
    # overdue False (completed)
    app_module.render_task({
        "id": 2, "title": "U", "description": "E",
        "priority": "P", "category": "C", "due_date": "d", "completed": True
    }, overdue=False)
    assert any("<span" in c for c in calls)
    assert any("~~U~~" in c for c in calls)

def test_run_helpers(monkeypatch):
    ran, md = [], []
    monkeypatch.setattr(subprocess, "run", lambda cmd: ran.append(cmd))
    monkeypatch.setattr(st, "markdown", lambda txt, **k: md.append(txt))
    app_module.run_unit_tests()
    app_module.run_param_tests()
    app_module.run_mock_tests()
    app_module.run_cov_tests()
    app_module.run_html_report()
    assert ["pytest", "-q"] in ran
    assert ["pytest", "tests/test_advanced.py", "-q"] in ran
    assert ["pytest", "--cov=src", "--cov-report=html", "-q"] in ran
    assert ["pytest", "--html=report.html", "--self-contained-html", "-q"] in ran
    assert any("View Coverage Report" in m for m in md)
    assert any("View HTML Report" in m for m in md)

def test_show_sidebar_adds_task(monkeypatch):
    class FS:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def text_input(self, *a, **k): return "Z"
        def text_area(self, *a, **k): return "D"
        def selectbox(self, *a, **k): return "Low"
        def date_input(self, *a, **k): return __import__("datetime").date.today()
        def form_submit_button(self, *a, **k): return True
    monkeypatch.setattr(st.sidebar, "form", lambda *a, **k: FS())
    got = []
    monkeypatch.setattr(st.sidebar, "success", lambda msg: got.append(msg))
    st.session_state.clear()
    st.session_state.tasks = []
    app_module.show_sidebar(st.session_state.tasks)
    assert got and "added" in got[0]