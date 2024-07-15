import os
import anthropic
import re
from typing import List, Optional, Dict, Callable
from pydantic import BaseModel, Field, ConfigDict
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, TaskID
from rich.text import Text
from prompts import ENHANCE_PROMPT, REFINE_GOAL_PROMPT, TASK_PLAN_PROMPT

# Initialize the Anthropic client
client = anthropic.Anthropic(
    api_key="API_KEY_HERE"
)

console = Console()

TASK_COMPLETE_PHRASE = "TASK IS COMPLETE"

# Updated Pydantic models
class Task(BaseModel):
    number: str
    name: str
    description: str
    tools: List[str] = Field(default_factory=list)
    success_factors: str = ""
    completion_criteria: str = ""
    status: str = Field(default="INCOMPLETE")
    advice: str = ""
    file_or_directory: Optional[str] = None

class TaskPlan(BaseModel):
    goal: str
    tasks: List[Task]

def send_prompt(prompt):
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text



def parse_tasks(content: str) -> TaskPlan:
    goal_match = re.search(r'GOAL:\s*(.*?)(?=\n\nTASK|\Z)', content, re.DOTALL)
    goal = goal_match.group(1).strip() if goal_match else ""

    tasks = []
    task_blocks = re.split(r'\n\nTASK \d+:', content)

    for i, block in enumerate(task_blocks[1:], start=1):
        task_dict = {
            "number": str(i).zfill(3),
            "name": "",
            "description": "",
            "tools": [],
            "success_factors": "",
            "completion_criteria": "",
            "status": "INCOMPLETE",
            "advice": "",
            "file_or_directory": None
        }
        
        lines = block.strip().split('\n')
        current_key = None
        for line in lines:
            if ':' in line and not line.strip().startswith('-'):
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                
                if key == 'tools':
                    task_dict[key] = [tool.strip() for tool in value.split(',') if tool.strip()]
                elif key == 'file/directory':
                    task_dict['file_or_directory'] = value
                elif key in task_dict:
                    task_dict[key] = value
                current_key = key
            elif current_key and current_key in task_dict:
                task_dict[current_key] += ' ' + line.strip()

        if task_dict['name']:
            tasks.append(Task(**task_dict))

    return TaskPlan(goal=goal, tasks=tasks)




def print_task(task: Task):
    task_info = [
        f"[bold]{task.name}[/bold]",
        f"Description: {task.description}" if task.description else "",
        f"Tools: {', '.join(task.tools)}" if task.tools else "",
        f"Success Factors: {task.success_factors}" if task.success_factors else "",
        f"Completion Criteria: {task.completion_criteria}" if task.completion_criteria else "",
        f"Status: {task.status}",
        f"Advice: {task.advice}" if task.advice else "",
        f"File/Directory: {task.file_or_directory}" if task.file_or_directory else "File/Directory: Not specified"
    ]
    
    task_info = [info for info in task_info if info]  # Remove empty lines
    
    console.print(Panel(
        "\n\n".join(task_info),
        title=f"Task {task.number}",
        border_style="cyan"
    ))

def save_task_plan_to_file(task_plan: TaskPlan, filename: str = "Goal_and_Tasks.txt"):
    with open(filename, "w") as f:
        f.write(f"Goal: {task_plan.goal}\n\n")
        for task in task_plan.tasks:
            f.write(f"Task {task.number}: {task.name}\n")
            f.write(f"Description: {task.description}\n")
            f.write(f"Tools: {', '.join(task.tools)}\n")
            f.write(f"Success Factors: {task.success_factors}\n")
            f.write(f"Completion Criteria: {task.completion_criteria}\n")
            f.write(f"Status: {task.status}\n")
            f.write(f"Advice: {task.advice}\n")
            f.write(f"File/Directory: {task.file_or_directory or 'Not specified'}\n\n")

# Example tool functions
def read_file(file_path: str) -> str:
    with open(file_path, 'r') as file:
        return file.read()

def write_file(args: str) -> str:
    file_path, content = args.split(':', 1)
    with open(file_path, 'w') as file:
        file.write(content)
    return f"File written: {file_path}"

def list_directory(dir_path: str) -> str:
    return ', '.join(os.listdir(dir_path))

def print_welcome():
    welcome_text = Text("🥷 Welcome to Agent X Chat 🥷", style="bold magenta")
    
    console.print(Panel(welcome_text, expand=False, border_style="cyan"))

def get_user_goal():
    goal_prompt = (
        "[bold cyan]What is your goal?[/bold cyan]"
    )
    return Prompt.ask(goal_prompt)

