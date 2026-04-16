# Implementation

## Scope Classification

- Classification: `Small`

## Solution Sketch

- Keep the Stage 1 `UIIntegrator` recovery path that wraps `context.new_page()` with a timeout and retries once on a fresh CDP connection.
- Harden `BrowserManager.reset_browser_state()` so it clears cached `browser` and `playwright` references before attempting cleanup and bounds stale `browser.close()` / `playwright.stop()` with timeouts.
- Add a unit regression test proving stale cleanup operations cannot wedge the reset path.
- Publish the framework change as `brui_core 2.0.2` so downstream consumers can drop local workarounds and depend on the framework fix directly.

## Planned Validation

- `uv run pytest tests/test_browser_manager_unit.py tests/test_ui_integrator_unit.py -q`
- `uv run pytest tests/integration/browser/test_browser_manager.py -q`
- `uv run pytest -q`
- `uv build`

## Execution Summary

- Retained the Stage 1 UI recovery logic from `2.0.1` and added the missing reset hardening in `brui_core/browser/browser_manager.py`.
- Added `tests/test_browser_manager_unit.py` to lock in the non-blocking reset behavior.
- Bumped the package version from `2.0.1` to `2.0.2`.

## Validation Results

- `uv run pytest tests/test_browser_manager_unit.py tests/test_ui_integrator_unit.py -q` -> `6 passed`
- `uv run pytest tests/integration/browser/test_browser_manager.py -q` -> `8 passed`
- `uv run pytest -q` -> `20 passed in 112.67s`
- `uv build` -> built `dist/brui_core-2.0.2.tar.gz` and `dist/brui_core-2.0.2-py3-none-any.whl`
