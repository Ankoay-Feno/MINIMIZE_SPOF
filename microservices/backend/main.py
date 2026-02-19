#!/usr/bin/env python3
from datetime import datetime
import os
import platform
import socket
import time

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator
import psycopg
from psycopg import OperationalError
from psycopg import Error as PsycopgError

ROOT_PATH = os.getenv("ROOT_PATH", "")
DB_HOST = os.getenv("DB_HOST", "pgpool")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "app_db")
DB_USER = os.getenv("DB_USER", "app_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "app_password")
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "5"))
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"

app = FastAPI(
    title="Machine Info API",
    description="Retourne des informations de la machine hote.",
    version="1.0.0",
    root_path=ROOT_PATH,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if ENABLE_METRICS:
    Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app, include_in_schema=False)

START_TIME = time.time()


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    done: bool | None = None


class Todo(BaseModel):
    id: int
    title: str
    description: str | None
    done: bool
    created_at: datetime
    updated_at: datetime


def _resolve_primary_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "unknown"


def get_machine_info() -> dict:
    return {
        "application": "machine-info-app",
        "hostname": socket.gethostname(),
        "ip": _resolve_primary_ip(),
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
        },
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "load_avg": os.getloadavg() if hasattr(os, "getloadavg") else None,
        "uptime_seconds": int(time.time() - START_TIME),
        "port": int(os.getenv("PORT", "8000")),
    }


def _db_conn() -> psycopg.Connection:
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=DB_CONNECT_TIMEOUT,
    )


def _row_to_todo(row: tuple) -> Todo:
    return Todo(
        id=row[0],
        title=row[1],
        description=row[2],
        done=row[3],
        created_at=row[4],
        updated_at=row[5],
    )


def _todos_table_exists() -> bool:
    query = "SELECT to_regclass('public.todos') IS NOT NULL;"
    with _db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()
    return bool(row and row[0])


@app.on_event("startup")
def init_database() -> None:
    create_table_query = """
    CREATE TABLE IF NOT EXISTS todos (
        id BIGSERIAL PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        description TEXT,
        done BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """
    last_error: Exception | None = None
    for _ in range(20):
        try:
            with _db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(create_table_query)
                conn.commit()
            return
        except OperationalError as exc:
            last_error = exc
            time.sleep(2)
        except PsycopgError:
            # Handle concurrent startup race between multiple backend instances.
            if _todos_table_exists():
                return
            time.sleep(1)

    raise RuntimeError("Database is not reachable for todos initialization") from last_error


@app.get("/")
def read_root() -> dict:
    return {
        "message": "Machine Info + Todo API",
        "docs": f"{ROOT_PATH}/docs" if ROOT_PATH else "/docs",
        "endpoints": {
            "machine_info": f"{ROOT_PATH}/machine-info" if ROOT_PATH else "/machine-info",
            "todos": f"{ROOT_PATH}/todos" if ROOT_PATH else "/todos",
            "metrics": f"{ROOT_PATH}/metrics" if ROOT_PATH else "/metrics",
        },
    }


@app.get("/machine-info")
def machine_info() -> dict:
    return get_machine_info()


@app.post("/todos", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoCreate) -> Todo:
    query = """
    INSERT INTO todos (title, description, done)
    VALUES (%s, %s, FALSE)
    RETURNING id, title, description, done, created_at, updated_at;
    """
    with _db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (payload.title, payload.description))
            row = cur.fetchone()
        conn.commit()
    return _row_to_todo(row)


@app.get("/todos", response_model=list[Todo])
def list_todos(done: bool | None = None) -> list[Todo]:
    if done is None:
        query = "SELECT id, title, description, done, created_at, updated_at FROM todos ORDER BY id;"
        params = ()
    else:
        query = "SELECT id, title, description, done, created_at, updated_at FROM todos WHERE done = %s ORDER BY id;"
        params = (done,)

    with _db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
    return [_row_to_todo(row) for row in rows]


@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int) -> Todo:
    query = "SELECT id, title, description, done, created_at, updated_at FROM todos WHERE id = %s;"
    with _db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (todo_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return _row_to_todo(row)


@app.patch("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, payload: TodoUpdate) -> Todo:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return get_todo(todo_id)

    fields: list[str] = []
    values: list[object] = []
    for key in ("title", "description", "done"):
        if key in updates:
            fields.append(f"{key} = %s")
            values.append(updates[key])
    fields.append("updated_at = NOW()")
    values.append(todo_id)

    query = (
        "UPDATE todos SET "
        + ", ".join(fields)
        + " WHERE id = %s RETURNING id, title, description, done, created_at, updated_at;"
    )
    with _db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, tuple(values))
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return _row_to_todo(row)


@app.delete("/todos/{todo_id}", status_code=status.HTTP_200_OK)
def delete_todo(todo_id: int) -> dict:
    query = "DELETE FROM todos WHERE id = %s RETURNING id;"
    with _db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (todo_id,))
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return {"message": "Todo deleted", "id": row[0]}


@app.exception_handler(OperationalError)
def database_unavailable_handler(_: Request, __: OperationalError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database unavailable"},
    )


@app.get("/health/db")
def health_db() -> dict:
    try:
        with _db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
    except OperationalError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")

    return {"status": "ok", "database": "reachable"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
