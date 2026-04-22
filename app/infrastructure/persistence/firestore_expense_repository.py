from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from decimal import Decimal

from google.cloud import firestore
from google.cloud.firestore_v1.async_client import AsyncClient

from app.domain.entities.expense import Expense
from app.domain.repositories.expense_repository import IExpenseRepository

logger = logging.getLogger(__name__)

COLLECTION = "expenses"


class FirestoreExpenseRepository(IExpenseRepository):
    def __init__(self, db: AsyncClient) -> None:
        self._db = db

    async def save(self, expense: Expense) -> None:
        doc = {
            "user_id": expense.user_id,
            "amount": float(expense.amount),
            "currency": expense.currency,
            "category": expense.category,
            "description": expense.description,
            "date": datetime.combine(expense.date, datetime.min.time()).replace(
                tzinfo=timezone.utc
            ),
            "source": expense.source,
            "created_at": expense.created_at.replace(tzinfo=timezone.utc),
        }
        await self._db.collection(COLLECTION).document(expense.id).set(doc)

    async def get_by_period(
        self, user_id: str, start: date, end: date
    ) -> list[Expense]:
        start_dt = datetime.combine(start, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        end_dt = datetime.combine(end, datetime.max.time()).replace(
            tzinfo=timezone.utc
        )

        query = (
            self._db.collection(COLLECTION)
            .where("user_id", "==", user_id)
            .where("date", ">=", start_dt)
            .where("date", "<=", end_dt)
            .order_by("date", direction=firestore.Query.DESCENDING)
        )

        docs = await query.get()
        return [self._to_entity(doc.id, doc.to_dict()) for doc in docs]  # type: ignore[arg-type]

    async def get_by_category(
        self, user_id: str, start: date, end: date
    ) -> dict[str, list[Expense]]:
        expenses = await self.get_by_period(user_id, start, end)
        result: dict[str, list[Expense]] = {}
        for expense in expenses:
            result.setdefault(expense.category, []).append(expense)
        return result

    async def get_all_user_ids(self) -> list[str]:
        docs = await self._db.collection(COLLECTION).select(["user_id"]).get()
        return list({doc.to_dict()["user_id"] for doc in docs})  # type: ignore[index]

    @staticmethod
    def _to_entity(doc_id: str, data: dict) -> Expense:
        raw_date = data["date"]
        if isinstance(raw_date, datetime):
            expense_date = raw_date.date()
        else:
            expense_date = date.today()

        created_at = data.get("created_at")
        if not isinstance(created_at, datetime):
            created_at = datetime.utcnow()

        return Expense(
            id=doc_id,
            user_id=data["user_id"],
            amount=Decimal(str(data["amount"])),
            currency=data["currency"],
            category=data["category"],
            description=data["description"],
            date=expense_date,
            source=data["source"],
            created_at=created_at,
        )
