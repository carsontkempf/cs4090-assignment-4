import sys
import os
# Ensure project root is on sys.path so 'src' package can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
from datetime import datetime
from src.tasks import (
    load_tasks,
    save_tasks,
    filter_tasks_by_priority,
    filter_tasks_by_category,
    generate_unique_id,
)
import subprocess

def build_task(tasks, title, description, priority, category, due_date):
    """Construct a task dict with a unique ID and timestamp."""
    return {
        "id": generate_unique_id(tasks),
        "title": title,
        "description": description,
        "priority": priority,
        "category": category,
        "due_date": due_date.strftime("%Y-%m-%d"),
        "completed": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

def complete_task(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["completed"] = not t["completed"]
    save_tasks(tasks)

def delete_task(task_id):
    tasks = load_tasks()
    save_tasks([t for t in tasks if t["id"] != task_id])

def get_filter_options(tasks):
    """Return sorted lists of unique categories and priorities."""
    categories = sorted({task["category"] for task in tasks})
    priorities = ["High", "Medium", "Low"]
    return categories, priorities

def handle_new_task(tasks, submitted, title, desc, priority, category, due_date):
    """Pure logic to add a task."""
    if submitted and title:
        new = build_task(tasks, title, desc, priority, category, due_date)
        tasks.append(new)
        save_tasks(tasks)
        return new
    return None

def compute_filters(selected_category, selected_priority, show_completed):
    """Pure logic to return filter choices."""
    return selected_category, selected_priority, show_completed

def decide_task_action(task, complete_pressed, delete_pressed):
    """Pure logic for task actions, including undo."""
    if complete_pressed:
        return "undo" if task.get("completed", False) else "complete"
    if delete_pressed:
        return "delete"
    return None

def show_sidebar(tasks):  # pragma: no cover
    """Render sidebar and handle new task submission."""
    st.sidebar.header("Add New Task")
    with st.sidebar.form("new_task_form"):
        title = st.text_input("Title")
        desc = st.text_area("Description")
        category = st.selectbox("Category", ["Work", "Personal", "School", "Other"])
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        due_date = st.date_input("Due Date")
        submitted = st.form_submit_button("Add Task")
    new_task = handle_new_task(tasks, submitted, title, desc, priority, category, due_date)
    if new_task:
        st.sidebar.success("Task added!")

def show_filters(tasks):  # pragma: no cover
    """Render filter controls and return chosen values."""
    col1, col2 = st.columns(2)
    with col1:
        cat = st.selectbox("Category", ["All", "Work", "Personal", "School", "Other"])
    with col2:
        pri = st.selectbox("Priority", ["All", "High", "Medium", "Low"])
    show_done = st.checkbox("Show Completed")
    return compute_filters(cat, pri, show_done)

def display_tasks(tasks):
    """Render tasks with on_click callbacks for instant updates."""
    for task in tasks:
        cols = st.columns([4, 1])
        with cols[0]:
            title = f"~~{task['title']}~~" if task["completed"] else task["title"]
            st.markdown(f"**{title}**")
            st.write(task["description"])
            st.caption(
                f"Due: {task['due_date']} | Priority: {task['priority']} | Category: {task['category']}"
            )
        with cols[1]:
            st.button(
                "Undo" if task["completed"] else "Complete",
                key=f"complete_{task['id']}",
                on_click=complete_task,
                args=(task["id"],)
            )
            st.button(
                "Delete",
                key=f"delete_{task['id']}",
                on_click=delete_task,
                args=(task["id"],)
            )

def main():  # pragma: no cover
    st.title("To-Do Application")
    tasks = load_tasks()
    show_sidebar(tasks)
    st.header("Your Tasks")
    cat, pri, show_done = show_filters(tasks)
    filtered = tasks.copy()
    if cat != "All":
        filtered = filter_tasks_by_category(filtered, cat)
    if pri != "All":
        filtered = filter_tasks_by_priority(filtered, pri)
    if not show_done:
        filtered = [t for t in filtered if not t["completed"]]

    display_tasks(filtered)

    if st.button("Run Tests"):
        subprocess.run(["pytest", "-q"])

if __name__ == "__main__":
    main()