"""
Production database connection helpers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class DbConfig:
    """configuration needed to build a Postgres connection string"""
    database: str
    user: str
    password: str
    host: str
    port: int = 5432


def _first_attr(config: Any, names: list[str]) -> Optional[str]:
    """return the first non-empty attribute value found in config"""
    for name in names:
        if hasattr(config, name):
            value = getattr(config, name)
            if value is None:
                continue
            text = str(value).strip()
            if text != "":
                return text
    return None


def _load_psql_config() -> DbConfig:
    """load database credentials"""
    try:
        from ProductionCode import psql_config
    except ImportError as exc:
        raise RuntimeError(
            "Missing ProductionCode/psql_config.py. "
            "Create it with your Postgres credentials, or set DATABASE_URL."
        ) from exc

    database = _first_attr(psql_config, [
        "database",
        "dbname",
        "db",
        "db_name",
        "database_name",
        "DB_NAME",
        "PSQL_DBNAME",
    ])
    user = _first_attr(psql_config, [
        "user",
        "username",
        "USER",
        "USERNAME",
        "PSQL_USER",
    ])
    password = _first_attr(psql_config, [
        "password",
        "passwd",
        "PASSWORD",
        "PSQL_PASSWORD",
    ])
    host = _first_attr(psql_config, [
        "host",
        "hostname",
        "HOST",
        "PSQL_HOST",
    ]) or "localhost"

    port_raw = _first_attr(psql_config, [
        "port",
        "PORT",
        "PSQL_PORT",
    ])
    port = 5432
    if port_raw is not None:
        try:
            port = int(port_raw)
        except ValueError:
            port = 5432

    missing = [
        name
        for name, value in [("database", database), ("user", user), ("password", password)]
        if value is None
    ]
    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(
            "psql_config.py is missing required values: "
            f"{missing_text}. "
            "Add them, or set DATABASE_URL."
        )

    return DbConfig(
        database=database or "",
        user=user or "",
        password=password or "",
        host=host,
        port=port,
    )


def get_db_url() -> str:
    """return the database url used by the application"""
    env_url = os.environ.get("DATABASE_URL")
    if env_url is not None and env_url.strip() != "":
        return env_url.strip()

    cfg = _load_psql_config()
    return f"postgresql://{cfg.user}:{cfg.password}@{cfg.host}:{cfg.port}/{cfg.database}"


def get_db():
    """create and return a records.Database connection"""
    db_url = get_db_url()

    try:
        import records  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "The 'records' package is required. Install it with: pip install records"
        ) from exc

    try:
        return records.Database(db_url)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        raise RuntimeError(f"Failed to connect to database: {exc}") from exc
