# UIIntegrator Lifecycle

## Summary
`UIIntegrator` is an explicit lifecycle wrapper over browser/context/page:

1. `initialize()` creates a page.
2. Caller performs page operations.
3. `reopen_page()` is explicit recovery when a fresh page is needed.
4. `close(...)` shuts down selected resources.

If the cached browser connection has gone stale and page creation fails during `initialize()` or `reopen_page()`, `UIIntegrator` resets the shared browser connection state and retries once with a fresh CDP session.

## No Keep-Alive Background Loop
`UIIntegrator` does not run a background keep-alive page probe. This prevents background task interference with active navigations and keeps page ownership deterministic.

## Migration Impact
- Removed API: `start_keep_alive()`
- Recommended usage: call `reopen_page()` explicitly when page recreation is required.
