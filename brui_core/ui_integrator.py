import asyncio
import logging
from typing import Optional

from playwright.async_api import BrowserContext, Page

from brui_core.browser.browser_manager import BrowserManager

logger = logging.getLogger(__name__)

class UIIntegrator:
    page_creation_timeout_seconds = 10.0

    def __init__(self):
        self.browser_manager = BrowserManager()
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.initialized = False

    async def _connect_browser_context(self, *, reconnect: bool = False) -> BrowserContext:
        logger.info("Connecting to browser...")
        browser = await self.browser_manager.connect_browser(reconnect=reconnect)
        logger.info("Successfully connected to browser")

        logger.info("Accessing browser context...")
        self.context = await self.browser_manager.get_browser_context(browser)
        logger.info(f"Successfully accessed browser context. Pages in context: {len(self.context.pages)}")
        return self.context

    async def _create_page(self) -> Page:
        if self.context is None:
            raise RuntimeError("Browser context is not initialized")
        return await asyncio.wait_for(
            self.context.new_page(),
            timeout=self.page_creation_timeout_seconds,
        )

    async def _create_page_with_recovery(self) -> Page:
        logger.info("Creating new page...")
        try:
            page = await self._create_page()
        except Exception as error:
            logger.warning(
                "Initial page creation failed. Resetting browser state and retrying once: %s",
                error,
            )
            await self.browser_manager.reset_browser_state()
            await self.browser_manager.ensure_browser_launched()
            await self._connect_browser_context(reconnect=True)
            page = await self._create_page()

        logger.info(f"New page created successfully. URL: {page.url}")
        return page

    async def initialize(self):
        """Initialize the browser and create a new page."""
        logger.info("Starting UIIntegrator initialization")
        
        logger.info("Ensuring browser is launched...")
        await self.browser_manager.ensure_browser_launched()
        logger.info("Browser launch check completed successfully")
        
        try:
            await self._connect_browser_context()
        except Exception as e:
            logger.error(f"Failed to access browser context: {str(e)}")
            raise

        try:
            self.page = await self._create_page_with_recovery()
        except Exception as e:
            logger.error(f"Failed to create new page: {str(e)}")
            raise
        
        self.initialized = True
        logger.info("UIIntegrator initialized successfully")

    async def reopen_page(self):
        """Reopen the page if it's closed."""
        if not self.initialized:
            logger.error("UIIntegrator is not initialized. Call initialize() first.")
            raise RuntimeError("UIIntegrator is not initialized")

        try:
            if self.page and not self.page.is_closed():
                await self.page.close()
                logger.info("Closed existing page")

            self.page = await self._create_page_with_recovery()
            logger.info("Opened new page")
        except Exception as e:
            logger.error(f"Error while reopening page: {str(e)}")
            raise

    async def close(self, close_page=True, close_context=False, close_browser=False):
        """Close the integrator and optionally its components."""
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
