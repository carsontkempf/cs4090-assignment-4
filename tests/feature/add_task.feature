Feature: Task management

  Scenario: Adding a new task
    Given I start with no tasks
    When I add a task with title "Buy milk" and description "Get 2% milk" and priority "High" and category "Personal" and due date "2025-05-01"
    Then the task list contains exactly 1 task
    And the task titled "Buy milk" has description "Get 2% milk"
    And the task titled "Buy milk" has priority "High"
    And the task titled "Buy milk" has category "Personal"
    And the task titled "Buy milk" has due date "2025-05-01"
    And the task titled "Buy milk" is not completed

  Scenario: Completing a task
    Given a task titled "Write report" with description "Draft v1" and priority "Medium" and category "Work" and due date "2025-06-01" exists
    When I mark the task "Write report" as complete
    Then the task "Write report" is marked completed

  Scenario: Deleting a task
    Given tasks titled "Old task" and "Keep task" exist
    When I delete the task "Old task"
    Then the task list does not contain "Old task"
    And the task list still contains "Keep task"

  Scenario: Filtering tasks by category
    Given tasks titled "A" (category "Work") and "B" (category "Personal") and "C" (category "Work") exist
    When I filter tasks by category "Work"
    Then only tasks titled "A" and "C" are visible

  Scenario: Editing a task
    Given I have an existing task titled "Draft" with description "Initial" and priority "Low" and category "School" and due date "2025-07-01" exists
    When I edit the task "Draft" changing title to "Final" and description to "Revised" and priority to "High" and category to "Work" and due date to "2025-07-15"
    Then the task list contains a task titled "Final"
    And that task has description "Revised"
    And that task has priority "High"
    And that task has category "Work"
    And that task has due date "2025-07-15"