# Investigation Notes

## Scope Triage

- Scope: `Small`
- Reason:
  - the defect is bounded to the shared browser lifecycle in `UIIntegrator` / `BrowserManager`
  - downstream Gemini audio code only exposed the issue; it is not the owner of the stale connection behavior

## Findings

- `BrowserManager` is a singleton and caches `self.browser` plus `self.playwright`.
- `connect_browser()` returns the cached `self.browser` whenever it exists and `reconnect=False`.
- `UIIntegrator.close()` defaults to closing only the page, leaving the cached browser connection alive.
- `UIIntegrator.initialize()` then reuses that cached browser, retrieves the first context, and calls `context.new_page()`.
- Downstream logs show the second sequential request reaches `Creating new page...` and then wedges before `New page created successfully`.
- Existing `brui_core` tests cover launch/reconnect/stop and basic `UIIntegrator` lifecycle, but they do not cover sequential `initialize -> close(page-only) -> initialize` usage with the shared singleton manager.

## Risk

- This is a framework-level robustness gap because callers using the documented explicit lifecycle can still inherit a stale cached browser connection across sequential runs in one process.
