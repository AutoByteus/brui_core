import asyncio
from playwright.async_api import async_playwright

async def main():
    playwright = await async_playwright().start()
    endpoint_url = "http://localhost:9222"  # or 9223 if socat-forwarded
    browser = await playwright.chromium.connect_over_cdp(endpoint_url)

    # Use the first context or create one
    context = browser.contexts[0]
    page = await context.new_page()

    await page.goto("https://www.google.com")
    print("Title:", await page.title())

    # cleanup
    await browser.close()
    await playwright.stop()

asyncio.run(main())
