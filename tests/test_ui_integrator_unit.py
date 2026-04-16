from __future__ import annotations

import asyncio

import pytest

import brui_core.ui_integrator as ui_module


class FakePage:
    def __init__(self, url: str = "about:blank") -> None:
        self.url = url
        self._closed = False

    def is_closed(self) -> bool:
        return self._closed

    async def close(self) -> None:
        self._closed = True


class FakeContext:
    def __init__(self) -> None:
        self.pages: list[FakePage] = []
        self.closed = False

    async def new_page(self) -> FakePage:
        page = FakePage()
        self.pages.append(page)
        return page

    async def close(self) -> None:
        self.closed = True


class SlowContext(FakeContext):
    async def new_page(self) -> FakePage:
        await asyncio.sleep(1)
        return await super().new_page()


class FakeBrowserManager:
    def __init__(self) -> None:
        self.contexts = [FakeContext()]
        self.stopped = False
        self.launched = False
        self.connect_calls: list[bool] = []
        self.reset_calls = 0

    async def ensure_browser_launched(self) -> None:
        self.launched = True

    async def connect_browser(self, reconnect: bool = False):
        self.connect_calls.append(reconnect)
        return len(self.connect_calls) - 1

    async def get_browser_context(self, browser_index) -> FakeContext:
        return self.contexts[browser_index]

    async def reset_browser_state(self) -> None:
        self.reset_calls += 1

    async def stop_browser(self) -> None:
        self.stopped = True


@pytest.fixture
def fake_integrator(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(ui_module, "BrowserManager", FakeBrowserManager)
    integrator = ui_module.UIIntegrator()
    return integrator


@pytest.mark.asyncio
async def test_initialize_creates_context_and_page(fake_integrator):
    await fake_integrator.initialize()

    assert fake_integrator.initialized is True
    assert fake_integrator.context is not None
    assert fake_integrator.page is not None
    assert fake_integrator.page.url == "about:blank"


@pytest.mark.asyncio
async def test_reopen_page_replaces_existing_page(fake_integrator):
    await fake_integrator.initialize()
    old_page = fake_integrator.page
    assert old_page is not None

    await fake_integrator.reopen_page()

    assert old_page.is_closed() is True
    assert fake_integrator.page is not None
    assert fake_integrator.page is not old_page


@pytest.mark.asyncio
async def test_close_respects_close_flags(fake_integrator):
    await fake_integrator.initialize()
    manager = fake_integrator.browser_manager
    context = fake_integrator.context

    await fake_integrator.close(close_page=True, close_context=True, close_browser=True)

    assert fake_integrator.initialized is False
    assert fake_integrator.page is None
    assert fake_integrator.context is None
    assert context is not None and context.closed is True
    assert manager.stopped is True


@pytest.mark.asyncio
async def test_reopen_page_requires_initialized(fake_integrator):
    with pytest.raises(RuntimeError, match="UIIntegrator is not initialized"):
        await fake_integrator.reopen_page()


@pytest.mark.asyncio
async def test_initialize_recovers_after_page_creation_timeout(fake_integrator):
    fake_integrator.browser_manager.contexts = [SlowContext(), FakeContext()]
    fake_integrator.page_creation_timeout_seconds = 0.01

    await fake_integrator.initialize()

    assert fake_integrator.initialized is True
    assert fake_integrator.page is not None
    assert fake_integrator.browser_manager.connect_calls == [False, True]
    assert fake_integrator.browser_manager.reset_calls == 1
