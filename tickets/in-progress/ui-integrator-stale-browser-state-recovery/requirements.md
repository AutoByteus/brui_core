# Requirements

- Ticket: `ui-integrator-stale-browser-state-recovery`
- Status: `Design-ready`

## Problem

Sequential `UIIntegrator` users in the same Python process can reuse a stale shared `BrowserManager` connection after page-only cleanup. In real usage this can wedge a follow-on `initialize()` call while creating the next page.

## Requirements

- `R-001`: `brui_core` must tolerate sequential `UIIntegrator.initialize() -> close(close_page=True, close_context=False, close_browser=False) -> initialize()` usage in the same process without hanging.
- `R-002`: The fix must be covered by a durable automated regression test in `brui_core`.
- `R-003`: `brui_core` package version must be incremented for release consumption by downstream repos.
- `R-004`: The consumer Gemini audio ticket must update its pinned `brui-core` version after the library fix is validated.

## Notes

- Current downstream evidence comes from the Gemini audio server E2E flow, where one browser-backed request succeeds and a follow-on request in the same pytest process can wedge while creating the next page.
- `brui_core` already exposes explicit lifecycle APIs and recovery helpers, so the intended fix should preserve that model rather than introducing hidden keep-alive or broad process killing.

## Acceptance Criteria

- `AC-001`: A regression test reproduces the sequential page-only cleanup lifecycle and passes after the fix.
- `AC-002`: `brui_core` test suite covering the changed lifecycle behavior passes locally.
- `AC-003`: `pyproject.toml` in `brui_core` reflects the next release version.
- `AC-004`: `autobyteus_rpa_llm` and `autobyteus_rpa_llm_server` pin the released `brui-core` version instead of `2.0.0`.
