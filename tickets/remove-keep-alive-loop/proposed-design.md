# Proposed Design - Remove Keep-Alive Loop (`v1`)

## Current-State Summary (As-Is)
- `UIIntegrator` owns background keep-alive task fields and methods:
  - `_keep_alive_task`,
  - `_keep_alive_interval`,
  - `_keep_alive()`,
  - `start_keep_alive()`,
  - `_stop_keep_alive()`.
- Keep-alive periodically evaluates page JS and can call `reopen_page()` from background context.
- This can race with active navigation and close the page unexpectedly.

## Target-State Summary (To-Be)
- `UIIntegrator` has no background keep-alive loop.
- Page lifecycle is explicit:
  - `initialize()` creates page,
  - callers operate on page,
  - `reopen_page()` is explicit recovery utility,
  - `close()` handles resource shutdown only.
- No automatic background reopen behavior.

## Change Inventory
| Type | File | Change |
|---|---|---|
| Modify | `brui_core/ui_integrator.py` | Remove keep-alive fields and methods; simplify lifecycle to explicit operations only. |
| Add | `tests/test_ui_integrator_unit.py` | Add unit tests for initialize/reopen/close behavior using fakes. |
| Modify | `README.md` | Update docs to reflect explicit lifecycle and no keep-alive loop. |
| Modify | `pyproject.toml` | Bump package version for release. |
| Remove | `UIIntegrator.start_keep_alive` API | Remove obsolete API surface and behavior. |

## Module Responsibilities and APIs
### `brui_core/ui_integrator.py`
- Responsibility: explicit UI lifecycle manager over browser/context/page.
- Public APIs after change:
  - `initialize()`,
  - `reopen_page()`,
  - `close(...)`.
- Removed API:
  - `start_keep_alive()`.

## Naming Decisions
- Keep `UIIntegrator` name unchanged; responsibility remains integration lifecycle.
- Keep `reopen_page` unchanged; behavior remains explicit recovery.
- Remove `keep_alive` naming entirely from API to avoid semantic drift.

## Naming Drift Check
- `UIIntegrator`: still accurate and cohesive with explicit lifecycle ownership.
- No split/rename needed.

## Dependency Flow
- `UIIntegrator -> BrowserManager -> Playwright BrowserContext/Page`.
- No new dependencies introduced.
- Removes background task coupling to page operations.

## Cleanup / Decommission
- Delete keep-alive code paths and task management logic.
- Remove any documentation implying background health loop exists.

## Error Handling Expectations
- Errors in explicit operations (`initialize`, `reopen_page`, `close`) are surfaced directly.
- No hidden background retries or implicit page replacement.

## Use-Case Coverage Matrix
| use_case_id | Description | Primary | Fallback | Error | Runtime Sections |
|---|---|---|---|---|---|
| UC-1 | Initialize and navigate without background race | Yes | N/A | Yes | `UC-1` |
| UC-2 | Explicit page reopen | Yes | N/A | Yes | `UC-2` |
| UC-3 | Explicit close options | Yes | N/A | Yes | `UC-3` |
