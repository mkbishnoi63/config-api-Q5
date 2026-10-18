
import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


def coerce(key, value):
    if key in {"port", "workers"}:
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


def load_config():
    config = DEFAULTS.copy()

    yaml_path = BASE_DIR / "config.development.yaml"
    if yaml_path.exists():
        with yaml_path.open(encoding="utf-8") as file:
            yaml_config = yaml.safe_load(file) or {}
        config.update(yaml_config)

    env_file = dotenv_values(BASE_DIR / ".env")
    for key, value in env_file.items():
        if value is None:
            continue
        if key == "NUM_WORKERS":
            config["workers"] = value
        elif key.startswith("APP_"):
            config[key[4:].lower()] = value

    for key, value in os.environ.items():
        if key.startswith("APP_"):
            config[key[4:].lower()] = value

    return config


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = load_config()

    for override in set:
        if "=" not in override:
            continue
        key, value = override.split("=", 1)
        key = key.strip().lower()
        if key:
            config[key] = value

    result = {
        key: coerce(key, value)
        for key, value in config.items()
    }
    result["api_key"] = "****"
    return result
