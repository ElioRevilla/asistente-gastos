from __future__ import annotations

import logging
import os
from decimal import Decimal

from app.application.utils.timezone import local_today

from app.application.ports.notifier import INotifier
from app.domain.repositories.expense_repository import IExpenseRepository
from app.domain.repositories.user_repository import IUserRepository

logger = logging.getLogger(__name__)


def _fmt(amount: Decimal) -> str:
    normalized = amount.normalize()
    return f"{normalized:,}" if normalized == normalized.to_integral_value() else f"{normalized:,f}"


def _format_summary(
    first_name: str,
    today: date,
    total: Decimal,
    currency: str,
    by_category: dict[str, Decimal],
) -> str:
    day_str = today.strftime("%-d %b").lstrip("0")
    lines = [f"📊 Resumen de hoy — {day_str}", f"Total: S/. {_fmt(total)} {currency}"]
    for cat, amount in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"  • {cat.capitalize()}: S/. {_fmt(amount)}")
    if not by_category:
        lines.append("Sin gastos registrados hoy.")
    return "\n".join(lines)


class SendDailySummaryUseCase:
    def __init__(
        self,
        expense_repo: IExpenseRepository,
        user_repo: IUserRepository,
        notifier: INotifier,
    ) -> None:
        self._expense_repo = expense_repo
        self._user_repo = user_repo
        self._notifier = notifier

    async def execute(self) -> int:
        """Send today's summary to all users. Returns count of messages sent."""
        today = local_today()
        user_ids = await self._expense_repo.get_all_user_ids()
        sent = 0

        for user_id in user_ids:
            try:
                user = await self._user_repo.get_by_id(user_id)
                if user is None:
                    continue

                expenses = await self._expense_repo.get_by_period(user_id, today, today)
                default_currency = os.environ.get("DEFAULT_CURRENCY", "PEN")
                currency = expenses[0].currency if expenses else default_currency
                total = sum((e.amount for e in expenses), Decimal(0))
                by_category: dict[str, Decimal] = {}
                for e in expenses:
                    by_category[e.category] = (
                        by_category.get(e.category, Decimal(0)) + e.amount
                    )

                text = _format_summary(
                    user.first_name, today, total, currency, by_category
                )
                await self._notifier.send_message(user_id, text)
                sent += 1
            except Exception:
                logger.exception("Failed to send daily summary to user %s", user_id)

        return sent
