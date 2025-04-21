# To-Do App Testing Assignment

## Objective
Develop a simple To-Do List application using Streamlit, enhanced with buttons that trigger various automated tests. The goal is to give students hands-on experience with:

- [ ] Basic pytest
- [ ] Pytest features (fixtures, parameterization)
- [ ] Test-Driven Development (TDD)
- [ ] Behavior-Driven Development (BDD)
- [ ] Property-Based Testing (hypothesis)

## Assignment Details

**Submission Format:** GitHub/GitLab repository link + Streamlit URL + written report

## The Application
The application allows users to:
- [ ] Create, edit, and delete tasks
- [ ] Set priorities and due dates
- [ ] Categorize and filter tasks
- [ ] Mark tasks as complete

## Setup Instructions

- [x] Fork the Repository  
  - [x] Fork the starter code from: https://github.com/imranraad07/cs4090-assignment-4-templaeLinks to an external site.
- [x] Clone your fork to your local machine  
  - [x] Note this code has bugs (added intentionally), you need to find the bugs, write tests and fix the bugs
- [x] Install Requirements  
   ```bash
   pip install -r requirements.txt
   ```
- [x] Run the Application  
   ```bash
   streamlit run app.py
   ```
- [x] Explore the Application  
   - [x] Familiarize yourself with all features
   - [x] Take notes on initial observations

## Testing Requirements
You must implement and document the following types of tests:

### 1. Unit Testing (20 points)
- [x] Write unit tests for at least 5 key functions using pytest
- [x] Achieve at least 90% code coverage
- [x] Document your approach to unit testing
- [x] Have a streamlit button. On button press it runs the tests

### 2. Bug Reporting and Fixing (20 points)
- [x] Document all bugs found using a standard bug report format
- [x] Fix all bugs you've identified
- [x] Provide before/after evidence of fixes

### 3. Pytest Features (20 points)
- [ ] Do different pytest features:
- [x]  pytest-cov
- [ ]  Parameterization
- [ ]  mocking
- [ ]  report-generation in html
- [ ] Have separate streamlit button for each functionalities. On button press it runs the specific test

### 4. Do Test-Driven Development (TDD)  (20 points)
- [ ] Identify at least 3 new features to add to the application
- [ ] Write tests for these features before implementing them
- [ ] Document your TDD process, including:
  - [ ] Initial test creation
  - [ ] Test failure demonstration
  - [ ] Feature implementation
  - [ ] Test passing verification
  - [ ] Any refactoring performed

### 5. Do Behavior-Driven Development (BDD)  (20 points)
- [ ] Add at least 5 BDD tests
- [ ] Have a streamlit button. On button press it runs the tests

### (Bonus) 6. Do Property-Based Testing   (20 points)
- [ ] Add at least 5 hypothesis tests
- [ ] Have a streamlit button. On button press it runs the tests

--- 

## Deliverables
- [ ] GitHub Repository containing:
  - [ ] All test code
  - [ ] Test data
  - [ ] Documentation
  - [ ] Fixed application code
- [ ] Written Report (4-5 pages) including:
  - [ ] Test results and metrics
  - [ ] Bug summary
  - [ ] Reports of TDD, BDD, and Property-based testing
  - [ ] Lessons learned
- [ ] Streamlit App Link
- [ ] Good luck and happy testing!


---

## Project Structure

```
todo_app/
│
├── app.py                  # Streamlit UI
├── tasks.py                # Core logic: add, delete, update, etc.
├── test/
│   ├── test_basic.py       # Basic pytest tests
│   ├── test_advanced.py    # Fixtures and parameterized tests
│   ├── test_tdd.py         # TDD-driven example
│   ├── test_property.py    # Property-based tests using hypothesis
│   └── features/           # BDD folder for behave
│       ├── add_task.feature
│       └── steps/
│           └── test_add_steps.py
├── requirements.txt
└── README.md
```

### Highlights

- **`app.py`** – Streamlit UI to interact with the to-do list.
- **`tasks.py`** – Contains the core logic for managing tasks.
- **`test/`** – Includes various test styles:
  - `test_basic.py`: Unit tests with `pytest`
  - `test_advanced.py`: Tests using fixtures & parameterization
  - `test_tdd.py`: Test-driven development example
  - `test_property.py`: Property-based testing with `hypothesis`
  - `features/`: BDD tests using `behave` or `pytest-bdd`, including feature files and steps
