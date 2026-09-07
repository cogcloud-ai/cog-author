# Initial verification

- Installed the declared Pixi environment and generated pixi.lock for the declared platforms.
- 15 deterministic tests passed on the local installed environment.
- Smith package validation with tests: zero errors, zero warnings.
- CogSpec reference validator: passed.
- Shared Smith runtime modules remain byte-identical to their template masters.
- Model calls in deterministic tests use mocked responses; this is interface and
  contract evidence, not model-quality evidence.
- Deep health probe: local default endpoint http://127.0.0.1:8080/v1 refused the
  connection. Live model fixtures have not been run. No live baseline is claimed.

The author handoff was also exercised with its hand-written action-extractor
source example: export, Smith request ingestion, transfer of the complete
source snapshot, manifest locality/fixture declarations, then Smith checking
with the candidate's tests and the core reference validator. All passed.
This was a deterministic handoff check, not a model-authored build.
