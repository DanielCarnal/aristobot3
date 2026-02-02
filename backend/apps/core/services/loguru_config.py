# -*- coding: utf-8 -*-
"""
Configuration centralisee Loguru pour tous les terminaux Aristobot.

Rotation: 2 minutes | Retention: 10 minutes | Format: JSON serialize
Niveau: INFO par defaut, configurable via env var ARISTOBOT_LOG_LEVEL
"""
import os
import sys
import contextvars
from loguru import logger
from django.conf import settings

# Repertoire logs a la racine du projet
LOG_DIR = os.path.join(str(settings.BASE_DIR.parent), 'logs')

# ContextVar pour propager trace_id sans toucher logger.configure()
# Utilisé par T5 (native_exchange_manager) pour binder le trace_id reçu de T3
trace_id_ctx = contextvars.ContextVar('trace_id', default=None)


def _inject_trace_id(record):
    """Filtre loguru: injecte trace_id depuis contextvars dans chaque record.
    Ne modifie rien si le contextvar est None (comportement par defaut)."""
    tid = trace_id_ctx.get()
    if tid is not None:
        record["extra"]["trace_id"] = tid
    return True


def setup_loguru(terminal_name: str):
    """
    Configure Loguru pour un terminal donne.

    - Rotation: nouveau fichier toutes les 2 minutes
    - Retention: 10 minutes (~5 fichiers par terminal)
    - Fichier: JSON seri alise (serialize=True)
    - Console: format lisible avec timestamp ms
    - Niveau: INFO par defaut, DEBUG via ARISTOBOT_LOG_LEVEL=DEBUG

    Args:
        terminal_name: Identifiant du terminal (ex: 'terminal2', 'terminal3')
    """
    logger.remove()

    log_level = os.getenv("ARISTOBOT_LOG_LEVEL", "INFO").upper()

    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"{terminal_name}.log")

    # Handler fichier: JSON seri alise, rotation 2min, retention 10min
    logger.add(
        log_file,
        level=log_level,
        rotation="2 minutes",
        retention="10 minutes",
        serialize=True,
        enqueue=True,
        filter=_inject_trace_id,
    )

    # Handler console: format lisible pour monitoring
    logger.add(
        sys.stderr,
        level=log_level,
        format="[{time:HH:mm:ss.SSS}] [{extra[terminal_name]}] [{level: <8}] {message}",
        colorize=True,
        filter=_inject_trace_id,
    )

    # Contexte par defaut porté sur tous les logs
    logger.configure(extra={
        "terminal_name": terminal_name,
        "trace_id": None,
    })

    return logger
