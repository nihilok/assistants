import os

HOME_DIR = os.environ["HOME"]
DB_TABLE = os.environ.get("USER_DATA_DB", f"{HOME_DIR}/.assistants_user_data.db")
