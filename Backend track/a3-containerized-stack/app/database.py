import os
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://postgres:dev@localhost:5432/tasks")

def get_db_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT false
                )
            """)
            cur.execute("SELECT COUNT(*) FROM tasks")
            if cur.fetchone()["count"] == 0:
                cur.execute("""
                    INSERT INTO tasks (title, done) VALUES
                    ('Learn Docker', false),
                    ('Run Postgres in a container', false),
                    ('Ship A3', true)
                """)
        conn.commit()

def get_all_tasks():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tasks ORDER BY id")
            return cur.fetchall()

def get_task_by_id(task_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            return cur.fetchone()

def create_task(title: str, done: bool):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *", (title, done))
            task = cur.fetchone()
        conn.commit()
        return task

def update_task(task_id: int, title: str, done: bool):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *", (title, done, task_id))
            task = cur.fetchone()
        conn.commit()
        return task

def delete_task(task_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            deleted = cur.rowcount > 0
        conn.commit()
        return deleted

def ping():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
