# Task API

A simple in-memory CRUD API built with Python and FastAPI.

## Features

- Create tasks
- Get all tasks
- Get a task by ID
- Update tasks
- Delete tasks
- Health check endpoint
- Interactive Swagger documentation

## Tech Stack

- Python 3.13
- FastAPI
- Uvicorn
- uv

## Run

From the repository root:

```bash
uv run --directory "Backend track/week-02-crud-api" uvicorn app.main:app --reload
