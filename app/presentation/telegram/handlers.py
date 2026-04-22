from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.application.use_cases.register_expense import RegisterExpenseUseCase
from app.domain.entities.expense import Expense
from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository

logger = logging.getLogger(__name__)


def _format_amount(amount) -> str:
    normalized = amount.normalize()
    return f"{normalized:,}"


def _format_confirmation(expense: Expense) -> str:
    return (
        f"✅ Gasto registrado\n"
        f"💰 S/. {_format_amount(expense.amount)} {expense.currency}\n"
        f"🏷️ {expense.category.capitalize()}\n"
        f"📝 {expense.description}"
    )


class ExpenseHandlers:
    def __init__(self, register_expense: RegisterExpenseUseCase, user_repo: IUserRepository) -> None:
        self._register = register_expense
        self._user_repo = user_repo

    async def _ensure_user(self, update: Update) -> None:
        tg_user = update.effective_user
        user = User(
            user_id=str(tg_user.id),
            first_name=tg_user.first_name or "Usuario",
        )
        await self._user_repo.save(user)

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.text:
            return
        user_id = str(update.effective_user.id)
        text = update.message.text

        await self._ensure_user(update)
        await update.message.reply_text("⏳ Procesando...")
        try:
            expense = await self._register.execute(
                user_id=user_id, source="text", text=text
            )
            await update.message.reply_text(_format_confirmation(expense))
        except Exception:
            logger.exception("Error registering text expense for user %s", user_id)
            await update.message.reply_text(
                "❌ No pude extraer el gasto. Intenta con: 'Gasté 15000 en almuerzo'"
            )

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.photo:
            return
        user_id = str(update.effective_user.id)

        await self._ensure_user(update)
        await update.message.reply_text("📷 Analizando recibo...")
        try:
            photo = update.message.photo[-1]  # highest resolution
            file = await context.bot.get_file(photo.file_id)
            image_bytes = await file.download_as_bytearray()

            expense = await self._register.execute(
                user_id=user_id, source="image", image_bytes=bytes(image_bytes)
            )
            await update.message.reply_text(_format_confirmation(expense))
        except Exception:
            logger.exception("Error registering photo expense for user %s", user_id)
            await update.message.reply_text(
                "❌ No pude leer el recibo. Asegúrate que la imagen sea clara."
            )

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.voice:
            return
        user_id = str(update.effective_user.id)

        await self._ensure_user(update)
        await update.message.reply_text("🎤 Transcribiendo audio...")
        try:
            file = await context.bot.get_file(update.message.voice.file_id)
            audio_bytes = await file.download_as_bytearray()

            expense = await self._register.execute(
                user_id=user_id, source="audio", audio_bytes=bytes(audio_bytes)
            )
            await update.message.reply_text(_format_confirmation(expense))
        except Exception:
            logger.exception("Error registering voice expense for user %s", user_id)
            await update.message.reply_text(
                "❌ No pude procesar el audio. Intenta de nuevo."
            )
