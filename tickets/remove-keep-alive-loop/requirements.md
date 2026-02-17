# Requirements - Remove UIIntegrator Keep-Alive Loop

## Version History
- `v0`: Initial capture from observed failure in browser-mcp integration flow.
- `v1`: Design-ready requirements after codebase understanding pass.

## Goal / Problem Statement
`UIIntegrator` keep-alive currently runs a background `page.evaluate("1")` loop and may close/reopen pages during normal navigations. This causes real failures (for example `open_tab(url)` / `page.goto()` failing with target-closed errors). We need deterministic page lifecycle behavior.

## In-Scope Use Cases
1. Initialize `UIIntegrator` and navigate immediately without background lifecycle races.
2. Reopen page explicitly when needed.
3. Close integrator resources cleanly with optional page/context/browser shutdown.
4. Ensure core no longer exposes unnecessary background keep-alive behavior.

## Acceptance Criteria
1. Remove keep-alive loop behavior from `UIIntegrator`.
2. Remove keep-alive API surface (`start_keep_alive`, internal keep-alive task/interval helpers).
3. `initialize()` + immediate `page.goto(...)` does not involve background page reopen logic.
4. `reopen_page()` remains explicit and deterministic.
5. Add/adjust tests to cover `UIIntegrator` lifecycle behavior without requiring real browser process.
6. Update documentation to reflect no keep-alive background loop.
7. Bump package version for release publishing.

## Constraints / Dependencies
- `brui_core` is consumed by `browser-mcp`; changes must be explicit so downstream can update quickly.
- Must avoid legacy compatibility shims or dual behavior.
- Existing integration tests in this repo depend on local runtime/browser availability and are not reliable in all environments.

## Assumptions
- Page health should be managed explicitly by callers and operation flow, not implicit background probing.
- Removing keep-alive is acceptable for current product use cases and improves determinism.

## Open Questions / Risks
- Downstream consumers currently calling `start_keep_alive` must be updated in lockstep.
- Versioning policy: this is a breaking API change, so release should use a new major or explicitly documented breaking minor.

## Scope Triage
- **Chosen depth: Medium**
- Rationale:
  - public API removal in core,
  - lifecycle behavior changes in foundational library module,
  - test and docs updates required.
