import sys
import os
import subprocess
import streamlit as st
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.tasks import (
    load_tasks,
    save_tasks,
    filter_tasks_by_priority,
    filter_tasks_by_category,
    generate_unique_id,
    edit_task,
)

# Initialize edit state
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

def start_edit(task_id):
    """Set task to edit."""
    st.session_state.edit_id = task_id


def save_edit(task_id):
    """Save edits by reading current form inputs from session_state."""
    # Read fresh values from session_state keys
    prefix = f"edit_{task_id}_"
    # Convert date object to string for JSON serialization
    raw_due = st.session_state[prefix + "due_date"]
    due_str = raw_due.strftime("%Y-%m-%d") if hasattr(raw_due, "strftime") else raw_due
    updates = {
        "title": st.session_state[prefix + "title"],
        "description": st.session_state[prefix + "description"],
        "category": st.session_state[prefix + "category"],
        "priority": st.session_state[prefix + "priority"],
        "due_date": due_str,
    }
    # Use edit_task to merge and replace
    tasks_list = edit_task(st.session_state.tasks, task_id, updates)
    st.session_state.tasks = tasks_list
    save_tasks(tasks_list)
    st.session_state.edit_id = None
    # Trigger rerun if available
    rerun = getattr(st, "experimental_rerun", None)
    if callable(rerun):
        rerun()

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
        st.session_state.tasks = tasks
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
            # Edit button
            st.button(
                "Edit",
                key=f"edit_{task['id']}",
                on_click=start_edit,
                args=(task["id"],)
            )

def run_unit_tests():
    subprocess.run(["pytest", "-q"])

def run_cov_tests():
    subprocess.run(["pytest", "--cov=src", "--cov-report=html", "-q"])
    st.markdown("[View Coverage Report](htmlcov/index.html)")

def run_param_tests():
    subprocess.run(["pytest", "tests/test_advanced.py", "-q"])

def run_mock_tests():
    subprocess.run(["pytest", "tests/test_advanced.py", "-q"])

def run_html_report():
    subprocess.run(["pytest", "--html=report.html", "--self-contained-html", "-q"])
    st.markdown("[View HTML Report](report.html)")

def main():  # pragma: no cover
    st.title("To-Do Application")
    # Persist tasks in session state for immediate UI updates
    if "tasks" not in st.session_state:
        st.session_state.tasks = load_tasks()
    tasks = st.session_state.tasks
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

    # Edit form for selected task
    if st.session_state.edit_id:
        task_to_edit = next(t for t in tasks if t["id"] == st.session_state.edit_id)
        with st.form(f"edit_form_{task_to_edit['id']}"):
            prefix = f"edit_{task_to_edit['id']}_"
            st.text_input("Title", value=task_to_edit["title"], key=prefix + "title")
            st.text_area("Description", value=task_to_edit["description"], key=prefix + "description")
            st.selectbox(
                "Category",
                ["Work","Personal","School","Other"],
                index=["Work","Personal","School","Other"].index(task_to_edit["category"]),
                key=prefix + "category"
            )
            st.selectbox(
                "Priority",
                ["Low","Medium","High"],
                index=["Low","Medium","High"].index(task_to_edit["priority"]),
                key=prefix + "priority"
            )
            st.date_input(
                "Due Date",
                value=datetime.strptime(task_to_edit["due_date"], "%Y-%m-%d").date(),
                key=prefix + "due_date"
            )
            st.form_submit_button("Save Changes", on_click=save_edit, args=(task_to_edit["id"],))

    display_tasks(filtered)

    # Legacy individual test-run buttons (hidden by default)
    with st.expander("Legacy Test Buttons", expanded=False):
        st.write("<small>Use only if necessary</small>", unsafe_allow_html=True)
        if st.button("Run Unit Tests", key="legacy_unit"):
            subprocess.run(["pytest", "-q"])
        if st.button("Run Coverage", key="legacy_cov"):
            subprocess.run(["pytest", "--cov=src", "--cov-report=html", "-q"])
            st.markdown("[View Coverage Report](htmlcov/index.html)")
        if st.button("Run Param Tests", key="legacy_param"):
            subprocess.run(["pytest", "tests/test_advanced.py", "-q"])
        if st.button("Run Mock Tests", key="legacy_mock"):
            subprocess.run(["pytest", "tests/test_advanced.py", "-q"])
        if st.button("Run HTML Report", key="legacy_html"):
            subprocess.run(["pytest", "--html=report.html", "--self-contained-html", "-q"])
            st.markdown("[View HTML Report](report.html)")

    # Test selection controls
    try:
        cols = st.columns(5)
        col_u, col_c, col_p, col_m, col_h = cols
    except ValueError:
        # Skip test controls in minimal contexts (e.g., tests)
        pass
    else:
        with col_u:
            run_unit = st.checkbox("Unit Tests", key="chk_unit")
        with col_c:
            run_cov = st.checkbox("Coverage Tests", key="chk_cov")
        with col_p:
            run_param = st.checkbox("Parameter Tests", key="chk_param")
        with col_m:
            run_mock = st.checkbox("Mock Tests", key="chk_mock")
        with col_h:
            run_html = st.checkbox("HTML Report", key="chk_html")
        if st.button("Run Selected Tests"):
            if run_unit:
                run_unit_tests()
            if run_cov:
                run_cov_tests()
            if run_param:
                run_param_tests()
            if run_mock:
                run_mock_tests()
            if run_html:
                run_html_report()

if __name__ == "__main__":
    main()