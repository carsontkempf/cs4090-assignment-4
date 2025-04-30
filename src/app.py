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
    is_task_overdue,
    sort_tasks_by_due_date,
)

# Initialize edit state safely
if not hasattr(st.session_state, "edit_id"):
    st.session_state.edit_id = None

def start_edit(task_id):
    """Set task to edit and remove original immediately."""
    tasks = st.session_state.tasks
    original = next((t for t in tasks if t["id"] == task_id), None)
    if original is not None:
        st.session_state.edit_task_data = original.copy()
        new_tasks = [t for t in tasks if t["id"] != task_id]
        st.session_state.tasks = new_tasks
        save_tasks(new_tasks)
    st.session_state.edit_id = task_id

def save_edit(task_id):
    """Save edits by reading current form inputs from session_state."""
    prefix = f"edit_{task_id}_"
    # Support both dict-like and attribute session_state
    if hasattr(st.session_state, "__getitem__"):
        raw_due = st.session_state[prefix + "due_date"]
    else:
        raw_due = getattr(st.session_state, prefix + "due_date")
    due_str = raw_due.strftime("%Y-%m-%d") if hasattr(raw_due, "strftime") else raw_due
    updates = {
        "title": getattr(st.session_state, prefix + "title"),
        "description": getattr(st.session_state, prefix + "description"),
        "category": getattr(st.session_state, prefix + "category"),
        "priority": getattr(st.session_state, prefix + "priority"),
        "due_date": due_str,
    }
    original = st.session_state.edit_task_data
    updated_task = original.copy()
    updated_task.update(updates)
    tasks_list = st.session_state.tasks + [updated_task]
    st.session_state.tasks = tasks_list
    save_tasks(tasks_list)
    st.session_state.edit_id = None
    # Support attribute-based session_state for edit_task_data
    if hasattr(st.session_state, "edit_task_data"):
        del st.session_state.edit_task_data
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
    categories = sorted({task["category"] for task in tasks})
    priorities = ["High", "Medium", "Low"]
    return categories, priorities

def handle_new_task(tasks, submitted, title, desc, priority, category, due_date):
    if submitted and title:
        new = build_task(tasks, title, desc, priority, category, due_date)
        tasks.append(new)
        save_tasks(tasks)
        st.session_state.tasks = tasks
        return new
    return None

def compute_filters(selected_category, selected_priority, show_completed):
    return selected_category, selected_priority, show_completed

def decide_task_action(task, complete_pressed, delete_pressed):
    if complete_pressed:
        return "undo" if task.get("completed", False) else "complete"
    if delete_pressed:
        return "delete"
    return None

def show_sidebar(tasks):  # pragma: no cover
    st.sidebar.header("Add New Task")
    form = st.sidebar.form("new_task_form")
    if not hasattr(form, "text_input"):
        return
    with form:
        title = form.text_input("Title")
        desc = form.text_area("Description")
        category = form.selectbox("Category", ["Work", "Personal", "School", "Other"])
        priority = form.selectbox("Priority", ["Low", "Medium", "High"])
        due_date = form.date_input("Due Date")
        submitted = form.form_submit_button("Add Task")
    new_task = handle_new_task(tasks, submitted, title, desc, priority, category, due_date)
    if new_task:
        st.sidebar.success("Task added!")

def show_filters(tasks):  # pragma: no cover
    col1, col2 = st.columns(2)
    with col1:
        cat = st.selectbox("Category", ["All"] + list({t["category"] for t in tasks}))
    with col2:
        pri = st.selectbox("Priority", ["All", "High", "Medium", "Low"])
    show_done = st.checkbox("Show Completed Tasks")
    return compute_filters(cat, pri, show_done)

def render_task(task, overdue=False):
    cols = st.columns([4, 1])
    with cols[0]:
        title = f"~~{task['title']}~~" if task["completed"] else task["title"]
        if overdue:
            try:
                st.markdown(f"<span class='overdue'>**{title}**</span>", unsafe_allow_html=True)
            except TypeError:
                st.markdown(f"<span class='overdue'>**{title}**</span>")
        else:
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
        st.button(
            "Edit",
            key=f"edit_{task['id']}",
            on_click=start_edit,
            args=(task["id"],)
        )

def display_tasks(tasks):
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
            st.button(
                "Edit",
                key=f"edit_{task['id']}",
                on_click=start_edit,
                args=(task["id"],)
            )

def run_unit_tests():
    result = subprocess.run(["pytest", "-q"], capture_output=True, text=True)
    st.code(result.stdout + result.stderr, language='bash')
    if result.returncode == 0:
        st.success("✅ Unit tests passed")
    else:
        st.error("❌ Unit tests failed")

def run_cov_tests():
    result = subprocess.run(["pytest", "--cov=src", "--cov-report=html", "-q"], capture_output=True, text=True)
    st.code(result.stdout + result.stderr, language='bash')
    if result.returncode == 0:
        st.success("✅ Coverage tests passed")
    else:
        st.error("❌ Coverage tests failed")