def ask_clarifying_questions(user_goal: str):
    prompt = f"""
    You are a goal enhancer. This is the user's goal: "{user_goal}".
    Your task is to respond with exactly 5 questions to help better understand their goal. MAKE SURE THE QUESTIONS ARENT DUMB AND GENUINLY HELP YOU BETTER UNDERSTAND HOW YOU ENHNACE THEIR GOAL. You never need to ask when they need something completed as the answer will always be asap.
    Please format your response as:
    Question 1: ...
    Question 2: ...
    Question 3: ...
    Question 4: ...
    Question 5: ...
    """
    response = send_prompt(prompt)
    question_matches = re.findall(r'Question \d+:\s*(.*?)(?=\nQuestion \d+:|$)', response, re.DOTALL)
    questions = [q.strip() for q in question_matches if q.strip()]
    
    # Ensure we have exactly 5 questions
    while len(questions) < 5:
        questions.append("Could you provide any additional information about your goal?")
    return questions[:5]

def get_user_responses(questions: List[str]) -> List[str]:
    responses = []
    for i, question in enumerate(questions, 1):
        console.print(f"\n[bold cyan]Question {i} of 5:[/bold cyan]")
        console.print(question)
        response = Prompt.ask("[bold green]Your answer[/bold green]")
        responses.append(response)
    return responses

def print_goal(goal: str):
    console.print(Panel(goal, title="[bold cyan]The Goal", border_style="cyan", expand=False))

def refine_goal(goal: str, clarifying_qas: List[str]) -> str:
    qas_formatted = "\n".join(f"Q{i+1}: {qa[0]}\nA{i+1}: {qa[1]}" for i, qa in enumerate(clarifying_qas))
    refined_goal_content = send_prompt(REFINE_GOAL_PROMPT.format(user_goal=goal, clarifying_qas=qas_formatted))
    match = re.search(r'<goal>(.*?)</goal>', refined_goal_content, re.DOTALL)
    return match.group(1).strip() if match else goal

def update_task_status(task: Task) -> Task:
    while True:
        console.print(f"\n[bold cyan]Current Task: {task.name}[/bold cyan]")
        console.print(f"Status: {task.status}")
        console.print(f"Completion Criteria: {task.completion_criteria}")
        
        user_input = Prompt.ask("[bold green]Enter 'TASK IS COMPLETE' when finished, or press Enter to continue[/bold green]")
        
        if user_input.upper() == TASK_COMPLETE_PHRASE:
            task.status = "COMPLETE"
            console.print(f"[bold green]Task {task.number} marked as complete![/bold green]")
            break
        elif user_input == "":
            console.print("[yellow]Continuing with the current task...[/yellow]")
            break
        else:
            console.print("[red]Invalid input. Please try again.[/red]")
    
    return task

def execute_task_plan(task_plan: TaskPlan):
    for task in task_plan.tasks:
        print_task(task)
        updated_task = update_task_status(task)
        task.status = updated_task.status

def main():
    print_welcome()
    user_goal = get_user_goal()
    
    console.print("\n[bold cyan]Great! Now, I'm going to ask you 5 clarifying questions to better understand your goal.[/bold cyan]")
    
    questions = ask_clarifying_questions(user_goal)
    responses = get_user_responses(questions)
    clarifying_qas = list(zip(questions, responses))
    
    console.print("\n[bold cyan]Refining your goal...[/bold cyan]")
    refined_goal = refine_goal(user_goal, clarifying_qas)
    print_goal(refined_goal)
    
    console.print("\n[bold cyan]Analyzing your refined goal and creating a detailed plan...[/bold cyan]")
    task_plan_content = send_prompt(TASK_PLAN_PROMPT.format(user_goal=refined_goal))
    enhanced_task_plan_content = send_prompt(ENHANCE_PROMPT.format(user_goal=refined_goal, task_plan_content=task_plan_content))
    
    try:
        enhanced_task_plan = parse_tasks(enhanced_task_plan_content)
        
        if enhanced_task_plan:
            console.print("\n[bold cyan]The Master Plan:[/bold cyan]")
            for task in enhanced_task_plan.tasks:
                print_task(task)

            save_task_plan_to_file(enhanced_task_plan)
            console.print(Panel("The Goal & Master Plan are saved to 'Goal_and_Tasks.txt'", title="File Saved", border_style="green"))

            console.print("\n[bold cyan]Executing the task plan...[/bold cyan]")
            execute_task_plan(enhanced_task_plan)

            console.print("\n[bold green]All tasks completed![/bold green]")
        else:
            console.print("Failed to create the enhanced and optimized task plan.", style="bold red")
    except Exception as e:
        console.print(f"An error occurred while processing the task plan: {str(e)}", style="bold red")
        console.print(f"Error type: {type(e).__name__}")
        console.print(f"Error details: {str(e)}")
        import traceback
        console.print("Traceback:")
        console.print(traceback.format_exc())

if __name__ == "__main__":
    main()
