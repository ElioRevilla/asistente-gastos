from __future__ import annotations

from datetime import date

from app.application.ports.ai_extractor import IAIExtractor
from app.domain.entities.expense import Expense, ExpenseSource
from app.domain.repositories.expense_repository import IExpenseRepository
from app.domain.repositories.user_repository import IUserRepository


class RegisterExpenseUseCase:
    def __init__(
        self,
        expense_repo: IExpenseRepository,
        user_repo: IUserRepository,
        extractor: IAIExtractor,
    ) -> None:
        self._expense_repo = expense_repo
        self._user_repo = user_repo
        self._extractor = extractor

    async def execute(
        self,
        user_id: str,
        source: ExpenseSource,
        text: str | None = None,
        image_bytes: bytes | None = None,
        audio_bytes: bytes | None = None,
    ) -> Expense:
        data = await self._extractor.extract(
            text=text,
            image_bytes=image_bytes,
            audio_bytes=audio_bytes,
        )

        expense = Expense(
            user_id=user_id,
            amount=data.amount,
            currency=data.currency,
            category=data.category,
            description=data.description,
            date=data.date or date.today(),
            source=source,
        )

        await self._expense_repo.save(expense)
        return expense
