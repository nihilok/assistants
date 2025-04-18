from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from assistants.log import logger
from assistants.telegram_ui.commands import (
    promote_user,
    demote_user,
    authorise_chat,
    authorise_user,
    deauthorise_chat,
    deauthorise_user,
    new_thread,
    toggle_auto_reply,
    message_handler,
    generate_image,
    respond_voice,
)
from assistants.telegram_ui.lib import assistant


def build_bot(token: str) -> Application:
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("add_chat", authorise_chat))
    application.add_handler(CommandHandler("remove_chat", deauthorise_chat))
    application.add_handler(CommandHandler("add_user", authorise_user))
    application.add_handler(CommandHandler("remove_user", deauthorise_user))
    application.add_handler(CommandHandler("promote", promote_user))
    application.add_handler(CommandHandler("demote", demote_user))
    application.add_handler(CommandHandler("new_thread", new_thread))
    application.add_handler(CommandHandler("auto_reply", toggle_auto_reply))
    application.add_handler(CommandHandler("image", generate_image))
    application.add_handler(CommandHandler("voice", respond_voice))
    application.add_handler(MessageHandler(filters.TEXT, message_handler))
    logger.info("Setup complete!")
    return application


def run_polling(application: Application):
    logger.info("Telegram bot is running...")
    application.run_polling()


async def async_setup():
    await assistant.start()


def setup_and_run(token: str):
    application = build_bot(token)
    run_polling(application)
