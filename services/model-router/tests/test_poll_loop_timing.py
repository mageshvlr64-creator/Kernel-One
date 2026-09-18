"""Tests for the health-poll loop's timing, using injectable seams.

ModelRegistry takes a ``sleep`` callable (default ``asyncio.sleep``). With a
fake sleep that yields one event-loop tick and a stub HTTP client that
records requests, the tests verify the loop's real behavior — the configured
interval is honored, every model is checked each round, results are written,
and stopping cancels the loop — without any real delay.
"""

from __future__ import annotations

import asyncio

import pytest

from app.config import ModelRouterConfig
from app.models import Capability, DataClassification, Model, Provider
from app.registry import ModelRegistry


class FakeSleep:
    """Records every sleep request, then yields one event-loop tick.

    The yield is essential: without a scheduling point, a no-op fake turns
    the poll loop into a synchronous hot spin that starves the test's own
    awaits (this hung the first version of these tests).
    """

    def __init__(self) -> None:
        self.calls: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)
        await asyncio.sleep(0)


class _Resp:
    status_code = 200


class StubHealthClient:
    """Async-client double: every health GET succeeds instantly."""

    def __init__(self) -> None:
        self.requests = 0

    async def get(self, url: str):
        self.requests += 1
        return _Resp()

    async def aclose(self) -> None:
        pass


def _make_model(model_id: str) -> Model:
    return Model(
        id=model_id,
        display_name=f"Test {model_id}",
        provider=Provider.VLLM,
        total_parameters_billions=7.0,
        context_window=32768,
        capabilities=[Capability.CODING],
        max_classification=DataClassification.CONFIDENTIAL,
        is_available=True,
    )


def _make_registry(sleep: FakeSleep, interval: float = 30.0) -> ModelRegistry:
    config = ModelRouterConfig(
        model_registry_path="", health_poll_interval_seconds=interval
    )
    return ModelRegistry(config, sleep=sleep)


@pytest.mark.asyncio
async def test_loop_sleeps_with_configured_interval():
    sleep = FakeSleep()
    registry = _make_registry(sleep, interval=30.0)
    await registry.start_health_polling()
    await asyncio.sleep(0)  # the loop records its first sleep, then yields
    try:
        assert sleep.calls, "loop never slept"
        assert all(c == 30.0 for c in sleep.calls)
    finally:
        await registry.stop_health_polling()


@pytest.mark.asyncio
async def test_each_round_checks_every_registered_model():
    sleep = FakeSleep()
    client = StubHealthClient()
    registry = _make_registry(sleep)
    registry._models = {"a": _make_model("a"), "b": _make_model("b")}
    await registry.start_health_polling()
    registry._http_client = client  # swap in the stub before the first tick
    try:
        await asyncio.sleep(0)  # round 1's sleep comes first
        assert len(sleep.calls) == 1
        assert registry.get_health("a") is None  # checks happen after the sleep
        for _ in range(10):  # bounded wait: round 1's checks + round 2's sleep
            await asyncio.sleep(0)
            if len(sleep.calls) >= 2:
                break
        assert len(sleep.calls) == 2  # exactly two rounds within bounded ticks
        assert client.requests == 2  # every registered model checked per round
        assert registry.get_health("a").is_healthy is True
        assert registry.get_health("b").is_healthy is True
    finally:
        await registry.stop_health_polling()


@pytest.mark.asyncio
async def test_stop_cancels_the_loop():
    sleep = FakeSleep()
    registry = _make_registry(sleep)
    await registry.start_health_polling()
    await asyncio.sleep(0)
    try:
        assert len(sleep.calls) == 1
    finally:
        await registry.stop_health_polling()
    assert registry._poll_task is None
    for _ in range(5):
        await asyncio.sleep(0)
    assert len(sleep.calls) == 1  # cancelled loop no longer advances
