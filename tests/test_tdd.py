import pytest
from datetime import datetime, timedelta
from src.tasks import edit_task, sort_tasks_by_due_date, get_overdue_tasks, get_upcoming_tasks

@pytest.fixture
def sample_tasks():
    today = datetime.now().date()
    return [
        {
            "id": 1,
            "title": "Old Task",
            "description": "Desc1",
            "priority": "Low",
            "category": "Work",
            "due_date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "id": 2,
            "title": "Today Task",
            "description": "Desc2",
            "priority": "Medium",
            "category": "Personal",
            "due_date": today.strftime("%Y-%m-%d"),
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "id": 3,
            "title": "New Task",
            "description": "Desc3",
            "priority": "High",
            "category": "Other",
            "due_date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
    ]

def test_edit_task_updates_fields(sample_tasks):
    updates = {
        "title": "Edited",
        "description": "Edited desc",
        "priority": "High",
        "category": "School",
        "due_date": (datetime.now().date() + timedelta(days=5)).strftime("%Y-%m-%d")
    }
    tasks = edit_task(sample_tasks.copy(), task_id=2, updates=updates)
    t = next(t for t in tasks if t["id"] == 2)
    assert t["title"] == "Edited"
    assert t["description"] == "Edited desc"
    assert t["priority"] == "High"
    assert t["category"] == "School"
    assert t["due_date"] == updates["due_date"]

def test_sort_tasks_by_due_date_asc(sample_tasks):
    sorted_tasks = sort_tasks_by_due_date(sample_tasks.copy(), ascending=True)
    dates = [t["due_date"] for t in sorted_tasks]
    assert dates == sorted(dates)

def test_sort_tasks_by_due_date_desc(sample_tasks):
    sorted_tasks = sort_tasks_by_due_date(sample_tasks.copy(), ascending=False)
    dates = [t["due_date"] for t in sorted_tasks]
    assert dates == sorted(dates, reverse=True)

def test_get_overdue_tasks(sample_tasks):
    overdue = get_overdue_tasks(sample_tasks.copy())
    assert all(t["due_date"] < datetime.now().date().strftime("%Y-%m-%d") for t in overdue)
    assert {t["id"] for t in overdue} == {1}

def test_get_upcoming_tasks(sample_tasks):
    upcoming = get_upcoming_tasks(sample_tasks.copy())
    today_str = datetime.now().date().strftime("%Y-%m-%d")
    assert all(t["due_date"] >= today_str for t in upcoming)
    assert {t["id"] for t in upcoming} == {2, 3}