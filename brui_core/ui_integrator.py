import asyncio
from abc import ABC
import logging
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page

from brui_core.browser.browser_manager import BrowserManager

logger = logging.getLogger(__name__)

class UIIntegrator:
    def __init__(self):
        self.browser_manager = BrowserManager()
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.initialized = False

    async def initialize(self):
        await self.browser_manager.ensure_browser_launched()
        browser = await self.browser_manager.connect_browser()
        self.context = browser.contexts[0]
        self.page = await self.context.new_page()
        self.initialized = True
        logger.info("UIIntegrator initialized successfully")

    async def reopen_page(self):
        if not self.initialized:
            logger.error("UIIntegrator is not initialized. Call initialize() first.")
            raise RuntimeError("UIIntegrator is not initialized")

        try:
            if self.page:
                await self.page.close()
                logger.info("Closed existing page")

            self.page = await self.context.new_page()
            logger.info("Opened new page")
        except Exception as e:
            logger.error(f"Error while reopening page: {str(e)}")
            raise

    async def close(self, close_page=True, close_context=False, close_browser=False):
        try:
            if close_page and self.page:
                await self.page.close()
                self.page = None
                logger.info("Closed page")

            if close_context and self.context:
                await self.context.close()
                self.context = None
                logger.info("Closed context")

            if close_browser:
                await self.browser_manager.stop_browser()
                logger.info("Stopped browser")
            self.initialized = False
        except Exception as e:
            logger.error(f"Error while closing: {str(e)}")
            raise