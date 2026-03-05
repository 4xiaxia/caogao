# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import socket

import click
import uvicorn

from ..constant import LOG_LEVEL_ENV
from ..config.utils import write_last_api
from ..utils.logging import setup_logger


def _find_free_port(host: str, start: int, max_tries: int = 20) -> int:
    """Return the first free TCP port starting from *start*."""
    for port in range(start, start + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError(
        f"No free port found in range {start}–{start + max_tries - 1}"
    )


@click.command("app")
@click.option(
    "--host",
    default="127.0.0.1",
    show_default=True,
    help="Bind host",
)
@click.option(
    "--port",
    default=8088,
    type=int,
    show_default=True,
    help="Bind port",
)
@click.option("--reload", is_flag=True, help="Enable auto-reload (dev only)")
@click.option(
    "--workers",
    default=1,
    type=int,
    show_default=True,
    help="Worker processes",
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(
        ["critical", "error", "warning", "info", "debug", "trace"],
        case_sensitive=False,
    ),
    show_default=True,
    help="Log level",
)
def app_cmd(
    host: str,
    port: int,
    reload: bool,
    workers: int,
    log_level: str,
) -> None:
    """Run CoPaw FastAPI app."""
    # Auto-switch port if requested port is already in use
    actual_port = _find_free_port(host, port)
    if actual_port != port:
        click.echo(
            f"⚠️  Port {port} is in use, switching to port {actual_port}",
            err=True,
        )

    # Persist last used host/port for other terminals
    write_last_api(host, actual_port)
    os.environ[LOG_LEVEL_ENV] = log_level
    setup_logger(log_level)
    if log_level in ("debug", "trace"):
        from .main import log_init_timings

        log_init_timings()

    uvicorn.run(
        "copaw.app._app:app",
        host=host,
        port=actual_port,
        reload=reload,
        workers=workers,
        log_level=log_level,
    )
