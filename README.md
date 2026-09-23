# Cog Author

Designer and source author for a Cog-building Op. This independent context Cog
turns a brief into a work contract, then produces complete source files ready
for evaluation and final formatting by cog-smith.

## Run

```sh
pixi install
pixi run test
pixi run resolve
pixi run check -- --deep
pixi run ask -- --bundle examples/sample-bundle.json
pixi run ask -- --bundle examples/author-bundle.json
```

The default model reference is relative to the CogLab workspace. Outside that
workspace, supply a compatible model through `pixi run use -- --help` or resolve
an available descriptor. A capable coding model is needed for useful authoring;
successful installation or a passing mock test does not establish model quality.

## Operations

All operations use the declared `ask` task (or the HTTP endpoint) and select
behavior with the request's `operation` field:

| Operation | Input | Result |
|---|---|---|
| design | Brief, optional previous contract, materials and feedback | Questions or a complete work contract |
| author | Accepted contract and package identity | Complete source snapshot and Smith request identity |
| revise | Same accepted contract, previous source files, feedback | Complete revised source snapshot |

There is no hidden conversational state. Feed answers into the next request's
brief/feedback. Contract changes go through design. The caller chooses when a
contract is accepted; this Cog does not make that decision.

`examples/authored-payload.json` is a hand-written source-output example for the
action-extractor task, not evidence of a model run. Its schema/example consistency,
code syntax and source checks are exercised by the deterministic suite.

## Source handoff

Save the full author envelope, including problems and model identity. Export it:

```sh
pixi run python scripts/export_draft.py --request examples/author-bundle.json \
  --envelope author-result.json --out runs/action-draft
```

The exporter rechecks input, output and identity, refuses reported problems and
existing destinations, and writes:

- `source/`: complete author-owned source text, including task logic and tests.
- `eval-plan.json`: input for cog-build-evaluator's plan operation.
- `smith-request.json`: current Smith-compatible context/identity overlays.
- `handoff.json`: accepted contract and inventory, including all fixture paths.

The source snapshot supports the author/evaluator revision loop before final
packaging. Generated code is **not executed** by authoring or export.

Smith's current `new --from-request` accepts content overlays but does not accept
task logic, tests, extra fixture files or a locality override. A Builder Op using
that interface must transfer every file in `source/`, set the final manifest's
locality from the contract and its fixture list from the handoff, then run Smith
checking with tests. A default starter package is not the authored candidate.
`smith-request.json` intentionally omits a destination; the caller supplies it.

This repository supplies a Cog, not the coordinating Builder Op or a new Smith
compiler interface. It supports context tasks and pure code tasks using stdlib, pyyaml and jsonschema.

## Verification and limits

`pixi run test` checks source completeness, traversal/machinery protection,
schema/example consistency, contract preservation, export, invalid inputs, and
envelope behavior with a mocked model. `pixi run eval` runs six live-model
fixtures: design, author, revise, missing information, injected instructions and
unsupported model-training work. Live authoring quality still needs a suitable model and
independent evaluation of the generated candidate.

Check the package from a sibling cog-smith checkout:

```sh
pixi run python ../cog-smith/src/cogsmith_cli.py check . --tests
pixi run python ../cog-spec/tools/validate_cog.py .
```

Only `src/task_logic.py` is author-owned under src. Other modules retain Smith's
verified hashes. Results carry envelope v1; an ok result with problems requires
the Op's Gate to decide whether to proceed.

## Workbench suite integration

The declared `composition` interface lets workbench prepare this Cog's packaged
context and run its existing input/output checks around an external Harness-only
or Model+Harness turn. It does not replace or modify Smith's src machinery.
The `export-draft` interface exposes the existing validated source exporter as a
declared lifecycle task. Workbench can transfer the complete source snapshot
into a Smith package and retain the accepted contract and evaluation evidence.
See sibling `cog-workbench/docs/tool-suite.md` for the goal-first workflow.

## Pure code authoring

For native Op execution through a Workbench provider, activate an already admitted
binding with `suite activate-composition --context cog-author --binding-id ID
--revision N`. The `ask-composed` usage task then accepts `--request` or `--bundle`
with the same author input. Activation writes ignored `.op-composition.json`;
the shared Op runtime includes it in the consumer fingerprint used for resume.
Reactivation is required after consumer or host changes. The adapter is vendored
from `cog-workbench/bridges/composed_usage.py`; native `ask` is unchanged.

Set request `kind: code`. The designed contract and author identity retain
`kind: code`; omit `model_cog` from the identity. The current extension supports
pure work with no external reaches. Code source implements `check_input`,
`run(bundle, grant, journal)` returning `(payload, problems)`, and `check_output`.
It needs no model prompt or model-evaluation fixtures. It still supplies schemas,
examples and deterministic tests. `examples/code-authored-payload.json` is a
hand-written integration fixture, not evidence of live model authoring.

The exporter writes kind in handoff.json; Workbench passes Smith's existing
`--kind code` flag and transfers source without adding a context bridge. Code
kind is a runtime property: this author Cog continues to use a model to write it.

For large snapshots, author/revise may return `contract: null` with the supplied
`contract_sha256`, and unchanged JSON schema/fixture files may use
`{path, material_ref, material_sha256}` instead of content. Supply SHA-256 values
with input materials so the model can copy them. The exporter verifies and expands
these references entirely from the request; it never reads referenced paths from
the filesystem. Code and tests cannot use references. Workbench `suite snapshot
--request ... --envelope ...` returns the expanded evaluator request. Always use
that snapshot for evaluation and fingerprinting; raw reference forms are not the
candidate source snapshot.

## License

Copyright 2026 OpenTeams. Licensed under the [Apache License 2.0](LICENSE).
Third-party dependencies and external model services retain their own licenses
and terms. Previously published BSD-3-Clause versions remain available under
that license.

## Public preview

See the [suite guide](https://github.com/cogcloud-ai/cog-op-builder/blob/main/docs/repositories.md)
for repository roles, supported setup, and current limitations.
