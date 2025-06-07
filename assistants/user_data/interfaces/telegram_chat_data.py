from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel

from assistants.config.file_management import DB_PATH


class NotAuthorised(ValueError):
    pass


class ChatHistory(BaseModel):
    chat_id: int
    thread_id: Optional[str] = None
    auto_reply: bool
    chat_history: list[dict] = []


class UserData(ABC):
    DB = DB_PATH

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            self.db_path = self.DB

    @abstractmethod
    async def create_db(self):
        pass

    @abstractmethod
    async def get_chat_history(self, chat_id: int) -> ChatHistory:
        pass

    @abstractmethod
    async def save_chat_history(self, history: ChatHistory):
        pass

    @abstractmethod
    async def check_user_authorised(self, user_id: int):
        pass

    @abstractmethod
    async def check_superuser(self, user_id: int):
        pass

    @abstractmethod
    async def authorise_user(self, user_id: int):
        pass

    @abstractmethod
    async def promote_superuser(self, user_id: int):
        pass

    @abstractmethod
    async def demote_superuser(self, user_id: int):
        pass

    @abstractmethod
    async def authorise_chat(self, chat_id: int):
        pass

    @abstractmethod
    async def deauthorise_user(self, user_id: int):
        pass

    @abstractmethod
    async def deauthorise_chat(self, chat_id: int):
        pass

    @abstractmethod
    async def clear_last_thread_id(self, chat_id: int):
        pass
