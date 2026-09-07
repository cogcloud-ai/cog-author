---
type: cog [0.1]
name: cog-author
description: "Context Cog. Designs and authors bounded context Cogs from a work brief. Depends on a Cog providing an OpenAI-compatible model endpoint."
version: "0.1.0"
license: BSD-3-Clause
publisher: OpenTeams
manifest: cog.yaml
manifest_schema: openteams/cog-manifest [0.1]
---

# Cog Author

Designs and authors bounded context Cogs for a Builder Op. The consumer is the
Op or a person building a Cog. Supports design, author and revise through the
operation field of the declared ask entry point; HTTP uses the same contract.

Input: a plain-language brief, optional accepted work contract and identity,
supplied source materials, and revision feedback. State is explicit in each
request; no conversation or filesystem access is implicit. Output: questions
or a complete work contract, or concrete source files and Smith identity request.
Schemas, sample pairs, Python syntax, file paths and contract preservation are
checked mechanically. Generated code is never executed by this Cog.

Authoring returns complete source text rather than writing into the caller's
workspace. scripts/export_draft.py validates a clean envelope and exports a
source directory plus smith-request.json. Smith owns final formatting; its
current request interface overlays content, while task_logic.py and tests must
also be transferred by the Builder Op. See README.md for the precise handoff.

Out of scope: arbitrary runtimes, model training, dependency installation,
execution, publication, orchestration and release approval. Unsupported work
abstains with a reason; missing design facts produce questions. This v0 supports
stdlib/pyyaml/jsonschema context tasks. It cannot prove generated code correct.

## Use and verification

Install with `pixi install`, bind with `pixi run resolve` or `pixi run use`, then
check model identity with `pixi run check -- --deep`. Invoke with
`pixi run ask -- --bundle examples/sample-bundle.json`; `pixi run serve` exposes
the declared HTTP endpoint. `pixi run test` runs model-free tests;
`pixi run eval` executes declared fixtures against the bound model.

Results use envelope v1 with payload, problems and binding identity. An ok result
may contain contract problems; the caller's Gate decides acceptance. Locality is
declared in the manifest; the installed binding chooses a compatible model.
The workspace-relative default satisfier is optional convenience, not a bundled
model. Independent installations must supply their own model binding.
