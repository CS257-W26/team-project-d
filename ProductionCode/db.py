"""
Production database connection helpers.
"""

from __future__ import annotations

import importlib
import os
from typing import Any, List

_CONFIG_MODULE = "ProductionCode.psql_config"
_REQUIRED = ("DATABASE", "USER", "PASSWORD", "HOST")


def _import(module_name: str) -> Any:
    """import and return a module by name"""
    return importlib.import_module(module_name)


def _val(cfg: Any, name: str, default: Any = "") -> str:
    """return a stripped config value as text ('' if missing)"""
    return str(getattr(cfg, name, default) or "").strip()


def _missing(cfg: Any) -> List[str]:
    """return missing required psql_config keys (lowercase)"""
    return [key.lower() for key in _REQUIRED if not _val(cfg, key)]


def _port(cfg: Any) -> int:
    """return PORT from config or 5432"""
    try:
        return int(_val(cfg, "PORT", 5432) or 5432)
    except ValueError:
        return 5432


def _import_config() -> Any:
    """import and return ProductionCode.psql_config"""
    try:
        return _import(_CONFIG_MODULE)
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing ProductionCode/psql_config.py. "
            "Create it with DATABASE/USER/PASSWORD/HOST (and optional PORT), "
            "or set DATABASE_URL."
        ) from exc


def _url_from_config(cfg: Any) -> str:
    """build a Postgres URL from psql_config"""
    missing = _missing(cfg)
    if missing:
        raise RuntimeError(
            "psql_config.py is missing required values: "
            f"{', '.join(missing)}. Add them, or set DATABASE_URL."
        )
    return (
        f"postgresql://{_val(cfg, 'USER')}:{_val(cfg, 'PASSWORD')}"
        f"@{_val(cfg, 'HOST')}:{_port(cfg)}/{_val(cfg, 'DATABASE')}"
    )


def get_db_url() -> str:
    """return the database URL used by the application"""
    url = os.environ.get("DATABASE_URL", "").strip()
    return url or _url_from_config(_import_config())


def get_db():
    """create and return a records.Database connection"""
    records = _import("records")
    try:
        return records.Database(get_db_url())
    except Exception as exc:
        raise RuntimeError(f"Failed to connect to database: {exc}") from exc
