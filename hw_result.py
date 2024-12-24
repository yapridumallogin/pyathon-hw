import pickle
import uuid
from fastapi import FastAPI, HTTPException

from pydantic import BaseModel

# before run this app, there must be installed fastapi and uvicorn: pip install fastapi uvicorn[standard]
# To run this app: uvicorn hw_result:app --reload


class Task:
    def __init__(self, id: str, title: str, priority: int, is_done: bool):
        self.id = id
        self.title = title
        self.priority = priority
        self.is_done = is_done

    def set_complete(self):
        self.is_done = True

    def set_incomplete(self):
        self.is_done = False


class TasksPickleFileStorage:
    def __init__(self, file_name):
        self.file_name = file_name

    def list_tasks(self):
        try:
            tasks = {}
            with open(self.file_name, 'rb+') as input_file:
                unpickler = pickle.Unpickler(input_file)
                tasks = unpickler.load()
            return tasks
        except FileNotFoundError:
            return {}
        except EOFError:
            return {}

    def persist(self, task: Task):
        tasks = self.list_tasks()
        tasks[task.id] = task
        with open(self.file_name, 'wb+') as output_file:
            pickle.dump(tasks, output_file)

    def get_by_id(self, task_id: str) -> Task | None:
        tasks = self.list_tasks()
        if task_id in tasks:
            return tasks[task_id]
        return None


class TasksManager:
    def __init__(self, tasks_storage: TasksPickleFileStorage):
        self.tasks_storage = tasks_storage

    def list_tasks(self):
        return self.tasks_storage.list_tasks()

    def create_task(self, title: str, priority: int) -> Task:
        task_id = str(uuid.uuid4())
        task = Task(task_id, title, priority, False)
        self.tasks_storage.persist(task)
        return task

    def complete_task(self, task_id: str) -> Task | None:
        task = self.tasks_storage.get_by_id(task_id)
        if task is None:
            return None
        task.set_complete()
        self.tasks_storage.persist(task)
        return task


class CreateTaskDTO(BaseModel):
    title: str
    priority: int


tasks_manager = TasksManager(TasksPickleFileStorage('tasks.txt'))
app = FastAPI()


@app.get("/tasks")
def list_tasks():
    tasks = tasks_manager.list_tasks()
    return tasks


@app.post("/tasks")
def create_task(crete_task_dto: CreateTaskDTO):
    task = tasks_manager.create_task(crete_task_dto.title, crete_task_dto.priority)
    return task


@app.post("/tasks/{id}/complete")
def complete_task(id: str):
    task = tasks_manager.complete_task(id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
