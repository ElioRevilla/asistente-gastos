from __future__ import annotations

import json
import logging
import os
from datetime import date
from decimal import Decimal, InvalidOperation

from app.application.utils.timezone import local_today

import vertexai
from vertexai.generative_models import GenerationConfig, GenerativeModel, Part

from app.application.ports.ai_extractor import IAIExtractor, NoExpenseDetectedError
from app.domain.entities.expense import ExpenseData
from app.infrastructure.ai.prompts import get_audio_prompt, get_expense_prompt

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-2.5-flash"


class GeminiExtractor(IAIExtractor):
    def __init__(self, project_id: str, location: str = "us-central1") -> None:
        vertexai.init(project=project_id, location=location)
        self._default_currency = os.environ.get("DEFAULT_CURRENCY", "COP").upper()
        self._model = GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

    async def extract(
        self,
        text: str | None = None,
        image_bytes: bytes | None = None,
        audio_bytes: bytes | None = None,
    ) -> ExpenseData:
        if sum(v is not None for v in [text, image_bytes, audio_bytes]) != 1:
            raise ValueError("Exactly one of text, image_bytes, or audio_bytes must be provided")

        if text is not None:
            response = await self._extract_from_text(text)
        elif image_bytes is not None:
            response = await self._extract_from_image(image_bytes)
        else:
            response = await self._extract_from_audio(audio_bytes)  # type: ignore[arg-type]

        return self._parse_response(response)

    async def _extract_from_text(self, text: str) -> str:
        result = await self._model.generate_content_async(
            [get_expense_prompt(self._default_currency), text]
        )
        return result.text

    async def _extract_from_image(self, image_bytes: bytes) -> str:
        part = Part.from_data(data=image_bytes, mime_type="image/jpeg")
        result = await self._model.generate_content_async(
            [get_expense_prompt(self._default_currency), part]
        )
        return result.text

    async def _extract_from_audio(self, audio_bytes: bytes) -> str:
        part = Part.from_data(data=audio_bytes, mime_type="audio/ogg")
        result = await self._model.generate_content_async(
            [get_audio_prompt(self._default_currency), part]
        )
        return result.text

    def _parse_response(self, raw: str) -> ExpenseData:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Gemini returned non-JSON: %s", raw)
            raise ValueError("AI response is not valid JSON")

        if data.get("amount") is None:
            raise NoExpenseDetectedError()

        try:
            amount = Decimal(str(data["amount"]))
        except (KeyError, InvalidOperation) as exc:
            raise ValueError("Missing or invalid 'amount' in AI response") from exc

        expense_date = local_today()
        if raw_date := data.get("date"):
            try:
                expense_date = date.fromisoformat(raw_date)
            except ValueError:
                pass

        return ExpenseData(
            amount=amount,
            currency=data.get("currency", self._default_currency).upper(),
            category=data.get("category", "otro").lower(),
            description=data.get("description", "")[:80],
            date=expense_date,
        )
