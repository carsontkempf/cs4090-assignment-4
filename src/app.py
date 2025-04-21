import streamlit as st
from datetime import datetime
from .tasks import (
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
    """Pure logic for task actions."""
    if complete_pressed and not task.get("completed", False):
        return "complete"
    if delete_pressed:
        return "delete"
    return None

def show_sidebar(tasks):  # pragma: no cover
    """Render sidebar and handle new task submission."""
    st.sidebar.header("Add New Task")
    with st.sidebar.form("new_task_form"):
        title = st.text_input("Title")
        desc = st.text_area("Description")
        categories, _ = get_filter_options(tasks)
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        category = st.selectbox("Category", ["Other"] + categories)
        due_date = st.date_input("Due Date")
        submitted = st.form_submit_button("Add Task")
    new_task = handle_new_task(tasks, submitted, title, desc, priority, category, due_date)
    if new_task:
        st.sidebar.success("Task added!")

def show_filters(tasks):  # pragma: no cover
    """Render filter controls and return chosen values."""
    categories, priorities = get_filter_options(tasks)
    col1, col2 = st.columns(2)
    with col1:
        cat = st.selectbox("Category", ["All"] + categories)
    with col2:
        pri = st.selectbox("Priority", ["All"] + priorities)
    show_done = st.checkbox("Show Completed")
    return compute_filters(cat, pri, show_done)

def display_tasks(tasks):  # pragma: no cover
    """Display tasks with action buttons."""
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
            action = decide_task_action(
                task,
                st.button("Complete", key=f"complete_{task['id']}"),
                st.button("Delete", key=f"delete_{task['id']}")
            )
            if action == "complete":
                task["completed"] = True
                save_tasks(tasks)
                return None
            if action == "delete":
                return task["id"]
    return None

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
    deleted = display_tasks(filtered)
    if deleted is not None:
        tasks = [t for t in tasks if t["id"] != deleted]
        save_tasks(tasks)
        return
    if st.button("Run Tests"):
        # Run pytest in subprocess and display output in terminal
        subprocess.run(["pytest", "-q"])

if __name__ == "__main__":
    main()