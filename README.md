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

The default model reference in `cog.yaml` is a legacy sibling-checkout
convenience and is not distributed with this Cog. Supply a compatible model
through `pixi run use -- --help` or resolve an available descriptor. A capable
coding model is needed for useful authoring; successful installation or a passing mock test does not establish model quality.

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
See the Workbench [tool-suite guide](https://github.com/cogcloud-ai/cog-workbench/blob/main/docs/tool-suite.md) for the goal-first workflow.

## Pure code authoring

For native Op execution through a Workbench provider, activate an already admitted
binding with `suite activate-composition --context cog-author --binding-id ID
--revision N`. The `ask-composed` usage task then accepts `--request` or `--bundle`
with the same author input. Activation writes ignored `.op-composition.json`;
the shared Op runtime includes it in the consumer fingerprint used for resume.
Reactivation is required after consumer or host changes. The adapter is vendored
from cog-workbench's [`bridges/composed_usage.py`](https://github.com/cogcloud-ai/cog-workbench/blob/main/bridges/composed_usage.py);
native `ask` is unchanged.

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

## Durable revision requests

The declared `prepare-revision` deterministic usage task turns saved author and evaluator
artifacts into a request for the existing `revise` usage operation:

```sh
pixi run prepare-revision -- --request examples/revision-input.json
```

The input has `author_request`, its clean `author_envelope`, `review_request`, its
clean `review_envelope`, and `allowed_change_scope` with explicit `paths` and
accepted `criterion_ids` (omission addresses all accepted criteria; the receipt
always records the resolved IDs). Save the output envelope; its `payload.request` is the
next author request. The task never invokes a model or executes source.

[The receipt schema](contracts/revision.schema.json) specifies the stable
`openteams/cog-revision [0.1]` format. The request contains the complete expanded
source snapshot with per-file hashes, the exact accepted contract and its digest,
the candidate fingerprint used by the evaluator, the original review request and
envelope, and a digest binding both review documents. Fingerprints use UTF-8
canonical JSON (sorted keys, compact separators, Unicode preserved); candidate
files are sorted by path. No digest is supplied by the model. Feedback referring
to another candidate/contract or evidence for another candidate is rejected.

Only `revise` and `insufficient_evidence` reviews prepare this handoff. A missing
evidence outcome normally means the coordinating Op should collect/review more
evidence first; this task does not choose that lifecycle policy. An explicit
repair may then use the same receipt. Revisions preserve the accepted contract,
identity and every source file outside the allowed paths, including additions and
deletions. Unchanged JSON schema/fixture material references are hydrated before
fingerprinting and comparison. Receipt hashes correlate artifacts; they are not
authenticated acceptance signatures. Contract redesign needs a new human Gate.

Manual legacy revise requests remain supported. Automatic builder cycles should
always use receipts. The composition adapter also supports Workbench's portable
workspace-relative installations; reactivate after upgrading its source.

Revision criterion IDs guide the requested repair; the mechanical scope is the
allowed file paths and immutable accepted contract. Warning findings outside
those paths do not prevent preparation. Error findings outside the scope refuse
preparation; start a new build with a reviewed wider scope. Original supplied
materials and feedback are retained in feedback alongside the prior source
snapshot, including materials whose paths overlap generated source.
