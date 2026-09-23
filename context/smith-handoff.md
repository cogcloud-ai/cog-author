# Source handoff v1
An authored payload is a complete source snapshot, not an installed Cog.
The caller exports a checked envelope with scripts/export_draft.py.
smith-request.json contains identity plus context/examples/evals/COG.md overlays.
The source directory also includes task_logic.py and tests, which Smith's current
--from-request interface does not accept. The Builder Op must retain and transfer
these author-owned files and check the final package with tests. Do not discard
them or accept Smith's starter tests as evidence for the generated task.
Locality and any additional fixture declarations must be reflected in the final
manifest. No model.json, secrets, filesystem paths or runtime grants are authored.

Each evals/*.fixture.yaml is a single mapping, not a sequence. Its bundle path
is relative to the Cog root, for example examples/sample-bundle.json. Exported
fixture inputs must satisfy the accepted input schema; deterministic tests cover
invalid input rejection. The four required fixture files are smoke, insufficient,
adversarial and boundary. A live authoring attempt exposed this ambiguity on
2026-09-07; the revised candidate passed these checks before packaging.

Explicit kind extension: handoff.json records kind (context by default for old
artifacts). Pure code contracts/identities use kind: code and no model_cog.
The exporter removes kind from Smith's request and the host supplies --kind code.
It transfers the complete authored snapshot onto code machinery and does not add
context composition, model requirements or model evaluation declarations.
Code test cases execute via the declared native task; review remains independent.

Compact references: an authored result can copy the request's contract_sha256
and use contract:null. JSON schema/fixture rows can copy a supplied material path
and SHA-256 in material_ref/material_sha256. The exporter verifies every digest,
expands from supplied request data only, and applies the same full-source checks.
It never reads material_ref as a filesystem path. Python and tests require source
content, not references. eval-plan.json always contains the expanded snapshot.
