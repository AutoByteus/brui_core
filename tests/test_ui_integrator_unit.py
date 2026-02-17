from __future__ import annotations

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


class FakeBrowserManager:
    def __init__(self) -> None:
        self.context = FakeContext()
        self.stopped = False
        self.launched = False
        self.connected = False

    async def ensure_browser_launched(self) -> None:
        self.launched = True

    async def connect_browser(self):
        self.connected = True
        return object()

    async def get_browser_context(self, _browser) -> FakeContext:
        return self.context

    async def stop_browser(self) -> None:
        self.stopped = True


@pytest.fixture
def fake_integrator(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(ui_module, "BrowserManager", FakeBrowserManager)
    integrator = ui_module.UIIntegrator()
    return integrator


@pytest.mark.anyio
async def test_initialize_creates_context_and_page(fake_integrator):
    await fake_integrator.initialize()

    assert fake_integrator.initialized is True
    assert fake_integrator.context is not None
    assert fake_integrator.page is not None
    assert fake_integrator.page.url == "about:blank"


@pytest.mark.anyio
async def test_reopen_page_replaces_existing_page(fake_integrator):
    await fake_integrator.initialize()
    old_page = fake_integrator.page
    assert old_page is not None

    await fake_integrator.reopen_page()

    assert old_page.is_closed() is True
    assert fake_integrator.page is not None
    assert fake_integrator.page is not old_page


@pytest.mark.anyio
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


@pytest.mark.anyio
async def test_reopen_page_requires_initialized(fake_integrator):
    with pytest.raises(RuntimeError, match="UIIntegrator is not initialized"):
        await fake_integrator.reopen_page()
