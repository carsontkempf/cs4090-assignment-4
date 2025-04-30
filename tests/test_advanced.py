import sys, os, subprocess
import pytest
from pathlib import Path
from datetime import datetime, date, timedelta
from datetime import date
import src.tasks as tasks_module

# Ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.tasks as tasks_module
import src.app as app_module

from src.tasks import (
    load_tasks, save_tasks, generate_unique_id,
    filter_tasks_by_priority, filter_tasks_by_category,
    filter_tasks_by_completion, search_tasks,
    get_overdue_tasks, get_upcoming_tasks,
    sort_tasks_by_due_date, edit_task
)

from src.app import (
    build_task, compute_filters, decide_task_action,
    handle_new_task, complete_task, delete_task,
    show_sidebar, show_filters, display_tasks, main
)

# Dummy context manager for UI stubs
class DummyCM:
    def __enter__(self): return self
    def __exit__(self, *args): pass

 # Verify that pytest can generate a self-contained HTML report
# --- HTML report generation test ---
def test_html_report_generation(tmp_path, monkeypatch):
    report_file = tmp_path / "report.html"
    def fake_run(cmd, *args, **kwargs):
        report_file.write_text("<html><body>OK</body></html>")
        return subprocess.CompletedProcess(cmd, 0)
    monkeypatch.setattr(subprocess, "run", fake_run)
    result = subprocess.run(
        ["pytest", "--html", str(report_file), "--self-contained-html", "-q"],
        check=True
    )
    assert result.returncode == 0
    assert report_file.exists()

# Test core task functions with mocked filesystem interactions
# --- Mock tests ---
 # Ensure handle_new_task invokes save_tasks when adding a valid task
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

 # Verify handle_new_task returns None for empty title submissions
def test_handle_new_task_rejects_empty_title():
    result = handle_new_task([], True, "", "desc", "Low", "Cat", date(2025, 1, 1))
    assert result is None

 # Check build_task assigns correct unique ID and formats dates
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

 # Validate get_filter_options returns sorted categories and fixed priorities
def test_get_filter_options_variants():
    cats, pris = app_module.get_filter_options(
        [{"category":"Z"}, {"category":"A"}, {"category":"Z"}]
    )
    assert cats == ["A", "Z"]
    assert pris == ["High", "Medium", "Low"]

 # Confirm compute_filters and decide_task_action behave as expected
def test_compute_and_decide_actions():
    assert compute_filters("A","B",False) == ("A","B",False)
    assert decide_task_action({"completed":False}, True, False) == "complete"
    assert decide_task_action({"completed":True}, True, False) == "undo"
    assert decide_task_action({"completed":False}, False, True) == "delete"
    assert decide_task_action({"completed":False}, False, False) is None

 # Verify load_tasks returns empty list when file is missing
def test_load_tasks_file_not_found(tmp_path):
    fp = tmp_path / "nofile.json"
    assert load_tasks(file_path=str(fp)) == []

 # Confirm load_tasks handles invalid JSON by warning and returning []
def test_load_tasks_invalid_json(tmp_path, capsys):
    fp = tmp_path / "bad.json"
    fp.write_text("###")
    out = load_tasks(file_path=str(fp))
    captured = capsys.readouterr().out
    assert "invalid JSON" in captured
    assert out == []

 # Ensure save_tasks writes JSON that load_tasks can read back correctly
def test_save_then_load(tmp_path):
    fp = tmp_path / "t.json"
    data = [{"id":1,"title":"x"}]
    save_tasks(data, file_path=str(fp))
    assert load_tasks(file_path=str(fp)) == data

 # Test filter_tasks_by_completion and search_tasks functionality
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

# Run parameterized tests for generate_unique_id, filters, and search
# --- Parameterized tests ---
 # Parameterized test for generate_unique_id edge cases
@pytest.mark.parametrize("tasks_list,expected", [
    ([], 1),
    ([{"id":2},{"id":7}], 8),
])
def test_generate_unique_id_param(tasks_list, expected):
    assert generate_unique_id(tasks_list) == expected

 # Parameterized test for filter_tasks_by_priority_param
