from __future__ import annotations

import logging
from decimal import Decimal

from telegram import Update
from telegram.ext import ContextTypes

from app.application.use_cases.get_category_summary import (
    CategoryDTO,
    GetCategorySummaryUseCase,
)
from app.application.use_cases.get_period_summary import (
    GetPeriodSummaryUseCase,
    Period,
    SummaryDTO,
)
from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository

logger = logging.getLogger(__name__)

PERIOD_LABELS: dict[Period, str] = {
    "hoy": "hoy",
    "semana": "esta semana",
    "mes": "este mes",
}


def _format_period_summary(summary: SummaryDTO) -> str:
    label = PERIOD_LABELS.get(summary.period, summary.period)  # type: ignore[arg-type]
    if summary.count == 0:
        return f"📊 No hay gastos registrados {label}."

    lines = [
        f"📊 Gastos {label}",
        f"Total: S/. {summary.total:,.0f} {summary.currency}",
        f"Transacciones: {summary.count}",
    ]
    for cat, amount in sorted(summary.by_category.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"  • {cat.capitalize()}: S/. {amount:,.0f}")
    return "\n".join(lines)


def _format_category_summary(categories: list[CategoryDTO]) -> str:
    if not categories:
        return "📊 No hay gastos registrados este mes."

    currency = categories[0].currency
    total = sum(c.total for c in categories)
    lines = [
        f"📊 Gastos por categoría (mes actual)",
        f"Total: S/. {total:,.0f} {currency}",
    ]
    for cat in categories:
        pct = int(cat.total / total * 100) if total else 0
        lines.append(
            f"  • {cat.category.capitalize()}: S/. {cat.total:,.0f} ({pct}%) — {cat.count} items"
        )
    return "\n".join(lines)


class BotCommands:
    def __init__(
        self,
        user_repo: IUserRepository,
        get_period_summary: GetPeriodSummaryUseCase,
        get_category_summary: GetCategorySummaryUseCase,
    ) -> None:
        self._user_repo = user_repo
        self._period_summary = get_period_summary
        self._category_summary = get_category_summary

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        tg_user = update.effective_user
        user = User(
            user_id=str(tg_user.id),
            first_name=tg_user.first_name or "Usuario",
        )
        await self._user_repo.save(user)
        await update.message.reply_text(
            f"👋 Hola {user.first_name}!\n\n"
            "Soy tu asistente de gastos. Puedes enviarme:\n"
            "• 📝 Texto: 'Gasté 12000 en el bus'\n"
            "• 📷 Foto de un recibo o factura\n"
            "• 🎤 Nota de voz describiendo el gasto\n\n"
            "Comandos disponibles:\n"
            "/hoy — resumen de hoy\n"
            "/semana — resumen de la semana\n"
            "/mes — resumen del mes\n"
            "/cat — gastos por categoría"
        )

    async def hoy(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self._reply_period(update, "hoy")

    async def semana(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self._reply_period(update, "semana")

    async def mes(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self._reply_period(update, "mes")

    async def cat(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = str(update.effective_user.id)
        try:
            categories = await self._category_summary.execute(user_id)
            await update.message.reply_text(_format_category_summary(categories))
        except Exception:
            logger.exception("Error in /cat for user %s", user_id)
            await update.message.reply_text("❌ Error obteniendo categorías.")

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "❓ Comando no reconocido.\n\n"
            "Comandos disponibles:\n"
            "/hoy — resumen de hoy\n"
            "/semana — resumen de la semana\n"
            "/mes — resumen del mes\n"
            "/cat — gastos por categoría"
        )

    async def _reply_period(self, update: Update, period: Period) -> None:
        user_id = str(update.effective_user.id)
        try:
            summary = await self._period_summary.execute(user_id, period)
            await update.message.reply_text(_format_period_summary(summary))
        except Exception:
            logger.exception("Error in /%s for user %s", period, user_id)
            await update.message.reply_text("❌ Error obteniendo el resumen.")
