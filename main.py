from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from google.cloud import firestore
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

load_dotenv()

from app.application.use_cases.get_category_summary import GetCategorySummaryUseCase
from app.application.use_cases.get_period_summary import GetPeriodSummaryUseCase
from app.application.use_cases.register_expense import RegisterExpenseUseCase
from app.application.use_cases.send_daily_summary import SendDailySummaryUseCase
from app.infrastructure.ai.gemini_extractor import GeminiExtractor
from app.infrastructure.persistence.firestore_expense_repository import (
    FirestoreExpenseRepository,
)
from app.infrastructure.persistence.firestore_user_repository import (
    FirestoreUserRepository,
)
from app.infrastructure.telegram.telegram_notifier import TelegramNotifier
from app.presentation.api.routes import build_router
from app.presentation.telegram.commands import BotCommands
from app.presentation.telegram.handlers import ExpenseHandlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def _require_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


def create_app() -> FastAPI:
    # ── Configuration ───────────────────────────────────────────────────────
    telegram_token = _require_env("TELEGRAM_TOKEN")
    gcp_project = _require_env("GCP_PROJECT_ID")
    scheduler_secret = os.environ.get("SCHEDULER_SECRET", "")

    # ── Infrastructure ───────────────────────────────────────────────────────
    db = firestore.AsyncClient(project=gcp_project)
    expense_repo = FirestoreExpenseRepository(db)
    user_repo = FirestoreUserRepository(db)
    extractor = GeminiExtractor(project_id=gcp_project)

    # ── Telegram Application ─────────────────────────────────────────────────
    ptb_app = Application.builder().token(telegram_token).build()
    notifier = TelegramNotifier(bot=ptb_app.bot)

    # ── Use Cases ────────────────────────────────────────────────────────────
    register_expense = RegisterExpenseUseCase(expense_repo, user_repo, extractor)
    get_period_summary = GetPeriodSummaryUseCase(expense_repo)
    get_category_summary = GetCategorySummaryUseCase(expense_repo)
    send_daily_summary = SendDailySummaryUseCase(expense_repo, user_repo, notifier)

    # ── Presentation — Telegram handlers ────────────────────────────────────
    handlers = ExpenseHandlers(register_expense)
    commands = BotCommands(user_repo, get_period_summary, get_category_summary)

    ptb_app.add_handler(CommandHandler("start", commands.start))
    ptb_app.add_handler(CommandHandler("hoy", commands.hoy))
    ptb_app.add_handler(CommandHandler("semana", commands.semana))
    ptb_app.add_handler(CommandHandler("mes", commands.mes))
    ptb_app.add_handler(CommandHandler("cat", commands.cat))
    ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_text))
    ptb_app.add_handler(MessageHandler(filters.PHOTO, handlers.handle_photo))
    ptb_app.add_handler(MessageHandler(filters.VOICE, handlers.handle_voice))
    ptb_app.add_handler(MessageHandler(filters.COMMAND, commands.unknown_command))

    # ── FastAPI ──────────────────────────────────────────────────────────────
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await ptb_app.initialize()
        logger.info("Bot inicializado. Webhook listo en /webhook")
        yield
        await ptb_app.shutdown()

    app = FastAPI(title="Asistente de Gastos", lifespan=lifespan)
    api_router = build_router(ptb_app, send_daily_summary, scheduler_secret)
    app.include_router(api_router)

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
