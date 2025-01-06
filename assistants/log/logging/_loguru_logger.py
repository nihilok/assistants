import sys

from loguru import logger

from assistants.config.file_management import DATA_DIR

# Create a log directory if it doesn't exist
log_path = DATA_DIR / "logs"
log_path.mkdir(parents=True, exist_ok=True)

# Remove the default logger configuration
logger.remove()

# Add a logger configuration for logging to a file
logger.add(
    log_path / "debug.log",
    rotation="1 MB",
    retention=7,
    compression="zip",
    level="DEBUG",
    format="{time} [{level}]\t\t{module} | {message}",
)

# Add a logger configuration for logging to stdout
logger.add(
    sys.stdout,
    level="INFO",
    format="{message}",
    filter=lambda record: record["level"].name not in ["WARNING", "ERROR", "CRITICAL"],
)

# Add a logger configuration for logging warnings to stdout
logger.add(
    sys.stdout,
    level="WARNING",
    format="[{level}] {message}",
    filter=lambda record: record["level"].name not in ["ERROR", "CRITICAL"],
)

# Add a logger configuration for logging to stderr
logger.add(
    sys.stderr,
    level="ERROR",
    format="[{level}] {message}",
)
