import asyncio
import logging

# Optional: see info logs from your UIIntegrator/BrowserManager
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

from brui_core.ui_integrator import UIIntegrator  # adjust import path if needed

async def main():
    ui = UIIntegrator()

    # Initialize (this will ensure the browser is launched, connect over CDP, create a context & page)
    await ui.initialize()

    # Open Google
    await ui.page.goto("https://aistudio.google.com/prompts/new_chat", wait_until="load")

    # Print title so you can see success in the console
    title = await ui.page.title()
    print("Title:", title)

    # (Optional) take a screenshot to verify visually
    try:
        await ui.page.screenshot(path="ui_integrator_google.png")
        print("Saved ui_integrator_google.png")
    except Exception as e:
        print("Screenshot skipped:", e)

    # Clean shutdown (keeps browser running if you want; set close_browser=True to kill it)
    await ui.close(close_page=True, close_context=False, close_browser=False)

if __name__ == "__main__":
    asyncio.run(main())
