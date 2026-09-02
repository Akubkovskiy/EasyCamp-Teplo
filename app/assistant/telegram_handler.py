"""Disabled-by-default Telegram transport for structured owner reads.

This module defines a narrow aiogram adapter but does not register it in the
application dispatcher. The caller must explicitly build and register the
router behind the assistant feature flag in a later rollout.
"""

from __future__ import annotations

import json
from collections.abc import Mapping

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message

from app.assistant.ask import TelegramActor, TelegramTrustedAskAdapter

TELEGRAM_MESSAGE_LIMIT = 4096
DEFAULT_RESPONSE_LIMIT = TELEGRAM_MESSAGE_LIMIT - 128


class OwnerAssistantTelegramHandler:
    """Translate one ``/ask`` command into the trusted adapter call."""

    def __init__(
        self,
        adapter: TelegramTrustedAskAdapter,
        *,
        enabled: bool = False,
        response_limit: int = DEFAULT_RESPONSE_LIMIT,
    ) -> None:
        if response_limit <= 0 or response_limit >= TELEGRAM_MESSAGE_LIMIT:
            raise ValueError("response_limit must fit inside a Telegram message")
        self._adapter = adapter
        self._enabled = enabled
        self._response_limit = response_limit

    async def handle_text(self, actor: TelegramActor, command_args: str | None) -> list[str]:
        """Handle JSON only; natural-language planning is deliberately absent."""
        if not self._enabled:
            return []
        if not isinstance(command_args, str) or not command_args.strip():
            return ["Формат: /ask {JSON structured-запроса}"]
        if len(command_args) > self._response_limit:
            return ["Structured-запрос слишком большой."]
        try:
            payload = json.loads(command_args)
        except json.JSONDecodeError:
            return ["Не удалось разобрать JSON structured-запрос."]
        if not isinstance(payload, Mapping):
            return ["Structured-запрос должен быть JSON-объектом."]

        result = await self._adapter.handle(actor, payload)
        return _chunk_text(
            json.dumps(result.to_dict(), ensure_ascii=False, separators=(",", ":")),
            self._response_limit,
        )


def build_owner_assistant_router(
    adapter: TelegramTrustedAskAdapter,
    *,
    enabled: bool = False,
    response_limit: int = DEFAULT_RESPONSE_LIMIT,
) -> Router | None:
    """Build the owner-only router only when explicitly enabled.

    The function is intentionally not called from ``app.main``. A disabled
    feature returns ``None`` and therefore cannot add a no-op command handler
    to the production dispatcher by accident.
    """
    if not enabled:
        return None

    handler = OwnerAssistantTelegramHandler(
        adapter,
        enabled=True,
        response_limit=response_limit,
    )
    router = Router(name="assistant_owner")

    @router.message(Command("ask"))
    async def assistant_ask_command(message: Message, command: CommandObject) -> None:
        if message.from_user is None:
            return
        actor = TelegramActor(message.from_user.id)
        for chunk in await handler.handle_text(actor, command.args):
            await message.answer(chunk)

    return router


def _chunk_text(value: str, limit: int) -> list[str]:
    return [value[start : start + limit] for start in range(0, len(value), limit)] or [""]
