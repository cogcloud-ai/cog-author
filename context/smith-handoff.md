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
