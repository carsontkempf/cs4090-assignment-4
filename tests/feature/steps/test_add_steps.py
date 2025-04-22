from pytest_bdd import scenarios, given, when, then, parsers
import streamlit as st
from datetime import datetime
from src import app
from src.tasks import load_tasks, save_tasks, filter_tasks_by_category, edit_task
from src.app import delete_task


# --- Scenario: Adding a new task ---

@given("I start with no tasks", target_fixture="fp")
def clear_tasks(tmp_path, monkeypatch):
    fp = tmp_path / "tasks.json"
    # Override the DEFAULT_TASKS_FILE constant so load/save use our temp file
    monkeypatch.setattr("src.tasks.DEFAULT_TASKS_FILE", str(fp), raising=False)
    st.session_state.tasks = []
    return fp

@when(parsers.parse(
    'I add a task with title "{title}" and description "{desc}" and priority "{priority}" and category "{category}" and due date "{due}"'
))
def add_task(fp, monkeypatch, title, desc, priority, category, due):
    # Ensure save/load use the same temp file
    monkeypatch.setattr("src.tasks.DEFAULT_TASKS_FILE", str(fp), raising=False)
    due_date = datetime.strptime(due, "%Y-%m-%d").date()
    new = app.handle_new_task(st.session_state.tasks, True, title, desc, priority, category, due_date)
    assert new is not None

@then("the task list contains exactly 1 task")
def one_task():
    assert len(st.session_state.tasks) == 1

@then(parsers.parse('the task titled "{title}" has description "{desc}"'))
def check_desc(title, desc):
    t = next(t for t in st.session_state.tasks if t["title"] == title)
    assert t["description"] == desc

@then(parsers.parse('the task titled "{title}" has priority "{priority}"'))
def check_pri(title, priority):
    t = next(t for t in st.session_state.tasks if t["title"] == title)
    assert t["priority"] == priority

@then(parsers.parse('the task titled "{title}" has category "{category}"'))
def check_cat(title, category):
    t = next(t for t in st.session_state.tasks if t["title"] == title)
    assert t["category"] == category

@then(parsers.parse('the task titled "{title}" has due date "{due}"'))
def check_due(title, due):
    t = next(t for t in st.session_state.tasks if t["title"] == title)
    assert t["due_date"] == due

@then(parsers.parse('the task titled "{title}" is not completed'))
def check_not_done(title):
    t = next(t for t in st.session_state.tasks if t["title"] == title)
    assert t["completed"] is False


# --- Scenario: Completing a task ---

@given(parsers.parse(
    'a task titled "{title}" with description "{desc}" and priority "{priority}" and category "{category}" and due date "{due}" exists'
), target_fixture="given_one_task")
def given_one_task(tmp_path, monkeypatch, title, desc, priority, category, due):
    fp = tmp_path / "tasks.json"
    monkeypatch.setattr("src.tasks.DEFAULT_TASKS_FILE", str(fp), raising=False)
    task = app.build_task([], title, desc, priority, category,
                           datetime.strptime(due, "%Y-%m-%d").date())
    save_tasks([task], file_path=str(fp))
    st.session_state.tasks = [task]
    return fp, task["id"]

@when(parsers.parse('I mark the task "{title}" as complete'))
def mark_complete(given_one_task):
    fp, tid = given_one_task
    app.complete_task(tid)

@then(parsers.parse('the task "{title}" is marked completed'))
def check_completed(given_one_task):
    fp, tid = given_one_task
    tasks = load_tasks(file_path=str(fp))
    t = next(t for t in tasks if t["id"] == tid)
    assert t["completed"] is True


# --- Scenario: Deleting a task ---

@given("tasks titled \"Old task\" and \"Keep task\" exist", target_fixture="given_two")
def given_two(tmp_path, monkeypatch):
    fp = tmp_path / "tasks.json"
    monkeypatch.setattr("src.tasks.DEFAULT_TASKS_FILE", str(fp), raising=False)
    t1 = app.build_task([], "Old task", "x", "Low", "Personal", datetime.today().date())
    t2 = app.build_task([t1], "Keep task", "y", "High", "Work", datetime.today().date())
    save_tasks([t1, t2], file_path=str(fp))
    st.session_state.tasks = [t1, t2]
    return fp

