from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.user import User


class IUserRepository(ABC):

    @abstractmethod
    async def save(self, user: User) -> None: ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None: ...

    @abstractmethod
    async def get_all(self) -> list[User]: ...
