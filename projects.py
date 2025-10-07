import json
import os

# Define the name of the file to store project data
DATA_FILE = 'projects.json'

def load_data():
    """
    Loads project data from the JSON file.
    If the file doesn't exist, it returns an empty dictionary.
    """
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r') as f:
            # Return an empty dict if the file is empty
            content = f.read()
            if not content:
                return {}
            return json.loads(content)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading data: {e}")
        return {}

def save_data(data):
    """
    Saves the project data to the JSON file.
    """
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Error saving data: {e}")

def display_menu():
    """
    Displays the main menu of options to the user.
    """
    print("\n--- Project Tracking Menu ---")
    print("1. View All Projects and Tasks")
    print("2. Add a New Project")
    print("3. Add a Task to a Project")
    print("4. Update a Task's Status")
    print("5. Exit")
    print("-----------------------------")

def view_projects(data):
    """
    Displays all projects and their associated tasks and statuses.
    """
    if not data:
        print("\nNo projects found. Add a project to get started!")
        return

    print("\n--- All Projects ---")
    for project_name, project_details in data.items():
        print(f"\nProject: {project_name}")
        tasks = project_details.get('tasks', [])
        if not tasks:
            print("  - No tasks yet.")
        else:
            for i, task in enumerate(tasks, 1):
                # Using .get() for safe access to 'name' and 'status' keys
                task_name = task.get('name', 'N/A')
                status = task.get('status', 'N/A')
                print(f"  {i}. {task_name} - [Status: {status}]")
    print("--------------------")


def add_project(data):
    """
    Prompts the user for a new project name and adds it to the data.
    """
    project_name = input("Enter the name for the new project: ").strip()
    if not project_name:
        print("Project name cannot be empty.")
        return
    if project_name in data:
        print(f"Project '{project_name}' already exists.")
    else:
        data[project_name] = {"tasks": []}
        save_data(data)
        print(f"Project '{project_name}' added successfully.")

def add_task(data):
    """
    Adds a new task to a specified project.
    """
    if not data:
        print("\nNo projects exist. Please add a project first.")
        return

    project_name = input("Enter the project name to add a task to: ").strip()
    if project_name not in data:
        print(f"Project '{project_name}' not found.")
        return

    task_name = input("Enter the task description: ").strip()
    if not task_name:
        print("Task description cannot be empty.")
        return
        
    new_task = {"name": task_name, "status": "Not Started"}
    data[project_name]['tasks'].append(new_task)
    save_data(data)
    print(f"Task '{task_name}' added to project '{project_name}'.")

def update_task_status(data):
    """
    Updates the status of a specific task in a project.
    """
    if not data:
        print("\nNo projects exist. Please add a project first.")
        return
        
    project_name = input("Enter the project name: ").strip()
    if project_name not in data:
        print(f"Project '{project_name}' not found.")
        return

    tasks = data[project_name].get('tasks', [])
    if not tasks:
        print(f"No tasks found for project '{project_name}'.")
        return

    print(f"\nTasks for '{project_name}':")
    for i, task in enumerate(tasks, 1):
        print(f"  {i}. {task['name']} - [Status: {task['status']}]")

    try:
        task_num_str = input("Enter the task number to update: ")
        task_num = int(task_num_str) - 1
        if 0 <= task_num < len(tasks):
            new_status = input("Enter the new status (e.g., In Progress, Completed): ").strip()
            if not new_status:
                print("Status cannot be empty.")
                return
            data[project_name]['tasks'][task_num]['status'] = new_status
            save_data(data)
            print("Task status updated successfully.")
        else:
            print("Invalid task number.")
    except ValueError:
        print("Invalid input. Please enter a number.")

def main():
    """
    Main function to run the project tracking application.
    """
    projects_data = load_data()

    while True:
        display_menu()
        choice = input("Enter your choice (1-5): ")

        if choice == '1':
            view_projects(projects_data)
        elif choice == '2':
            add_project(projects_data)
        elif choice == '3':
            add_task(projects_data)
        elif choice == '4':
            update_task_status(projects_data)
        elif choice == '5':
            print("Exiting Project Tracker. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")

if __name__ == '__main__':
    main()
