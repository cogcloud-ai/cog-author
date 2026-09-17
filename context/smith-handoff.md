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
