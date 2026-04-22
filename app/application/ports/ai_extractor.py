from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.expense import ExpenseData


class IAIExtractor(ABC):
    """Port: extracts expense data from any input modality."""

    @abstractmethod
    async def extract(
        self,
        text: str | None = None,
        image_bytes: bytes | None = None,
        audio_bytes: bytes | None = None,
    ) -> ExpenseData:
        """
        Exactly one of text, image_bytes, or audio_bytes must be provided.
        Returns structured ExpenseData parsed by the AI model.
        """
        ...
