from functools import wraps
from typing import Callable, Any

from telegram import Update

from deploy_bot.config import config


def auth(command_handler: Callable):

    @wraps(command_handler)
    async def handle(update: Update, context: Any):
        username = update.effective_user.username

        if username not in config.bot_owners:
            return

        return await command_handler(update, context)

    return handle
