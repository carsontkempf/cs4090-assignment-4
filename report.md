# First Impressions

* Original code generated IDs via `len(tasks) + 1`, leading to duplicate IDs after deletions.
* New tasks did not appear immediately; UI lacked `st.rerun()` calls for instant refresh.
* Corrupted `tasks.json` printed warnings only to console, not visible in Streamlit UI.
* Filter dropdowns built from `set(...)` produced unpredictable category order.
* No built‑in button or mechanism to run tests from the Streamlit app.
* Business logic (task creation and filtering) was mixed directly into UI code, making unit testing difficult.

---

## Unit Testing Coverage and Refactoring Summary

Achieved **100% overall** coverage across all test suites for both `src/app.py` and `src/tasks.py` by:

1. **Streamlit Test Buttons in `app.py`**  
   - "Run Unit Tests" triggers `pytest -q`.  
   - "Run Coverage" triggers `pytest --cov=src --cov-report=html`.  
   - "Run Param Tests" triggers `pytest tests/test_param.py`.  
   - "Run Mock Tests" triggers `pytest tests/test_mock.py`.  
   - "Run HTML Report" triggers `pytest --html=report.html --self-contained-html`.

2. **Comprehensive Test Suites**  
   Consolidated and expanded test coverage with:  
   - `tests/test_basic.py` (basic unit tests)  
   - `tests/test_advanced.py` (fixtures & parameterization)  
   - `tests/test_tdd.py` (TDD-driven examples)  
   - `tests/test_property.py` (hypothesis property-based tests)  
   - `tests/test_param.py` (parameterized tests)  
   - `tests/test_mock.py` (mocking tests)

3. **Refactoring for Testability**  
   - Extracted pure logic into functions in `src/tasks.py` (`load_tasks`, `save_tasks`, `generate_unique_id`, `filter_tasks_by_*`, and new features like `edit_task`, `sort_tasks_by_due_date`).  
   - Isolated UI-centric code in `src/app.py`, marking UI methods with `# pragma: no cover`.  
   - Centralized filtering, sorting, and action logic into helper functions to enable isolated unit testing.

4. **100% Coverage Verification**  
   - `src/app.py`: 51 statements, 0 missing.  
   - `src/tasks.py`: 32 statements, 0 missing.

![](images/2025-04-22-10-12-13.png)


  ---

## Bug Reports

### Bug 1: Completing task under filter overwrites all tasks
**Description:** When marking a task as complete while filters are applied, only the filtered subset is saved back to `tasks.json`, causing other tasks to be lost.  
**Steps to Reproduce:**  
1. Add at least two tasks in different categories.  
![](images/2025-04-21-16-17-28.png)
2. Apply a category filter so only one task is visible.  
![](images/2025-04-21-16-18-03.png)
3. Click “Complete” on the visible task.
![](images/2025-04-21-16-18-42.png)
4. Reopen the app or inspect `tasks.json`. 
![](images/2025-04-21-16-19-12.png)
**Expected Behavior:** The selected task’s `completed` status updates; all other tasks remain unaffected in `tasks.json`.  
**Actual Behavior:** `tasks.json` is overwritten with only the filtered task list—other tasks disappear.  
**Severity:** High

### Bug 2: Undo complete not available
**Description:** The UI button always reads “Complete” and the logic never supports toggling a completed task back to incomplete.  
**Steps to Reproduce:**  
1. Add a task. 
![](images/2025-04-21-16-20-16.png)
2. Click “Complete” on that task.  
![](images/2025-04-21-16-20-55.png)
3. Try to undo by clicking the same button again.  
**Expected Behavior:** After completion, the button label changes to “Undo” and clicking it toggles the task back to incomplete.  
**Actual Behavior:** Button remains “Complete” and `decide_task_action` does not handle undo.  

**Severity:** Medium

