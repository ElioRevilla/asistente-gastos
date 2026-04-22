from __future__ import annotations

from abc import ABC, abstractmethod


class INotifier(ABC):
    """Port: sends a text message to a user."""

    @abstractmethod
    async def send_message(self, user_id: str, text: str) -> None: ...
