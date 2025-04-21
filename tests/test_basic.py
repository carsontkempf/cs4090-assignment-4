import json
import pytest
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
from src.app import build_task, get_filter_options, handle_new_task, compute_filters, decide_task_action
from datetime import datetime, date
import src.app as app


def test_generate_unique_id_empty():
    assert generate_unique_id([]) == 1

def test_generate_unique_id_non_empty():
    tasks = [{'id': 5}, {'id': 2}, {'id': 9}]
    assert generate_unique_id(tasks) == 10

def test_filter_priority_and_category_and_completion():
    tasks = [
        {'priority': 'High', 'category': 'A', 'completed': False},
        {'priority': 'Low',  'category': 'B', 'completed': True},
        {'priority': 'High', 'category': 'B', 'completed': False},
    ]
    assert filter_tasks_by_priority(tasks, 'High') == [tasks[0], tasks[2]]
    assert filter_tasks_by_category(tasks, 'B') == [tasks[1], tasks[2]]
    assert filter_tasks_by_completion(tasks, False) == [tasks[0], tasks[2]]

def test_search_tasks_case_insensitive():
    tasks = [
        {'title': 'Hello', 'description': 'World'},
        {'title': 'Test',  'description': 'hello world'},
    ]
    assert search_tasks(tasks, 'HELLO') == [tasks[0], tasks[1]]
    assert search_tasks(tasks, 'world') == [tasks[0], tasks[1]]

def test_load_and_save_tasks(tmp_path):
    file_path = tmp_path / "t.json"
    data = [{'id':1,'title':'x'}]
    save_tasks(data, file_path=str(file_path))
    loaded = load_tasks(file_path=str(file_path))
    assert loaded == data

def test_load_tasks_file_not_found(tmp_path):
    loaded = load_tasks(file_path=str(tmp_path / "nofile.json"))
    assert loaded == []

def test_load_tasks_invalid_json(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("nope")
    loaded = load_tasks(file_path=str(bad))
    out = capsys.readouterr().out
    assert 'invalid JSON' in out
    assert loaded == []

def test_get_overdue_tasks(monkeypatch):
    import src.tasks as m
    class D:
        @classmethod
        def now(cls):
            return datetime(2025,1,2)
    monkeypatch.setattr(m, 'datetime', D)
    tasks = [
        {'due_date': '2025-01-01', 'completed': False},
        {'due_date': '2025-01-02', 'completed': False},
        {'due_date': '2025-01-03', 'completed': False},
    ]
    assert get_overdue_tasks(tasks) == [tasks[0]]

def test_build_task():
    tasks = [{'id':1}, {'id':3}]
    # Freeze time manually
    t = app.build_task(tasks, 'T','D','High','C', date(2025,2,3))
    assert t['id'] == 4
    assert t['title'] == 'T'
    assert t['description'] == 'D'
    assert t['priority'] == 'High'
    assert t['category'] == 'C'
    assert t['due_date'] == '2025-02-03'
    assert isinstance(t['created_at'], str)

def test_get_filter_options():
    tasks = [
        {'category':'B'},
        {'category':'A'},
        {'category':'C'},
    ]
    cats, pris = app.get_filter_options(tasks)
    assert cats == ['A','B','C']
    assert pris == ['High','Medium','Low']

def test_display_tasks_complete_and_delete(monkeypatch):
    calls = []
    # Dummy st
    class DummySt:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass
        def columns(self, spec):
            return (self, self)
        def markdown(self, *a): calls.append(('md',a))
        def write(self, *a): calls.append(('w',a))
        def caption(self, *a): calls.append(('c',a))
        def button(self, label, key):
            # Simulate pressing the "Complete" button only
            return label.startswith("Complete")
        def experimental_rerun(self): pass
    monkeypatch.setattr(app, 'st', DummySt())
    global all_tasks
    all_tasks = []
    # Test complete
    tasks = [{'id':1,'title':'X','description':'','priority':'','category':'','due_date':'2025-01-01','completed':False}]
    res = app.display_tasks(tasks)
    assert tasks[0]['completed'] is True
    # Test delete
    calls.clear()
    tasks[0]['completed'] = True
    def btn(label, key):
        return label.startswith("Delete")
    monkeypatch.setattr(app.st, 'button', btn)
    res2 = app.display_tasks(tasks)
    assert res2 == 1

def test_handle_new_task_appends_and_saves(monkeypatch):
    from src.app import handle_new_task
    tasks = []
    saved = {}
    def fake_save(tsk):
        saved['tasks'] = list(tsk)
    monkeypatch.setattr('src.app.save_tasks', fake_save)
    due = date(2025, 7, 7)
    new = handle_new_task(tasks, True, 'T', 'D', 'High', 'Work', due)
    assert isinstance(new, dict)
    assert tasks == [new]
    assert saved['tasks'] == [new]

    # when not submitted
    tasks2 = []
    none = handle_new_task(tasks2, False, 'T', 'D', 'High', 'Work', due)
    assert none is None
    assert tasks2 == []

def test_compute_filters():
    from src.app import compute_filters
    assert compute_filters('Cat', 'Pri', True) == ('Cat', 'Pri', True)
    assert compute_filters('All', 'All', False) == ('All', 'All', False)

@pytest.mark.parametrize("completed,complete_pressed,delete_pressed,expected", [
    (False, True, False, 'complete'),
    (True, True, False, None),
    (False, False, True, 'delete'),
    (False, False, False, None),
])
def test_decide_task_action(completed, complete_pressed, delete_pressed, expected):
    task = {'completed': completed}
    from src.app import decide_task_action
    assert decide_task_action(task, complete_pressed, delete_pressed) == expected