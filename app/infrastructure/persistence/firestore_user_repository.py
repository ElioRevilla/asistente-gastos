from __future__ import annotations

import logging

from google.cloud.firestore_v1.async_client import AsyncClient

from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository

logger = logging.getLogger(__name__)

COLLECTION = "users"


class FirestoreUserRepository(IUserRepository):
    def __init__(self, db: AsyncClient) -> None:
        self._db = db

    async def save(self, user: User) -> None:
        doc = {
            "user_id": user.user_id,
            "first_name": user.first_name,
            "timezone": user.timezone,
        }
        await self._db.collection(COLLECTION).document(user.user_id).set(doc)

    async def get_by_id(self, user_id: str) -> User | None:
        doc = await self._db.collection(COLLECTION).document(user_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        return User(
            user_id=data["user_id"],
            first_name=data["first_name"],
            timezone=data.get("timezone", "America/Bogota"),
        )

    async def get_all(self) -> list[User]:
        docs = await self._db.collection(COLLECTION).get()
        return [
            User(
                user_id=d["user_id"],
                first_name=d["first_name"],
                timezone=d.get("timezone", "America/Bogota"),
            )
            for doc in docs
            if (d := doc.to_dict())
        ]
