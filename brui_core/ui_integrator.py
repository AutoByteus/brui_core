import logging
from typing import Optional

from playwright.async_api import BrowserContext, Page

from brui_core.browser.browser_manager import BrowserManager

logger = logging.getLogger(__name__)

class UIIntegrator:
    def __init__(self):
        self.browser_manager = BrowserManager()
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.initialized = False

    async def initialize(self):
        """Initialize the browser and create a new page."""
        logger.info("Starting UIIntegrator initialization")
        
        logger.info("Ensuring browser is launched...")
        await self.browser_manager.ensure_browser_launched()
        logger.info("Browser launch check completed successfully")
        
        logger.info("Connecting to browser...")
        browser = await self.browser_manager.connect_browser()
        logger.info("Successfully connected to browser")
        
        logger.info("Accessing browser context...")
        try:
            # Use the get_browser_context method instead of direct access
            self.context = await self.browser_manager.get_browser_context(browser)
            logger.info(f"Successfully accessed browser context. Pages in context: {len(self.context.pages)}")
        except Exception as e:
            logger.error(f"Failed to access browser context: {str(e)}")
            raise
        
        logger.info("Creating new page...")
        try:
            self.page = await self.context.new_page()
            logger.info(f"New page created successfully. URL: {self.page.url}")
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

            self.page = await self.context.new_page()
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
