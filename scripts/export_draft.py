#!/usr/bin/env python3
"""Export validated source text. Never execute or package generated code."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import cog_core
import task_logic
import yaml


def export(request, envelope, destination):
    if not isinstance(envelope, dict) or envelope.get('envelope') != 1 or envelope.get('ok') is not True or envelope.get('problems') or envelope.get('error'):
        raise ValueError('Export requires an ok envelope v1 with no problems or error.')
    if envelope.get('cog') != cog_core.SELF_ID:
        raise ValueError('Envelope identity does not match this author version.')
    problems = cog_core.validate_input(request)
    payload = envelope.get('payload')
    if not isinstance(payload, dict):
        raise ValueError('Missing object payload.')
    problems += cog_core.validate_output(payload, request)
    if problems or payload.get('classification') != 'authored':
        raise ValueError(f'Only a validated authored result can be exported: {problems}')
    payload = task_logic.hydrate(payload, request)
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('Destination must not exist.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.cog-source-', dir=destination.parent))
    try:
        files = {f['path']: f['content'] for f in payload['files']}
        for path, content in files.items():
            target = stage / 'source' / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        smith = dict(payload['smith_request'])
        kind = smith.pop('kind', 'context')
        smith.update(manifest='yaml', cog_md=files['COG.md'], context={
            'input_schema': json.loads(files['context/input-schema.json']),
            'output_schema': json.loads(files['context/output-schema.json']),
            'output_example': json.loads(files['context/output-example.json'])},
            examples={'sample_bundle': json.loads(files['examples/sample-bundle.json'])})
        if kind == 'context':
            smith['context']['system_md'] = files['context/system.md']
            smith['evals'] = {'smoke_fixture': files['evals/smoke.fixture.yaml']}
        for path, value in {
            'smith-request.json': smith,
            'eval-plan.json': {'operation': 'plan', 'contract': payload['contract'], 'files': payload['files'], 'evidence': []},
            'handoff.json': {'version': 1, 'kind': kind, 'contract': payload['contract'],
                             'fixture_paths': sorted(p for p in files if p.endswith('.fixture.yaml')),
                             'source_paths': sorted(files),
                             'status': 'source-only-not-packaged-or-executed'},
        }.items():
            (stage / path).write_text(json.dumps(value, indent=2) + '\n')
        # Never replace an existing destination, including one created during export.
        destination.mkdir()
        for child in stage.iterdir():
            shutil.move(str(child), destination / child.name)
    finally:
        shutil.rmtree(stage)
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True)
    parser.add_argument('--envelope', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        print(export(json.loads(Path(args.request).read_text()), json.loads(Path(args.envelope).read_text()), args.out))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Export refused: {exc}\n')
