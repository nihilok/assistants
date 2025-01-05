import os
from pathlib import Path

HOME_DIR = Path.home()

_override_config_dir = os.getenv("ASSISTANTS_CONFIG_DIR")

CONFIG_DIR = (
    Path(_override_config_dir)
    if _override_config_dir
    else HOME_DIR / ".config" / "assistants"
)

if not CONFIG_DIR.exists():
    CONFIG_DIR.mkdir(parents=True)

_override_data_dir = os.getenv("ASSISTANTS_DATA_DIR")

DATA_DIR = (
    Path(_override_data_dir)
    if _override_data_dir
    else HOME_DIR / ".local" / "share" / "assistants"
)

DB_PATH = DATA_DIR / "data.db"
