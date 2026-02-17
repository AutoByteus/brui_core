# UIIntegrator Lifecycle

## Summary
`UIIntegrator` is an explicit lifecycle wrapper over browser/context/page:

1. `initialize()` creates a page.
2. Caller performs page operations.
3. `reopen_page()` is explicit recovery when a fresh page is needed.
4. `close(...)` shuts down selected resources.

## No Keep-Alive Background Loop
`UIIntegrator` does not run a background keep-alive page probe. This prevents background task interference with active navigations and keeps page ownership deterministic.

## Migration Impact
- Removed API: `start_keep_alive()`
- Recommended usage: call `reopen_page()` explicitly when page recreation is required.
