# API / E2E Testing

## Validation Scope

- Validate the new reset hardening with the targeted unit regression.
- Revalidate UIIntegrator lifecycle recovery against real Chrome.
- Re-run the full repository suite before release.

## Executed Commands

- `uv run pytest tests/test_browser_manager_unit.py tests/test_ui_integrator_unit.py -q`
- `uv run pytest tests/integration/browser/test_browser_manager.py -q`
- `uv run pytest -q`

## Results

- `uv run pytest tests/test_browser_manager_unit.py tests/test_ui_integrator_unit.py -q` -> `6 passed`
- `uv run pytest tests/integration/browser/test_browser_manager.py -q` -> `8 passed`
- `uv run pytest -q` -> `20 passed in 112.67s`

## Acceptance Coverage

- Sequential `UIIntegrator.initialize()` after page-only cleanup still recovers.
- Stale `browser.close()` / `playwright.stop()` calls do not block reset indefinitely.
- Full repo regression suite stays green on the release candidate.
