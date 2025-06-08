import asyncio
import logging
import os
import random
import time
from typing import List, Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from assistants.ai.types import AssistantInterface
from assistants.telegram_ui.lib import get_telegram_assistant
from assistants.user_data.sqlite_backend import init_db
from assistants.user_data.sqlite_backend.telegram_chat_data import (
    BotConversationMessage,
    BotConversationsTable,
    get_telegram_data,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class MessageRecord:
    """Represents a message in the conversation history"""

    def __init__(self, bot_id: str, user_id: int, text: str, timestamp: float = None):
        self.bot_id = (
            bot_id  # "user" for user messages, bot token identifier for bot messages
        )
        self.user_id = user_id
        self.text = text
        self.timestamp = timestamp or time.time()

    def to_dict(self):
        return {
            "bot_id": self.bot_id,
            "user_id": self.user_id,
            "text": self.text,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            bot_id=data["bot_id"],
            user_id=data["user_id"],
            text=data["text"],
            timestamp=data["timestamp"],
        )


class BotConversationManager:
    """Manages the conversation history for all bots"""

    def __init__(self, db_path=None):
        self.db_path = db_path or get_telegram_data().db_path
        self.bot_conversations_table = BotConversationsTable(self.db_path)

    async def initialize(self):
        await init_db()
        await self.bot_conversations_table.create_table()

    async def get_chat_history(self, chat_id: int) -> List[MessageRecord]:
        """Get the conversation history for a chat"""
        messages = await self.bot_conversations_table.get_chat_messages(chat_id)
        return [
            MessageRecord(
                bot_id=msg.bot_id,
                user_id=msg.user_id,
                text=msg.text,
                timestamp=msg.timestamp,
            )
            for msg in messages
        ]

    async def get_messages_since_last_bot_response(
        self, chat_id: int, bot_id: str
    ) -> List[MessageRecord]:
        """Get all messages since the last response from the specified bot"""
        messages = (
            await self.bot_conversations_table.get_messages_since_last_bot_response(
                chat_id, bot_id
            )
        )
        return [
            MessageRecord(
                bot_id=msg.bot_id,
                user_id=msg.user_id,
                text=msg.text,
                timestamp=msg.timestamp,
            )
            for msg in messages
        ]

    async def add_message(self, chat_id: int, message: MessageRecord):
        """Add a message to the conversation history"""
        logger.info(f"Adding message to chat {chat_id}: {message.text}")
        await self.bot_conversations_table.insert(
            BotConversationMessage(
                chat_id=chat_id,
                bot_id=message.bot_id,
                user_id=message.user_id,
                text=message.text,
                timestamp=message.timestamp,
            )
        )

    async def get_last_message(self, chat_id: int) -> Optional[MessageRecord]:
        """Get the last message in the conversation"""
        last_msg = await self.bot_conversations_table.get_last_message(chat_id)
        if last_msg:
            return MessageRecord(
                bot_id=last_msg.bot_id,
                user_id=last_msg.user_id,
                text=last_msg.text,
                timestamp=last_msg.timestamp,
            )
        return None


from assistants.config import environment

DEFAULT_CONVERSATION_BOT_INSTRUCTIONS = (
    "You communicate with users over Telegram. You may receive multiple messages from different users, and you may "
    "choose to respond to any of them at any time. You can tag the user in your response by using '@' followed by "
    "their username, but you do not need to do this if theirs was the last message in the thread. You will see each message prefixed with JSON data containing the user and time, which you should "
    "ignore in your responses, i.e. your responses should NOT include this json prefix. Your responses should be "
    "concise and to the point, without any code blocks or markdown formatting. You are a conversation bot that can "
    "respond to user messages based on the context provided. What follows are specific instructions as to your role "
    "and how you should respond. You will be given a set of instructions that you must follow when responding to user "
    "messages."
)

environment.DEFAULT_MAX_RESPONSE_TOKENS = 300
environment.ASSISTANT_INSTRUCTIONS = (
    DEFAULT_CONVERSATION_BOT_INSTRUCTIONS
    + "\n\n"
    + (
        "You are a butler called Jeeves. Your sexuality is questionable and you are "
        "prone to innuendo. You are well educated, but can be obtuse and opinionated."
    )
)
assistant_b = get_telegram_assistant()
environment.DEFAULT_MODEL = "claude-3-7-sonnet-latest"
environment.ASSISTANT_INSTRUCTIONS = (
    DEFAULT_CONVERSATION_BOT_INSTRUCTIONS
    + "\n\n"
    + (
        "You are a depressed but talented physicist and theologian called Woofter (pronounced 'whu-sta' - the 'f' is a relic from "
        "Old English). You have a short temper but always remain professional."
    )
)
assistant_a = get_telegram_assistant()


class ConversationBot:
    """Base class for conversation bots"""

    def __init__(
        self,
        token: str,
        manager: BotConversationManager,
        assistant: AssistantInterface,
        bot_id: str,
        response_interval: tuple = (10, 30),
    ):
        self.token = token
        self.manager = manager
        self.assistant = assistant
        self.bot_id = bot_id  # Short identifier for this bot
        self.response_interval = response_interval
        self.application = Application.builder().token(token).build()
        self.bot = self.application.bot
        self._setup_handlers()
        self.active_chats = set()

    def _setup_handlers(self):
        """Set up the message handlers"""
        # Override in derived classes
        pass

    async def start_responding(self, chat_id: int):
        """Start the response loop for a chat"""
        if chat_id in self.active_chats:
            return

        self.active_chats.add(chat_id)
        asyncio.create_task(self._response_loop(chat_id))

    async def stop_responding(self, chat_id: int):
        """Stop the response loop for a chat"""
        self.active_chats.discard(chat_id)

    async def _response_loop(self, chat_id: int):
        """Periodically respond to messages"""
        while chat_id in self.active_chats:
            await self._maybe_respond(chat_id)
            delay = random.randint(*self.response_interval)
            await asyncio.sleep(delay)

    async def _maybe_respond(self, chat_id: int):
        """Respond to a message if conditions are met"""
        last_message = await self.manager.get_last_message(chat_id)
        if not last_message:
            return

        # Don't respond to our own messages
        if last_message.bot_id == self.bot_id:
            return

        # Get all messages since this bot's last response
        response = await self._generate_response(chat_id, last_message)
        if response:
            # Send the original response to the chat (without prefix)
            await self.bot.send_message(chat_id=chat_id, text=response)

            # Create JSON prefix for bot response with bot_id and timestamp
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            prefix = f'{{"user": "{self.bot_id}", "time": "{current_time}"}} '
            prefixed_response = prefix + response

            # Record the bot's response with the prefix
            await self.manager.add_message(
                chat_id,
                MessageRecord(
                    bot_id=self.bot_id, user_id=self.bot.id, text=prefixed_response
                ),
            )

    async def _generate_response(
        self, chat_id: int, last_message: MessageRecord
    ) -> str:
        """Generate a response considering all messages since the bot's last response"""
        # Get all messages since this bot's last response
        recent_messages = await self.manager.get_messages_since_last_bot_response(
            chat_id, self.bot_id
        )

        # If there are no messages to respond to, return None
        if not recent_messages:
            return None

        # Update the assistant's memory with recent messages if available
        # This makes the assistant aware of the conversation context
        if hasattr(self.assistant, "memory") and recent_messages:
            # Create a conversation history from recent messages
            conversation_history = []
            for msg in recent_messages:
                role = "user"
                conversation_history.append({"role": role, "content": msg.text})

            # Update the assistant's memory with this conversation context
            if previous := conversation_history[:-1]:
                self.assistant.memory.extend(previous)

        # If there are multiple messages, use the most recent one as the direct prompt
        # but the assistant will have context from all messages
        response = await self.assistant.converse(
            last_message.text, f"{chat_id}-{self.bot_id}"
        )
        return response.text_content if response else None

    async def start(self):
        """Start the bot"""
        await self.application.initialize()
        await self.application.start()
        asyncio.create_task(self.application.updater.start_polling())

    async def stop(self):
        """Stop the bot"""
        await self.application.stop()
        await self.application.shutdown()


class MainConversationBot(ConversationBot):
    """The main bot that records all messages it sees"""

    def _setup_handlers(self):
        # Handle /start command
        self.application.add_handler(CommandHandler("start", self._start_command))

        # Handle /stop command
        self.application.add_handler(CommandHandler("stop", self._stop_command))

        # Handle all messages
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._message_handler)
        )

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command"""
        chat_id = update.effective_chat.id
        await self.start_responding(chat_id)
        await update.message.reply_text(
            f"Bot {self.bot_id} is active. Type /stop to deactivate."
        )

    async def _stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /stop command"""
        chat_id = update.effective_chat.id
        await self.stop_responding(chat_id)
        await update.message.reply_text(
            f"Bot {self.bot_id} is now inactive. Type /start to reactivate."
        )

    async def _message_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle incoming messages"""
        # Record the user message
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        if not update.message:
            logger.warning("Received an update without a message.")
            logger.info("Update details: %s", update.to_dict())
            return
        text = update.message.text

        # Create JSON prefix with user info and timestamp
        user_name = update.effective_user.username or update.effective_user.first_name
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        prefix = f'{{"user": "{user_name}", "time": "{current_time}"}} '
        prefixed_text = prefix + text

        await self.manager.add_message(
            chat_id, MessageRecord(bot_id="user", user_id=user_id, text=prefixed_text)
        )

        # Ensure the response loop is running
        await self.start_responding(chat_id)


class SecondaryConversationBot(ConversationBot):
    """Secondary bot that only records its own responses"""

    def _setup_handlers(self):
        # Only handle /start and /stop commands
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("stop", self._stop_command))

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command"""
        chat_id = update.effective_chat.id
        logger.info(f"Starting bot {self.bot_id} for chat {chat_id}")
        await self.start_responding(chat_id)
        await update.message.reply_text(
            f"Bot {self.bot_id} is now active. Type /stop to deactivate."
        )

    async def _stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /stop command"""
        chat_id = update.effective_chat.id
        await self.stop_responding(chat_id)
        await update.message.reply_text(
            f"Bot {self.bot_id} is now inactive. Type /start to reactivate."
        )


async def main():
    # Initialize the conversation manager
    manager = BotConversationManager()
    await manager.initialize()

    # Create the bots with different response intervals
    main_bot = MainConversationBot(
        token=os.environ.get("MAIN_BOT_TOKEN"),
        manager=manager,
        assistant=assistant_a,
        bot_id="woofterbot",
        response_interval=(5, 30),  # Respond every 5-30 seconds
    )

    secondary_bot = SecondaryConversationBot(
        token=os.environ.get("SECONDARY_BOT_TOKEN"),
        manager=manager,
        assistant=assistant_b,
        bot_id="jeevzbot",
        response_interval=(5, 30),  # Respond every 5-30 seconds
    )

    # Start the bots
    await main_bot.start()
    await secondary_bot.start()

    # Keep the script running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        # Stop the bots on keyboard interrupt
        await main_bot.stop()
        await secondary_bot.stop()


if __name__ == "__main__":
    # Check if required environment variables are set
    if not os.environ.get("MAIN_BOT_TOKEN") or not os.environ.get(
        "SECONDARY_BOT_TOKEN"
    ):
        print(
            "Please set MAIN_BOT_TOKEN and SECONDARY_BOT_TOKEN environment variables."
        )
        exit(1)

    asyncio.run(main())
