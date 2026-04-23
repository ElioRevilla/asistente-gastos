from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo

from app.domain.repositories.expense_repository import IExpenseRepository

Period = Literal["hoy", "semana", "mes"]


@dataclass
class SummaryDTO:
    period: str
    total: Decimal
    currency: str
    by_category: dict[str, Decimal]
    count: int


def _today_local() -> date:
    tz = ZoneInfo(os.environ.get("DEFAULT_TIMEZONE", "America/Lima"))
    return datetime.now(tz).date()


def _period_range(period: Period) -> tuple[date, date]:
    today = _today_local()
    if period == "hoy":
        return today, today
    if period == "semana":
        start = today - timedelta(days=today.weekday())
        return start, today
    # mes
    return today.replace(day=1), today


class GetPeriodSummaryUseCase:
    def __init__(self, expense_repo: IExpenseRepository) -> None:
        self._repo = expense_repo

    async def execute(self, user_id: str, period: Period) -> SummaryDTO:
        start, end = _period_range(period)
        expenses = await self._repo.get_by_period(user_id, start, end)

        if not expenses:
            return SummaryDTO(
                period=period,
                total=Decimal(0),
                currency="COP",
                by_category={},
                count=0,
            )

        currency = expenses[0].currency
        total = sum((e.amount for e in expenses), Decimal(0))

        by_category: dict[str, Decimal] = {}
        for e in expenses:
            by_category[e.category] = by_category.get(e.category, Decimal(0)) + e.amount

        return SummaryDTO(
            period=period,
            total=total,
            currency=currency,
            by_category=by_category,
            count=len(expenses),
        )