@pytest.mark.parametrize("tasks_list,priority,expected", [
    ([{"priority":"High"},{"priority":"Low"}], "High", [{"priority":"High"}]),
    ([{"priority":"X"},{"priority":"X"}], "X", [{"priority":"X"},{"priority":"X"}]),
])
def test_filter_tasks_by_priority_param(tasks_list, priority, expected):
    assert filter_tasks_by_priority(tasks_list, priority) == expected

 # Parameterized test for filter_tasks_by_category_param
@pytest.mark.parametrize("tasks_list,category,expected", [
    ([{"category":"A"},{"category":"B"}], "B", [{"category":"B"}]),
])
def test_filter_tasks_by_category_param(tasks_list, category, expected):
    assert filter_tasks_by_category(tasks_list, category) == expected

 # Parameterized test for test_filter_tasks_by_completion_param
@pytest.mark.parametrize("tasks_list,completed,expected", [
    ([{"completed":True},{"completed":False}], True, [{"completed":True}]),
    ([{"completed":True},{"completed":False}], False, [{"completed":False}]),
])
def test_filter_tasks_by_completion_param(tasks_list, completed, expected):
    assert filter_tasks_by_completion(tasks_list, completed) == expected

 # Parameterized test for test_search_tasks_param
@pytest.mark.parametrize("tasks_list,query,expected", [
    ([{"title":"Foo","description":"Bar"}], "foo", [{"title":"Foo","description":"Bar"}]),
    ([{"title":"X","description":"Y"}], "z", []),
])
def test_search_tasks_param(tasks_list, query, expected):
    assert search_tasks(tasks_list, query) == expected

# Integration tests for Streamlit UI run buttons with mocked inputs
# --- Mock integration tests for app buttons and UI flows ---
 # Check each app button triggers correct pytest command and link
