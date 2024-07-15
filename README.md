# Goal Setter

## Overview

`goal_setter.py` is a Python script designed to help users define, refine goals and tasks to provide an AI Agent. The script leverages the Anthropic API to enhance and refine user goals, and uses the `rich` library to provide a visually appealing command-line interface.

## Features

- **User Goal Input**: Prompts the user to input their goal.
- **Clarifying Questions**: Asks the user five clarifying questions to better understand their goal.
- **Goal Refinement**: Refines the user's goal based on their responses to the clarifying questions.
- **Task Plan Creation**: Generates a detailed task plan to achieve the refined goal.
- **Task Execution**: Guides the user through the execution of each task, updating the task status as they progress.
- **File Operations**: Includes utility functions to read from and write to files, and list directory contents.

## Requirements

- Python 3.7+
- `anthropic` library
- `pydantic` library
- `rich` library

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/goal_setter.git
    cd goal_setter
    ```

2. Install the required Python packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Run the script:
    ```sh
    python goal_setter.py
    ```

2. Follow the prompts to input your goal, answer clarifying questions, and execute the generated task plan.

## Configuration

- **Anthropic API Key**: The script requires an Anthropic API key to function. Replace the placeholder API key in the script with your actual API key:
    ```python
    client = anthropic.Anthropic(
        api_key="your_actual_api_key_here"
    )
    ```

## Functions

### Main Functions

- `main()`: The main function that orchestrates the entire process from goal input to task execution.

### Helper Functions

- `print_welcome()`: Prints a welcome message.
- `get_user_goal()`: Prompts the user to input their goal.
- `ask_clarifying_questions(user_goal: str)`: Asks the user five clarifying questions about their goal.
- `get_user_responses(questions: List[str])`: Collects the user's responses to the clarifying questions.
- `print_goal(goal: str)`: Prints the refined goal.
- `refine_goal(goal: str, clarifying_qas: List[str])`: Refines the user's goal based on their responses.
- `send_prompt(prompt: str)`: Sends a prompt to the Anthropic API and returns the response.
- `parse_tasks(content: str) -> TaskPlan`: Parses the task plan content and returns a `TaskPlan` object.
- `print_task(task: Task)`: Prints the details of a task.
- `save_task_plan_to_file(task_plan: TaskPlan, filename: str)`: Saves the task plan to a file.
- `update_task_status(task: Task) -> Task`: Updates the status of a task based on user input.
- `execute_task_plan(task_plan: TaskPlan)`: Executes the task plan by guiding the user through each task.

### Utility Functions

- `read_file(file_path: str) -> str`: Reads the content of a file.
- `write_file(args: str) -> str`: Writes content to a file.
- `list_directory(dir_path: str) -> str`: Lists the contents of a directory.

## Example

