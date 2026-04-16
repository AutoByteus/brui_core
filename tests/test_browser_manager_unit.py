from __future__ import annotations

import asyncio

import pytest

from brui_core.browser.browser_manager import BrowserManager


class SlowBrowser:
    async def close(self) -> None:
        await asyncio.sleep(1)


class SlowPlaywright:
    async def stop(self) -> None:
        await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_reset_browser_state_times_out_stale_close_operations():
    BrowserManager._instances = {}
    manager = BrowserManager()
    manager.browser = SlowBrowser()
    manager.playwright = SlowPlaywright()
    manager.reset_timeout_seconds = 0.01

    await asyncio.wait_for(manager.reset_browser_state(), timeout=0.2)

    assert manager.browser is None
    assert manager.playwright is None
