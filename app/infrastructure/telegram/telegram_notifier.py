from __future__ import annotations

import logging

from telegram import Bot

from app.application.ports.notifier import INotifier

logger = logging.getLogger(__name__)


class TelegramNotifier(INotifier):
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def send_message(self, user_id: str, text: str) -> None:
        await self._bot.send_message(chat_id=int(user_id), text=text)
