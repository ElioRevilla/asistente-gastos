from __future__ import annotations

from dataclasses import dataclass


@dataclass
class User:
    """Telegram user registered in the system."""
    user_id: str          # Telegram user_id as string
    first_name: str
    timezone: str = "America/Bogota"
