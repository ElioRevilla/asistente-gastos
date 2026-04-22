from __future__ import annotations

import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from telegram import Update

from app.application.use_cases.send_daily_summary import SendDailySummaryUseCase

logger = logging.getLogger(__name__)

router = APIRouter()


def _verify_scheduler_secret(
    x_scheduler_secret: str | None = Header(default=None),
    scheduler_secret: str = "",
) -> None:
    """Simple HMAC-based protection for the scheduler endpoint."""
    if not scheduler_secret:
        return  # secret not configured — allow (dev mode)
    if not x_scheduler_secret:
        raise HTTPException(status_code=401, detail="Missing X-Scheduler-Secret header")
    if not hmac.compare_digest(x_scheduler_secret, scheduler_secret):
        raise HTTPException(status_code=403, detail="Invalid scheduler secret")


def build_router(
    ptb_application,  # telegram.ext.Application
    send_daily_summary: SendDailySummaryUseCase,
    scheduler_secret: str = "",
) -> APIRouter:

    @router.post("/webhook")
    async def webhook(request: Request) -> dict:
        data = await request.json()
        update = Update.de_json(data, ptb_application.bot)
        await ptb_application.process_update(update)
        return {"ok": True}

    @router.post("/scheduler/daily-summary")
    async def daily_summary(
        x_scheduler_secret: str | None = Header(default=None),
    ) -> dict:
        if scheduler_secret:
            if not x_scheduler_secret:
                raise HTTPException(status_code=401, detail="Missing X-Scheduler-Secret")
            if not hmac.compare_digest(x_scheduler_secret, scheduler_secret):
                raise HTTPException(status_code=403, detail="Invalid secret")

        sent = await send_daily_summary.execute()
        logger.info("Daily summary sent to %d users", sent)
        return {"ok": True, "sent": sent}

    return router
