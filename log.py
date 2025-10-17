import logging.config
import os
import sys

class LoggerWriter:
    """
    Custom stream handler to redirect stdout/stderr to a logger.
    """
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.buffer = '' # To handle incomplete lines

    def write(self, message):
        # Filter out empty messages and just newlines
        if message.strip() == '':
            return

        # Append to buffer
        self.buffer += message

        # Process line by line
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            # Emit the full line to the logger
            self.logger.log(self.level, line.strip().encode("utf-8"))

    def flush(self):
        # Flush any remaining content in the buffer (if no newline at end)
        if self.buffer:
            self.logger.log(self.level, self.buffer.strip().encode("utf-8"))
            self.buffer = ''

LOG_DIR = "logs"
APP_LOG_FILE = os.path.join(LOG_DIR, "server.log")

os.makedirs(LOG_DIR, exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "verbose": {
            "format": "%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s"
        },
        "simple": {
            "format": "%(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "verbose",
            "filename": APP_LOG_FILE,
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "level": "DEBUG"
        },
        "error_file": {
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": os.path.join(LOG_DIR, "errors.log"),
            "level": "ERROR"
        }
    },
    "loggers": {
        '': {
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": False
        },
        "chat": {
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": False
        },
        "chainlit": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False
        },
        "langchain": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False
        },
        "langgraph": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False
        },
        'httpx': {
            'handlers': ['file'],
            'level': 'INFO', # Or DEBUG if you want to see request/response details
            'propagate': False
        },
        'httpcore': {
            'handlers': ['file'],
            'level': 'INFO', # Or DEBUG for even lower-level network details
            'propagate': False
        },
        'openai': { # If you're using OpenAI models directly
            'handlers': ['file'],
            'level': 'INFO', # OpenAI library also logs
            'propagate': False
        },
        "fastmcp": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False
        },
        "fastapi": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False
        },
        "mcp": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False
        },
        "mcp_use": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False
        },
        "asyncio": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False
        },
    }
}

logging.config.dictConfig(LOGGING_CONFIG)

stdout_logger = logging.getLogger("stdout_logger")
# stderr_logger = logging.getLogger("stderr_logger")

sys.stdout = LoggerWriter(stdout_logger, logging.INFO)
# sys.stderr = LoggerWriter(stderr_logger, logging.INFO)

logger = logging.getLogger("zen7-payment-agent")