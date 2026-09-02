import json
from uuid import uuid4

import pytest

from app.assistant.ask import TelegramActor
from app.assistant.gateway import ToolResult
from app.assistant.telegram_handler import (
    OwnerAssistantTelegramHandler,
    build_owner_assistant_router,
)
from app.core.config import Settings, validate_assistant_settings


class FakeAdapter:
    def __init__(self):
        self.calls = []

    async def handle(self, actor, request):
        self.calls.append((actor, request))
        return ToolResult(request_id=uuid4(), data={"status": "read_only"})


@pytest.mark.asyncio
async def test_disabled_handler_is_a_noop_and_does_not_call_adapter():
    adapter = FakeAdapter()
    handler = OwnerAssistantTelegramHandler(adapter, enabled=False)

    assert await handler.handle_text(TelegramActor(111), "not-json") == []
    assert adapter.calls == []
    assert build_owner_assistant_router(adapter, enabled=False) is None


@pytest.mark.asyncio
async def test_enabled_handler_forwards_json_and_trusted_actor_only():
    adapter = FakeAdapter()
    handler = OwnerAssistantTelegramHandler(adapter, enabled=True)

    chunks = await handler.handle_text(
        TelegramActor(111),
        json.dumps(
            {
                "session_id": "owner-session",
                "query": {
                    "intent": "list_houses",
                    "arguments": {"include_inactive": False},
                },
            }
        ),
    )

    assert len(adapter.calls) == 1
    actor, request = adapter.calls[0]
    assert actor == TelegramActor(111)
    assert request["session_id"] == "owner-session"
    assert json.loads("".join(chunks))["ok"] is True
    assert build_owner_assistant_router(adapter, enabled=True) is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "command_args",
    [
        None,
        "plain text",
        "[]",
    ],
)
async def test_handler_accepts_structured_json_only(command_args):
    adapter = FakeAdapter()
    handler = OwnerAssistantTelegramHandler(adapter, enabled=True)

    result = await handler.handle_text(TelegramActor(111), command_args)

    assert result
    assert adapter.calls == []


def test_assistant_transport_defaults_off_and_is_blocked_in_production():
    settings = Settings(telegram_bot_token="test-token", telegram_chat_id=1)

    assert settings.assistant_telegram_enabled is False
    with pytest.raises(RuntimeError):
        validate_assistant_settings("production", True)