@when("I delete the task \"Old task\"")
def do_delete(given_two):
    fp = given_two
    tasks = load_tasks(file_path=str(fp))
    tid = next(t["id"] for t in tasks if t["title"] == "Old task")
    delete_task(tid)

@then("the task list does not contain \"Old task\"")
def check_deleted(given_two):
    fp = given_two
    tasks = load_tasks(file_path=str(fp))
    titles = [t["title"] for t in tasks]
    assert "Old task" not in titles

@then("the task list still contains \"Keep task\"")
def check_keep(given_two):
    fp = given_two
    tasks = load_tasks(file_path=str(fp))
    titles = [t["title"] for t in tasks]
    assert "Keep task" in titles


# --- Scenario: Filtering tasks by category ---

@given("tasks titled \"A\" (category \"Work\") and \"B\" (category \"Personal\") and \"C\" (category \"Work\") exist")
def given_three():
    st.session_state.tasks = [
        {"id":1,"title":"A","description":"","priority":"Low","category":"Work","due_date":"2025-01-01","completed":False,"created_at":""},
        {"id":2,"title":"B","description":"","priority":"Low","category":"Personal","due_date":"2025-01-01","completed":False,"created_at":""},
        {"id":3,"title":"C","description":"","priority":"Low","category":"Work","due_date":"2025-01-01","completed":False,"created_at":""},
    ]
    return st.session_state.tasks

@when(parsers.parse('I filter tasks by category "{cat}"'))
def do_filter(cat):
    visible = filter_tasks_by_category(st.session_state.tasks, cat)
    st.session_state.filtered = visible

@then(parsers.parse('only tasks titled "{t1}" and "{t2}" are visible'))
def check_visible(t1, t2):
    titles = [t["title"] for t in st.session_state.filtered]
    assert set(titles) == {t1, t2}


# --- Scenario: Editing a task ---

@given(parsers.parse(
    'I have an existing task titled "{title}" with description "{desc}" and priority "{priority}" and category "{category}" and due date "{due}" exists'
), target_fixture="edit_context")
def given_edit(tmp_path, monkeypatch, title, desc, priority, category, due):
    st.session_state.tasks = []
    due_date = datetime.strptime(due, "%Y-%m-%d").date()
    original = app.build_task([], title, desc, priority, category, due_date)
    st.session_state.tasks = [original]
    return original["id"], original

@when(parsers.parse(
    'I edit the task "{orig}" changing title to "{newt}" and description to "{newd}" and priority to "{newp}" and category to "{newc}" and due date to "{newdue}"'
))
def do_edit(orig, newt, newd, newp, newc, newdue, edit_context):
    tid, original = edit_context
    updates = {
        "title": newt,
        "description": newd,
        "priority": newp,
        "category": newc,
        "due_date": newdue,
    }
    st.session_state.tasks = edit_task([original], tid, updates)

@then("the task list contains a task titled \"Final\"")
def check_final():
    titles = [t["title"] for t in st.session_state.tasks]
    assert "Final" in titles

@then(parsers.parse('that task has description "{newd}"'))
def check_final_desc(newd):
    t = next(t for t in st.session_state.tasks if t["title"] == "Final")
    assert t["description"] == newd

@then(parsers.parse('that task has priority "{newp}"'))
def check_final_pri(newp):
    t = next(t for t in st.session_state.tasks if t["title"] == "Final")
    assert t["priority"] == newp

@then(parsers.parse('that task has category "{newc}"'))
def check_final_cat(newc):
    t = next(t for t in st.session_state.tasks if t["title"] == "Final")
    assert t["category"] == newc

@then(parsers.parse('that task has due date "{newdue}"'))
def check_final_due(newdue):
    t = next(t for t in st.session_state.tasks if t["title"] == "Final")
    assert t["due_date"] == newdue


scenarios("../../feature/add_task.feature")