from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


app = FastAPI(
    title="Task API",
    version="1.0",
    description="A simple in-memory CRUD API for managing tasks.",
)


class Task(BaseModel):
    id: int
    title: str
    done: bool


class TaskCreate(BaseModel):
    title: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


tasks = [
    Task(id=1, title="Learn FastAPI", done=False),
    Task(id=2, title="Build CRUD API", done=False),
    Task(id=3, title="Test with Swagger", done=False),
]


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid request body"},
    )


@app.get("/", summary="API information")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}


@app.get("/tasks", summary="Get all tasks")
def get_tasks():
    return tasks


@app.get("/tasks/{task_id}", summary="Get a task by ID")
def get_task(task_id: int):
    for task in tasks:
        if task.id == task_id:
            return task

    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"},
    )


@app.post("/tasks", status_code=201, summary="Create a new task")
def create_task(task_data: TaskCreate):
    if task_data.title is None or not task_data.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Title is required"},
        )

    used_ids = {task.id for task in tasks}

    new_id = 1
    while new_id in used_ids:
        new_id += 1

    new_task = Task(
        id=new_id,
        title=task_data.title.strip(),
        done=False,
    )

    tasks.append(new_task)

    return new_task


@app.put("/tasks/{task_id}", summary="Update a task")
def update_task(task_id: int, task_data: TaskUpdate):
    for index, task in enumerate(tasks):
        if task.id == task_id:
            if task_data.title is None and task_data.done is None:
                return JSONResponse(
                    status_code=400,
                    content={"error": "At least one field is required"},
                )

            updated_task = Task(
                id=task.id,
                title=(
                    task_data.title.strip()
                    if task_data.title is not None
                    else task.title
                ),
                done=(
                    task_data.done
                    if task_data.done is not None
                    else task.done
                ),
            )

            if not updated_task.title:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Title cannot be empty"},
                )

            tasks[index] = updated_task

            return updated_task

    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"},
    )


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    for index, task in enumerate(tasks):
        if task.id == task_id:
            tasks.pop(index)
            return Response(status_code=204)

    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"},
    )