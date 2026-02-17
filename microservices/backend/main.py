
#!/usr/bin/env python3
import os
import platform
import socket
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT_PATH = os.getenv("ROOT_PATH", "")

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

START_TIME = time.time()


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


@app.get("/")
def read_root() -> dict:
    return {
        "message": "Machine Info API",
        "docs": f"{ROOT_PATH}/docs" if ROOT_PATH else "/docs",
        "endpoint": f"{ROOT_PATH}/machine-info" if ROOT_PATH else "/machine-info",
    }


@app.get("/machine-info")
def machine_info() -> dict:
    return get_machine_info()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