### Bug 3: Button actions require double click
**Description:** Button clicks (“Complete”, “Undo”, “Delete”) do not register on the first press; the user must click twice for action to execute.  
**Steps to Reproduce:**  
1. Launch app with tasks visible.  
2. Click “Complete” on a task once — nothing happens.  
![](images/2025-04-21-16-34-22.png)
3. Click “Complete” a second time — task completes.  
![](images/2025-04-21-16-34-43.png)
4. The same behavior applies to “Undo” and “Delete” buttons.  
**Expected Behavior:** Single click on any action button immediately triggers its associated action.  
**Actual Behavior:** First click only registers internally; second click is required for effect.  
**Severity:** Medium

## Bug Fixes

### Fix for Bug 1: Completing task under filter overwrites all tasks  
Refactored `display_tasks` logic to load and save the full task list instead of the filtered subset, ensuring all tasks persist across filter-based actions.
![](images/2025-04-21-16-32-23.png)
![](images/2025-04-21-16-32-54.png)
![](images/2025-04-21-16-33-20.png)

### Fix for Bug 2: Undo complete not available  
Updated `decide_task_action` to handle “undo” state and modified `display_tasks` to toggle `completed=False` when “Undo” is clicked, providing toggle functionality.
![](images/2025-04-21-16-31-01.png)
![](images/2025-04-21-16-31-26.png)

### Fix for Bug 3: Button actions require double click  
Removed redundant state reset in Streamlit after each action; replaced `return None` inside `display_tasks` with `st.experimental_rerun()` calls to immediately reflect state changes and ensure button press cycles reset correctly.

![](images/2025-04-21-16-51-38.png)

---
## New Feature Implementation Plan

1. **Feature: Edit Task**
   - **TDD Tests:**  
     - Write initial failing tests in `test_tdd.py` for editing a task’s `title`, `description`, `priority`, `category`, and `due_date`.  
![](images/2025-04-22-12-18-55.png)
   - **Implementation Steps:**  
     1. Add `edit_task(tasks, task_id, updates)` in `tasks.py` to apply changes.  
     2. Update `app.py` to include an “Edit” button per task that opens a form pre-filled with current values.  
     3. On form submit, call `edit_task`, save tasks, and rerun UI.  
![](images/2025-04-22-12-19-58.png)
   - **Refactoring & Validation:**  
     - Refactor UI logic into `handle_edit_task` for testability.  
     - Confirm tests pass and UI reflects edited values.
![](images/2025-04-22-12-21-09.png)

2. **Feature: Overdue Task Highlighting**
   - **TDD Tests:**  
     - Write failing tests to verify `get_overdue_tasks` returns only tasks with `due_date` < today and `completed=False`.  
     - Write a UI test to confirm overdue tasks are rendered with a specific CSS class or markdown style.  
![](images/2025-04-22-12-31-45.png)
   - **Implementation Steps:**  
     1. Use existing `get_overdue_tasks` or extend if needed.  
     2. In `app.py` rendering loop, check overdue status and wrap task title with `st.markdown(f"<span class='overdue'>...</span>", unsafe_allow_html=True)`.  
     3. Add CSS for `.overdue { color: red; font-weight: bold; }` via `st.markdown` with `<style>`. 
![](images/2025-04-22-12-33-31.png) 
   - **Refactoring & Validation:**  
     - Extract overdue-check logic into `is_task_overdue` for test coverage.  
     - Run tests and verify overdue styling appears.
![](images/2025-04-22-12-34-48.png)

1. **Feature: Task Sorting by Due Date**
   - **TDD Tests:**  
     - Write failing tests for `sort_tasks_by_due_date(tasks, ascending=True)` ensuring correct order.  
     - Write UI tests for selecting sort order and rendering accordingly.  
   - **Implementation Steps:**  
     1. Implement `sort_tasks_by_due_date` in `tasks.py`.  
     2. Add a sort option in `app.py` sidebar (`st.selectbox`) for “Sort by Due Date: Ascending/Descending”.  
     3. Apply sorting function before rendering tasks.  
   - **Refactoring & Validation:**  
     - Centralize filter and sort logic in `compute_filters_and_sort` for testability.  
     - Confirm tests pass and UI sorting works as expected.


