# Future-State Runtime Call Stack

1. Caller creates `UIIntegrator()`.
2. `UIIntegrator.initialize()` calls `BrowserManager.ensure_browser_launched()`.
3. `UIIntegrator.initialize()` calls `BrowserManager.connect_browser()`.
4. `BrowserManager.connect_browser()` returns a healthy browser connection or reconnects when cached state was cleared.
5. `UIIntegrator.initialize()` gets the browser context and creates a page with `context.new_page()`.
6. Caller performs browser work.
7. Caller invokes `UIIntegrator.close(close_page=True, close_context=False, close_browser=False)`.
8. `UIIntegrator.close()` closes the page and clears stale shared browser-manager connection state so a later `initialize()` starts from a fresh CDP session instead of reusing an unhealthy cached handle.
