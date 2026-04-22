from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from app.domain.entities.expense import Expense


class IExpenseRepository(ABC):

    @abstractmethod
    async def save(self, expense: Expense) -> None: ...

    @abstractmethod
    async def get_by_period(
        self, user_id: str, start: date, end: date
    ) -> list[Expense]: ...

    @abstractmethod
    async def get_by_category(
        self, user_id: str, start: date, end: date
    ) -> dict[str, list[Expense]]: ...

    @abstractmethod
    async def get_all_user_ids(self) -> list[str]: ...
