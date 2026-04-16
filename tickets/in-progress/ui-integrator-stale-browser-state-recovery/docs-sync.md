# Docs Sync

## Decision

- No additional repository doc changes were required for `2.0.2`.

## Rationale

- `2.0.1` already introduced and documented the UIIntegrator page-creation recovery flow.
- `2.0.2` only hardens the internal browser-state reset path so that recovery cannot hang on stale cleanup operations.
- The public usage guidance for consumers does not change.
