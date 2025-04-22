import sys, os, subprocess
import pytest
from pathlib import Path
from datetime import datetime, date, timedelta

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

# --- Mock tests ---
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
    cats, pris = app_module.get_filter_options(
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

# --- Parameterized tests ---
@pytest.mark.parametrize("tasks_list,expected", [
    ([], 1),
    ([{"id":2},{"id":7}], 8),
])
def test_generate_unique_id_param(tasks_list, expected):
    assert generate_unique_id(tasks_list) == expected

@pytest.mark.parametrize("tasks_list,priority,expected", [
    ([{"priority":"High"},{"priority":"Low"}], "High", [{"priority":"High"}]),
    ([{"priority":"X"},{"priority":"X"}], "X", [{"priority":"X"},{"priority":"X"}]),
])
def test_filter_tasks_by_priority_param(tasks_list, priority, expected):
    assert filter_tasks_by_priority(tasks_list, priority) == expected

@pytest.mark.parametrize("tasks_list,category,expected", [
    ([{"category":"A"},{"category":"B"}], "B", [{"category":"B"}]),
])
def test_filter_tasks_by_category_param(tasks_list, category, expected):
    assert filter_tasks_by_category(tasks_list, category) == expected

@pytest.mark.parametrize("tasks_list,completed,expected", [
    ([{"completed":True},{"completed":False}], True, [{"completed":True}]),
    ([{"completed":True},{"completed":False}], False, [{"completed":False}]),
])
def test_filter_tasks_by_completion_param(tasks_list, completed, expected):
    assert filter_tasks_by_completion(tasks_list, completed) == expected

@pytest.mark.parametrize("tasks_list,query,expected", [
    ([{"title":"Foo","description":"Bar"}], "foo", [{"title":"Foo","description":"Bar"}]),
    ([{"title":"X","description":"Y"}], "z", []),
])
def test_search_tasks_param(tasks_list, query, expected):
    assert search_tasks(tasks_list, query) == expected

# --- Mock integration tests for app buttons and UI flows ---
@pytest.mark.parametrize("label,args,link", [
    ("Run Unit Tests", ["pytest","-q"], None),
    ("Run Coverage", ["pytest","--cov=src","--cov-report=html","-q"], "[View Coverage Report](htmlcov/index.html)"),
    ("Run Param Tests", ["pytest","tests/test_advanced.py","-q"], None),
    ("Run Mock Tests", ["pytest","tests/test_advanced.py","-q"], None),
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

# --- TDD feature tests for edit, sort, overdue/upcoming ---
@pytest.fixture
def sample_tasks():
    today = datetime.now().date()
    return [
        {"id":1,"title":"Old","description":"D","priority":"Low","category":"Work","due_date":(today-timedelta(days=1)).strftime("%Y-%m-%d"),"completed":False,"created_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"id":2,"title":"Today","description":"D2","priority":"Medium","category":"Personal","due_date":today.strftime("%Y-%m-%d"),"completed":False,"created_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"id":3,"title":"New","description":"D3","priority":"High","category":"Other","due_date":(today+timedelta(days=1)).strftime("%Y-%m-%d"),"completed":False,"created_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    ]

def test_edit_task(sample_tasks):
    updates = {"title":"E","description":"ED","priority":"High","category":"School","due_date":(datetime.now().date()+timedelta(days=5)).strftime("%Y-%m-%d")}
    tasks = edit_task(sample_tasks.copy(), task_id=2, updates=updates)
    t = next(t for t in tasks if t["id"]==2)
    assert t["title"]=="E"

def test_sort_tasks_by_due_date(sample_tasks):
    asc = sort_tasks_by_due_date(sample_tasks.copy(), ascending=True)
    dates = [t["due_date"] for t in asc]
    assert dates == sorted(dates)
    desc = sort_tasks_by_due_date(sample_tasks.copy(), ascending=False)
    assert [t["due_date"] for t in desc] == sorted(dates, reverse=True)

def test_get_overdue_and_upcoming(sample_tasks):
    overdue = get_overdue_tasks(sample_tasks.copy())
    upcoming = get_upcoming_tasks(sample_tasks.copy())
    assert {t["id"] for t in overdue} == {1}
    assert {t["id"] for t in upcoming} == {2,3}
