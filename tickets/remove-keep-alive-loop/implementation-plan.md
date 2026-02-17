# Implementation Plan - Remove Keep-Alive Loop

## Scope
Remove `UIIntegrator` keep-alive background loop and related APIs. Keep lifecycle explicit and deterministic.

## Requirement Traceability
| Requirement | Design Section | Use Case | Tasks | Verification |
|---|---|---|---|---|
| AC-1 remove loop behavior | Target-State | UC-1 | Delete keep-alive task logic from `ui_integrator.py` | unit tests + direct repro |
| AC-2 remove API surface | Change Inventory | UC-1/UC-3 | Remove `start_keep_alive` and keep-alive internals | static checks + tests |
| AC-3 deterministic navigation | Runtime UC-1 | UC-1 | verify `initialize -> goto` path without background reopen | direct repro |
| AC-4 explicit reopen | Runtime UC-2 | UC-2 | keep/review `reopen_page` behavior | unit tests |
| AC-5 lifecycle tests | Change Inventory | UC-1..UC-3 | add unit tests with fakes | `tests/test_ui_integrator_unit.py` |
| AC-6 docs update | Cleanup | UC-1..UC-3 | update README and docs notes | docs diff review |
| AC-7 release prep | Change Inventory | N/A | bump package version | pyproject diff |

## Task Sequence (Bottom-Up)
1. Refactor `brui_core/ui_integrator.py` to remove keep-alive code paths.
2. Add unit tests for initialize/reopen/close lifecycle.
3. Update README lifecycle guidance.
4. Bump package version.
5. Run unit tests and targeted real repro.

## Verification Strategy
- Unit tests:
  - `UIIntegrator.initialize()` builds context/page state.
  - `UIIntegrator.reopen_page()` replaces page deterministically.
  - `UIIntegrator.close()` closes configured resources.
- Integration/repro:
  - direct `UIIntegrator` script against container debug endpoint:
    - with current code path, `initialize -> goto google search` succeeds.
- E2E feasibility:
  - feasible for targeted repro via container debug endpoint (`localhost:9227` in current environment).
  - full `brui_core` integration suite in this host is partially blocked by local env assumptions and missing optional test deps in selected runner.

## Cleanup / Decommission
- Remove keep-alive helpers and fields.
- Remove keep-alive API from public class surface.
- No compatibility wrappers.

## Risks
- Downstream callers may still call removed API.
- Mitigation: update dependent MCP immediately after release or vendor local core first.
