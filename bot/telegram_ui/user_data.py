import os
from abc import ABC, abstractmethod

from pydantic import BaseModel


DB = os.environ.get("TG_USER_DB", "tg_user_data.db")


class NotAuthorized(ValueError):
    pass


class ChatHistory(BaseModel):
    chat_id: int
    history: list[dict[str, str]]


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
    async def authorise_user(self, user_id: int):
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
