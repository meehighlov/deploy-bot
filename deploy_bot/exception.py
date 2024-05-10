from functools import wraps

from telegram import Update


def do_default_reply_on_any_error(command_handler):

    @wraps(command_handler)
    async def handle(update: Update, context):
        try:
            return await command_handler(update, context)
        except Exception as e:
            await update.effective_user.send_message(text=f"Прерываю накат из-за: {e}")

        return

    return handle