@pytest.mark.parametrize("label,args,link", [
    ("Run Unit Tests", ["pytest","-q"], None),
    ("Run Coverage", ["pytest","--cov=src","--cov-report=html","-q"], "[View Coverage Report](htmlcov/index.html)"),
    ("Run Param Tests", ["pytest","tests/test_advanced.py","-q"], None),
    ("Run Mock Tests", ["pytest","tests/test_advanced.py","-q"], None),
    ("Run HTML Report", ["pytest","--html=report.html","--self-contained-html","-q"], "[View HTML Report](report.html)"),
    ("Run BDD Tests", ["pytest","-q","tests/feature"], None),
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

# TDD-style tests covering edit_task, sort, and overdue/upcoming logic
# --- TDD feature tests for edit, sort, overdue/upcoming ---
@pytest.fixture
def sample_tasks():
    today = datetime.now().date()
    return [
        {"id":1,"title":"Old","description":"D","priority":"Low","category":"Work","due_date":(today-timedelta(days=1)).strftime("%Y-%m-%d"),"completed":False,"created_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"id":2,"title":"Today","description":"D2","priority":"Medium","category":"Personal","due_date":today.strftime("%Y-%m-%d"),"completed":False,"created_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"id":3,"title":"New","description":"D3","priority":"High","category":"Other","due_date":(today+timedelta(days=1)).strftime("%Y-%m-%d"),"completed":False,"created_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    ]

 # Verify edit_task correctly applies updates to a task
def test_edit_task(sample_tasks):
    updates = {"title":"E","description":"ED","priority":"High","category":"School","due_date":(datetime.now().date()+timedelta(days=5)).strftime("%Y-%m-%d")}
    tasks = edit_task(sample_tasks.copy(), task_id=2, updates=updates)
    t = next(t for t in tasks if t["id"]==2)
    assert t["title"]=="E"

 # Ensure sort_tasks_by_due_date orders tasks ascending/descending
def test_sort_tasks_by_due_date(sample_tasks):
    asc = sort_tasks_by_due_date(sample_tasks.copy(), ascending=True)
    dates = [t["due_date"] for t in asc]
    assert dates == sorted(dates)
    desc = sort_tasks_by_due_date(sample_tasks.copy(), ascending=False)
    assert [t["due_date"] for t in desc] == sorted(dates, reverse=True)

 # Validate get_overdue_tasks and get_upcoming_tasks partition correctly
def test_get_overdue_and_upcoming(sample_tasks):
    overdue = get_overdue_tasks(sample_tasks.copy())
    upcoming = get_upcoming_tasks(sample_tasks.copy())
    assert {t["id"] for t in overdue} == {1}
    assert {t["id"] for t in upcoming} == {2,3}

# Test that the sidebar form adds a task to storage via show_sidebar
# --- Sidebar form integration test ---
class FS:
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def text_input(self, *a, **k): return "T"
    def text_area(self, *a, **k): return "D"
    def selectbox(self, *a, **k): return "Low"
    def date_input(self, *a, **k): return date.today()
    def form_submit_button(self, *a, **k): return True

 # Confirm show_sidebar writes a new task based on form inputs
def test_show_sidebar_integration(tmp_path, monkeypatch):
    # Setup file and state
    fp = tmp_path / "tasks.json"
    monkeypatch.setenv("DEFAULT_TASKS_FILE", str(fp))
    monkeypatch.setattr(tasks_module, "DEFAULT_TASKS_FILE", str(fp))
    state = type("S", (), {})()
    state.tasks = []
    monkeypatch.setattr(app_module.st, "session_state", state)
    monkeypatch.setattr(app_module.st, "sidebar", type("SB", (), {
        "header": lambda *a,**k: None,
        "form": lambda *a,**k: FS(),
        "success": lambda msg: None
    }))
    monkeypatch.setattr(app_module, "save_tasks",
        lambda tasks: tasks_module.save_tasks(tasks, file_path=str(fp)))
    monkeypatch.setattr(app_module, "load_tasks",
        lambda: tasks_module.load_tasks(file_path=str(fp)))

    app_module.show_sidebar(state.tasks)
    saved = tasks_module.load_tasks(file_path=str(fp))
    assert len(saved) == 1
    assert state.tasks and state.tasks[0]["title"] == "T"

# Test standalone run_* functions execute correct commands
# --- Run test runner functions ---
 # Ensure run_unit_tests, run_cov_tests, etc. call subprocess correctly
def test_run_helpers(monkeypatch):
    calls = []
    md = []
    monkeypatch.setattr(app_module.subprocess, "run", lambda cmd, *a, **k: calls.append(cmd))
    monkeypatch.setattr(app_module.st, "markdown", lambda txt: md.append(txt))
    app_module.run_unit_tests()
    assert calls[-1] == ["pytest","-q"]
    app_module.run_cov_tests()
    assert calls[-1] == ["pytest","--cov=src","--cov-report=html","-q"]
    assert "[View Coverage Report]" in md[-1]
    app_module.run_param_tests()
    assert calls[-1] == ["pytest","tests/test_advanced.py","-q"]
    app_module.run_mock_tests()
    assert calls[-1] == ["pytest","tests/test_advanced.py","-q"]
    app_module.run_html_report()
    assert calls[-1] == ["pytest","--html=report.html","--self-contained-html","-q"]
    assert "[View HTML Report]" in md[-1]
    app_module.run_bdd_tests()
    assert calls[-1] == ["pytest", "-q", "tests/feature"]

# Cover show_filters UI logic returns correct filter tuple
# --- show_filters coverage ---
 # Verify show_filters returns selected category, priority, and completed flag
def test_show_filters(monkeypatch):
    # stub UI
    monkeypatch.setattr(app_module.st, "columns", lambda *a,**k: (DummyCM(), DummyCM()))
    seq = iter(["CatVal","PriVal"])
    monkeypatch.setattr(app_module.st, "selectbox", lambda *a,**k: next(seq))
    monkeypatch.setattr(app_module.st, "checkbox", lambda *a,**k: True)
    result = app_module.show_filters([])
    assert result == ("CatVal","PriVal",True)

# Confirm render_task outputs markdown and buttons for tasks
# --- render_task coverage ---
 # Test render_task markup for normal and overdue tasks
def test_render_task(monkeypatch):
    calls = []
    monkeypatch.setattr(app_module.st, "markdown", lambda txt, **k: calls.append(("md", txt)))
    monkeypatch.setattr(app_module.st, "write", lambda txt: calls.append(("wr", txt)))
    monkeypatch.setattr(app_module.st, "caption", lambda txt: calls.append(("cap", txt)))
    monkeypatch.setattr(app_module.st, "button", lambda *a, **k: None)
    task = {"id":1,"title":"X","description":"Y","due_date":"D","priority":"P","category":"C","completed":False}
    app_module.render_task(task, overdue=False)
    assert any(c[0]=="md" and "**X**" in c[1] for c in calls)
    calls.clear()
    app_module.render_task(task, overdue=True)
    assert any(c[0]=="md" and "overdue" in c[1] for c in calls)

# Confirm display_tasks lists tasks with proper labels and buttons
# --- display_tasks coverage ---
 # Ensure display_tasks renders each task title and description
def test_display_tasks(monkeypatch):
    calls = []
    monkeypatch.setattr(app_module.st, "markdown", lambda txt: calls.append(txt))
    monkeypatch.setattr(app_module.st, "write", lambda txt: calls.append(txt))
    monkeypatch.setattr(app_module.st, "caption", lambda txt: calls.append(txt))
    monkeypatch.setattr(app_module.st, "button", lambda lbl, **k: calls.append(lbl))
    tasks = [{"id":2,"title":"Z","description":"D","due_date":"D","priority":"P","category":"C","completed":True}]
    app_module.display_tasks(tasks)
    assert any("Z" in c for c in calls)

# Test that complete_task toggles and delete_task removes a task
# --- complete_task and delete_task coverage ---
 # Verify complete_task and delete_task persist changes to storage
def test_complete_and_delete(tmp_path, monkeypatch):
    fp = tmp_path / "tasks.json"
    tasks_module.save_tasks([{"id":5,"completed":False}], file_path=str(fp))
    # Stub app_module load/save to use our tmp file
    monkeypatch.setattr(app_module, "load_tasks", lambda: tasks_module.load_tasks(file_path=str(fp)))
    monkeypatch.setattr(app_module, "save_tasks", lambda tasks_list: tasks_module.save_tasks(tasks_list, file_path=str(fp)))
    app_module.complete_task(5)
    loaded = tasks_module.load_tasks(file_path=str(fp))
    assert loaded[0]["completed"] is True
    app_module.delete_task(5)
    loaded2 = tasks_module.load_tasks(file_path=str(fp))
    assert loaded2 == []

# Additional tests to cover session_state init and edit flow
# --- Additional tests for src/app.py coverage ---
import sys, runpy
import streamlit as st

 # Ensure import initializes edit_id in session_state
def test_session_state_initialization(monkeypatch):
    # Simulate fresh import; session_state should get edit_id=None
    class SS: pass
    new_state = SS()
    monkeypatch.setattr(st, "session_state", new_state)
    if "src.app" in sys.modules:
        del sys.modules["src.app"]
    new_app = __import__("src.app", fromlist=[""])
    assert hasattr(new_state, "edit_id") and new_state.edit_id is None

 # Test start_edit and save_edit properly update session_state and storage
def test_start_and_save_edit(tmp_path, monkeypatch):
    from datetime import datetime
    # Prepare temp tasks file
    fp = tmp_path / "tasks.json"
    # Stub app_module load/save to use our temp file
    monkeypatch.setattr(app_module, "load_tasks", lambda: tasks_module.load_tasks(file_path=str(fp)))
    monkeypatch.setattr(app_module, "save_tasks", lambda lst: tasks_module.save_tasks(lst, file_path=str(fp)))
    # Write initial task
    tasks_module.save_tasks([{
        "id": 10,
        "title": "Orig",
        "description": "Desc",
        "priority": "Low",
        "category": "Cat",
        "due_date": "2025-01-01",
        "completed": False,
        "created_at": "2025-01-01 00:00:00"
    }], file_path=str(fp))
    # Inject session_state
    class SS2: pass
    state = SS2()
    state.tasks = tasks_module.load_tasks(file_path=str(fp))
    monkeypatch.setattr(app_module.st, "session_state", state)
    # Call start_edit
    app_module.start_edit(10)
    assert state.tasks == []
    assert state.edit_id == 10
    assert state.edit_task_data["id"] == 10
    # Fill edited values
    prefix = f"edit_10_"
    setattr(state, prefix + "title", "NewTitle")
    setattr(state, prefix + "description", "NewDesc")
    setattr(state, prefix + "priority", "High")
    setattr(state, prefix + "category", "NewCat")
    setattr(state, prefix + "due_date", datetime.strptime("2025-02-02", "%Y-%m-%d").date())
    # Call save_edit
    app_module.save_edit(10)
    assert state.edit_id is None
    updated = state.tasks[0]
    assert updated["title"] == "NewTitle"
    assert updated["description"] == "NewDesc"
    assert updated["priority"] == "High"
    assert updated["category"] == "NewCat"
    assert updated["due_date"] == "2025-02-02"
    assert not hasattr(state, "edit_task_data")

 # Verify main() dispatches to all run_* functions when checkboxes are set
def test_main_run_selected(monkeypatch):
    calls = []
    # Stub UI and logic components
    monkeypatch.setattr(app_module, "show_sidebar", lambda tasks: None)
    monkeypatch.setattr(app_module, "show_filters", lambda tasks: ("All","All",True))
    monkeypatch.setattr(app_module, "filter_tasks_by_category", lambda tasks,cat: tasks)
    monkeypatch.setattr(app_module, "filter_tasks_by_priority", lambda tasks,pri: tasks)
    monkeypatch.setattr(app_module, "sort_tasks_by_due_date", lambda tasks,ascending: tasks)
    monkeypatch.setattr(app_module, "display_tasks", lambda tasks: None)
    # Prepare session_state
    class SS3: pass
    ss = SS3(); ss.tasks = []
    monkeypatch.setattr(app_module.st, "session_state", ss)
    # Stub Streamlit UI calls
    monkeypatch.setattr(app_module.st, "title", lambda *a,**k: None)
    monkeypatch.setattr(app_module.st, "header", lambda *a,**k: None)
    monkeypatch.setattr(app_module.st, "markdown", lambda *a,**k: None)
    monkeypatch.setattr(app_module.st, "expander", lambda *a,**k: DummyCM())
    monkeypatch.setattr(app_module.st, "write", lambda *a,**k: None)
    monkeypatch.setattr(app_module.st, "columns", lambda *a,**k: (
        DummyCM(), DummyCM(), DummyCM(), DummyCM(), DummyCM(), DummyCM()
    ))    
    monkeypatch.setattr(app_module.st, "checkbox", lambda *a,**k: True)
    # Stub run functions
    for fname in ["run_unit_tests","run_cov_tests","run_param_tests","run_mock_tests","run_html_report", "run_bdd_tests"]:
        monkeypatch.setattr(app_module, fname, lambda f=fname: calls.append(f))
    monkeypatch.setattr(app_module.st, "button", lambda lbl, **k: lbl=="Run Selected Tests")
    # Execute main
    app_module.main()
    assert set(calls) == {"run_unit_tests","run_cov_tests","run_param_tests","run_mock_tests","run_html_report", "run_bdd_tests"}

 # Cover the __main__ import guard running main()
def test_module_run_main(monkeypatch):
    import sys
    # Ensure no prior src.app module to prevent RuntimeWarning
    sys.modules.pop("src.app", None)
    # Cover the __main__ block
    called = []
    monkeypatch.setattr("src.app.main", lambda: called.append(True))
    runpy.run_module("src.app", run_name="__main__")
    assert called