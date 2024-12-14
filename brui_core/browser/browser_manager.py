import asyncio
import logging
from typing import Optional

from playwright.async_api import async_playwright
from playwright.async_api import Browser

from brui_core.browser.browser_launcher import (
    is_browser_opened_in_debug_mode,
    launch_browser,
    remote_debugging_port
)
from brui_core.singleton_meta import SingletonMeta

logger = logging.getLogger(__name__)

class BrowserManager(metaclass=SingletonMeta):
    def __init__(self):
        self.browser_launch_lock = asyncio.Lock()
        self.browser_launched = False
        self.playwright: Optional[async_playwright] = None
        self.browser: Optional[Browser] = None

    async def is_browser_running(self) -> bool:
        try:
            return await is_browser_opened_in_debug_mode()
        except Exception as e:
            logger.error(f"Error checking if browser is running: {str(e)}")
            return False

    async def reset_browser_state(self):
        """Reset the browser state and clean up existing connections"""
        try:
            if self.browser is not None:
                await self.browser.close()
                self.browser = None
            if self.playwright is not None:
                await self.playwright.stop()
                self.playwright = None
            self.browser_launched = False
        except Exception as e:
            logger.error(f"Error resetting browser state: {str(e)}")
            # Still reset the state even if cleanup fails
            self.browser = None
            self.playwright = None
            self.browser_launched = False

    async def ensure_browser_launched(self):
        """Ensure browser is launched, resetting state if necessary"""
        if not await self.is_browser_running():
            async with self.browser_launch_lock:
                if not await self.is_browser_running():  # Double-check after acquiring lock
                    # Reset state before launching new browser
                    await self.reset_browser_state()
                    try:
                        await launch_browser()
                        self.browser_launched = True
                    except Exception as e:
                        logger.error(f"Failed to launch browser: {str(e)}")
                        raise

    async def connect_browser(self) -> Browser:
        """Connect to the browser, launching it if necessary"""
        await self.ensure_browser_launched()
        
        if self.browser is None:
            self.playwright = await async_playwright().start()
            endpoint_url = f"http://localhost:{remote_debugging_port}"
            self.browser = await self.playwright.chromium.connect_over_cdp(endpoint_url)
        return self.browser

    async def stop_browser(self):
        """Stop the browser and clean up resources"""
        await self.reset_browser_state()