import logging.config
import re

from asgi_correlation_id import CorrelationIdFilter
from pythonjsonlogger.json import JsonFormatter
from timing_asgi import TimingClient

from app.core.config import settings

timing_logger = logging.getLogger("app.timing")


def setup_logging() -> None:
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JsonFormatter,
                "format": "correlation_id,levelname,asctime,created,name,module,funcName,lineno,message,exc_info",
                "style": ",",
                "rename_fields": {"lineno": "line"},
                "timestamp": True,
            },
        },
        "filters": {
            "warnings_and_below": {"()": filter_maker, "level": "WARNING"},
            "correlation_id": {"()": CorrelationIdFilter},
            "secrets_masking": {"()": SecretsMaskingFilter},
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "json",
                "stream": "ext://sys.stdout",
                "filters": ["warnings_and_below", "correlation_id", "secrets_masking"],
            },
            "stderr": {
                "class": "logging.StreamHandler",
                "level": "WARNING",
                "formatter": "json",
                "stream": "ext://sys.stderr",
                "filters": ["correlation_id", "secrets_masking"],
            },
            "app_file_json": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "json",
                "filename": "logs/app.log.jsonl",
                "maxBytes": settings.LOG_FILE_MAX_SIZE,
                "backupCount": settings.MAX_COUNT_LOG_FILES,
                "filters": ["correlation_id", "secrets_masking"],
            },
        },
        "loggers": {
            "redis": {"level": "WARNING"},
            "uvicorn": {
                "handlers": [ "stdout", "app_file_json",
                ],
                "level": "WARNING",
            },
            "uvicorn.access": {
                "handlers": ["stdout", "app_file_json",
                ],
                "level": "WARNING",
            },
            "app.timing": {
                "handlers": ["stdout", "app_file_json"],
                "level": "WARNING",
            },
            "sqlalchemy.engine": {
                "handlers": ["stdout", "app_file_json"],
                "level": "WARNING",
            },
        },
        "root": {"level": "DEBUG", "handlers": ["stdout", "stderr"]},
    }

    if settings.DEBUG:
        config["root"]["handlers"].append("app_file_json")

    logging.config.dictConfig(config)


def filter_maker(level):
    level = getattr(logging, level)

    def filter(record):
        return record.levelno <= level

    return filter


class SecretsMaskingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except (TypeError, ValueError, KeyError):
            return True
        pattern = r"(token=)([a-zA-Z0-9_\-\.]+)"
        replacement = r"\1[REDACTED]"
        message = re.sub(pattern, replacement, message)
        record.msg = message
        record.args = None

        return True


class LogTimings(TimingClient):
    def timing(self, metric_name, timing, tags):
        timing_logger.info(
            "timing",
            extra={
                "metric": metric_name,
                "duration": timing,
                "tags": tags,
            },
        )