def run_param_tests():
    result = subprocess.run(["pytest", "tests/test_advanced.py", "-q"], capture_output=True, text=True)
    st.code(result.stdout + result.stderr, language='bash')
    if result.returncode == 0:
        st.success("✅ Parameterized tests passed")
    else:
        st.error("❌ Parameterized tests failed")

def run_mock_tests():
    result = subprocess.run(["pytest", "tests/test_advanced.py", "-q"], capture_output=True, text=True)
    st.code(result.stdout + result.stderr, language='bash')
    if result.returncode == 0:
        st.success("✅ Mock tests passed")
    else:
        st.error("❌ Mock tests failed")

def run_html_report():
    result = subprocess.run(["pytest", "--html=report.html", "--self-contained-html", "-q"], capture_output=True, text=True)
    st.code(result.stdout + result.stderr, language='bash')
    if result.returncode == 0:
        st.success("✅ HTML report generated")
    else:
        st.error("❌ HTML report generation failed")

def run_bdd_tests():
    result = subprocess.run(["pytest", "-q", "tests/feature"], capture_output=True, text=True)
    st.code(result.stdout + result.stderr, language='bash')
    if result.returncode == 0:
        st.success("✅ BDD tests passed")
    else:
        st.error("❌ BDD tests failed")

def main():  # pragma: no cover
    # Ensure edit_id exists in session_state for non-dict session_state
    if not hasattr(st.session_state, "edit_id"):
        st.session_state.edit_id = None
    st.title("To-Do Application")

    # Persist tasks safely
    if not hasattr(st.session_state, "tasks"):
        st.session_state.tasks = load_tasks()
    tasks = st.session_state.tasks

    show_sidebar(tasks)
    st.header("Your Tasks")

    html_style = """
    <style>
      .overdue { color: red; font-weight: bold; }
    </style>
    """
    try:
        st.markdown(html_style, unsafe_allow_html=True)
    except TypeError:
        st.markdown(html_style)

    cat, pri, show_done = show_filters(tasks)
    filtered = tasks.copy()
    if cat != "All":
        filtered = filter_tasks_by_category(filtered, cat)
    if pri != "All":
        filtered = filter_tasks_by_priority(filtered, pri)
    if not show_done:
        filtered = [t for t in filtered if not t["completed"]]

    sort_option = st.selectbox("Sort by Due Date", ["Ascending", "Descending"])
    ascending = sort_option == "Ascending"
    filtered = sort_tasks_by_due_date(filtered, ascending=ascending)

    if st.session_state.edit_id:
        task_to_edit = st.session_state.edit_task_data
        with st.form(f"edit_form_{task_to_edit['id']}"):
            prefix = f"edit_{task_to_edit['id']}_"
            st.text_input("Title", value=task_to_edit["title"], key=prefix + "title")
            st.text_area("Description", value=task_to_edit["description"], key=prefix + "description")
            st.selectbox(
                "Category",
                ["Work", "Personal", "School", "Other"],
                index=["Work", "Personal", "School", "Other"].index(task_to_edit["category"]),
                key=prefix + "category"
            )
            st.selectbox(
                "Priority",
                ["Low", "Medium", "High"],
                index=["Low", "Medium", "High"].index(task_to_edit["priority"]),
                key=prefix + "priority"
            )
            st.date_input(
                "Due Date",
                value=datetime.strptime(task_to_edit["due_date"], "%Y-%m-%d").date(),
                key=prefix + "due_date"
            )
            st.form_submit_button("Save Changes", on_click=save_edit, args=(task_to_edit["id"],))

    overdue = [t for t in filtered if is_task_overdue(t)]
    upcoming = [t for t in filtered if not is_task_overdue(t)]

    if overdue:
        st.subheader("Overdue Tasks")
        for t in overdue:
            render_task(t, overdue=True)

    if upcoming:
        st.subheader("Upcoming Tasks")
        for t in upcoming:
            render_task(t)

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
        if st.button("Run BDD Tests", key="legacy_bdd_tests"):
            subprocess.run(["pytest", "-q", "tests/feature"])

    try:
        cols = st.columns(6)
        col_u, col_c, col_p, col_m, col_h, col_b = cols
    except ValueError:
        pass
    else:
        with col_u:
            run_unit = st.checkbox("Unit Tests", key="chk_unit", value=True)
        with col_c:
            run_cov = st.checkbox("Coverage Tests", key="chk_cov", value=True)
        with col_p:
            run_param = st.checkbox("Parameter Tests", key="chk_param", value=True)
        with col_m:
            run_mock = st.checkbox("Mock Tests", key="chk_mock", value=True)
        with col_h:
            run_html = st.checkbox("HTML Report", key="chk_html", value=True)
        with col_b:
            run_bdd = st.checkbox("BDD Tests", key="chk_bdd", value=True)

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
            if run_bdd:
                run_bdd_tests()

if __name__ == "__main__":
    # Always delegate to src.app.main so test monkeypatch applies
    from src import app as _app
    _app.main()