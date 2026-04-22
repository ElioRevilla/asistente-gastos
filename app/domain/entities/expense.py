from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import uuid4

ExpenseSource = Literal["text", "image", "audio"]

VALID_CATEGORIES = {
    "comida",
    "transporte",
    "hogar",
    "salud",
    "ocio",
    "ropa",
    "educación",
    "otro",
}


@dataclass
class ExpenseData:
    """DTO returned by the AI extractor before persistence."""
    amount: Decimal
    currency: str
    category: str
    description: str
    date: date


@dataclass
class Expense:
    """Core domain entity representing a recorded expense."""
    user_id: str
    amount: Decimal
    currency: str
    category: str
    description: str
    date: date
    source: ExpenseSource
    id: str = field(default_factory=lambda: uuid4().hex)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("amount must be positive")
        if self.category not in VALID_CATEGORIES:
            self.category = "otro"
