from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.domain.repositories.expense_repository import IExpenseRepository


@dataclass
class CategoryDTO:
    category: str
    total: Decimal
    currency: str
    count: int


class GetCategorySummaryUseCase:
    def __init__(self, expense_repo: IExpenseRepository) -> None:
        self._repo = expense_repo

    async def execute(self, user_id: str) -> list[CategoryDTO]:
        today = date.today()
        start = today.replace(day=1)
        by_category = await self._repo.get_by_category(user_id, start, today)

        result: list[CategoryDTO] = []
        for category, expenses in by_category.items():
            if not expenses:
                continue
            total = sum((e.amount for e in expenses), Decimal(0))
            result.append(
                CategoryDTO(
                    category=category,
                    total=total,
                    currency=expenses[0].currency,
                    count=len(expenses),
                )
            )

        result.sort(key=lambda c: c.total, reverse=True)
        return result
