import os
from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel

DB = os.environ.get("TG_USER_DATA")


class NotAuthorized(ValueError):
    pass


class ChatHistory(BaseModel):
    chat_id: int
    thread_id: Optional[str] = None
    auto_reply: bool


class UserData(ABC):
    DB = DB

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
