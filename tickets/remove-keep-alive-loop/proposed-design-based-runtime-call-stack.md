# Proposed-Design-Based Runtime Call Stack (`v1`)

## Coverage Summary
| use_case_id | Primary | Fallback | Error |
|---|---|---|---|
| UC-1 | Yes | N/A | Yes |
| UC-2 | Yes | N/A | Yes |
| UC-3 | Yes | N/A | Yes |

## UC-1: Initialize and navigate without background race
1. `brui_core/ui_integrator.py:UIIntegrator.initialize()`
2. `brui_core/browser/browser_manager.py:BrowserManager.ensure_browser_launched()` `await`
3. `brui_core/browser/browser_manager.py:BrowserManager.connect_browser()` `await`
4. `brui_core/browser/browser_manager.py:BrowserManager.get_browser_context(...)` `await`
5. `BrowserContext.new_page()` `await` -> assign `self.page` (state mutation)
6. Caller executes `Page.goto(...)` directly.
7. No background task can close/reopen page during navigation.

Error branch:
1. Browser/context/page initialization error surfaces directly from explicit call stack.

## UC-2: Explicit page reopen
1. `brui_core/ui_integrator.py:UIIntegrator.reopen_page()`
2. Validate `self.initialized` else raise runtime error.
3. If existing page open, close existing page explicitly.
4. `BrowserContext.new_page()` `await` -> replace `self.page` (state mutation).
5. Caller continues operations on new page.

Error branch:
1. If context invalid or page creation fails, exception is raised directly.

## UC-3: Explicit close options
1. `brui_core/ui_integrator.py:UIIntegrator.close(close_page, close_context, close_browser)`
2. If `close_page` and page exists -> close page, clear `self.page` (state mutation).
3. If `close_context` and context exists -> close context, clear `self.context` (state mutation).
4. If `close_browser` -> `BrowserManager.stop_browser()` `await`.
5. Set `self.initialized=False` (state mutation).

Error branch:
1. Any close operation failure is raised directly (no background recovery path).
