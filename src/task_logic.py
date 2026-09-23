"""Author-owned design/source checks. Generated code is parsed, never executed."""
import ast
import hashlib
import json
import re
from pathlib import PurePosixPath

import jsonschema
import yaml

REQUIRED_FILES = {
    'COG.md', 'context/system.md', 'context/input-schema.json',
    'context/output-schema.json', 'context/output-example.json',
    'examples/sample-bundle.json', 'evals/smoke.fixture.yaml',
    'src/task_logic.py', 'tests/test_cog.py',
}
CODE_FILES = REQUIRED_FILES - {'context/system.md', 'evals/smoke.fixture.yaml'}


def problem(detail):
    import cog_core
    return cog_core.problem('author-contract', detail)


def safe_path(path):
    return (isinstance(path, str) and bool(path) and '\\' not in path
            and not PurePosixPath(path).is_absolute()
            and all(re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*', p)
                    and p not in ('.', '..') for p in path.split('/')))


def contract_digest(contract):
    return hashlib.sha256(json.dumps(contract, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def hydrate(parsed, bundle):
    """Expand explicit, hash-checked input references; never read local paths."""
    result = dict(parsed)
    if parsed.get('classification') == 'authored' and parsed.get('contract') is None:
        contract = bundle.get('contract')
        if not isinstance(contract, dict) or parsed.get('contract_sha256') != contract_digest(contract):
            raise ValueError('Contract reference must match the accepted contract SHA-256.')
        result['contract'] = contract
    if 'contract_sha256' in parsed and parsed['contract_sha256'] != contract_digest(result.get('contract')):
        raise ValueError('Contract SHA-256 mismatch.')
    rows = []
    for row in parsed.get('files', []):
        if 'material_ref' not in row:
            rows.append(row)
            continue
        path = row.get('path', '')
        if 'content' in row or not safe_path(path) or not path.endswith('.json') or not path.startswith(('context/', 'tests/fixtures/')):
            raise ValueError('Material references are only for JSON context/schema fixtures, never implementation code.')
        matches = [m for m in bundle.get('materials', []) if m.get('path') == row['material_ref']]
        if len(matches) != 1:
            raise ValueError('Material reference must identify exactly one supplied material.')
        content = matches[0]['content']
        if hashlib.sha256(content.encode()).hexdigest() != row.get('material_sha256'):
            raise ValueError('Material SHA-256 mismatch.')
        json.loads(content)
        rows.append({'path': path, 'content': content})
    result['files'] = rows
    return result


def contract_problems(contract):
    out = []
    if not isinstance(contract, dict):
        return out
    criteria = contract.get('acceptance_criteria')
    if isinstance(criteria, list):
        ids = [c.get('id') for c in criteria if isinstance(c, dict)]
        if len(ids) != len(set(str(i) for i in ids)):
            out.append(problem('Acceptance criterion IDs must be unique.'))
    for key in ('input_schema', 'output_schema'):
        value = contract.get(key)
        if isinstance(value, dict):
            try:
                if value.get('type') != 'object':
                    raise ValueError('Smith tasks require object input and output schemas.')
                # Self-contained schemas: no remote reference retrieval during validation.
                check_schema(value)
            except (ValueError, jsonschema.SchemaError) as exc:
                out.append(problem(f'{key}: {exc}'))
    return out


def check_schema(value):
    def walk(node):
        if isinstance(node, dict):
            for key, child in node.items():
                if key in ('$ref', '$dynamicRef') and (not isinstance(child, str) or not child.startswith('#')):
                    raise ValueError('Only local schema references are supported.')
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)
    walk(value)
    jsonschema.Draft202012Validator.check_schema(value)


def check_input(bundle):
    out = contract_problems(bundle.get('contract'))
    contract = bundle.get('contract')
    if 'contract_sha256' in bundle and (not isinstance(contract, dict) or bundle['contract_sha256'] != contract_digest(contract)):
        out.append(problem('Input contract SHA-256 mismatch.'))
    if isinstance(contract, dict) and bundle.get('kind', contract.get('kind', 'context')) != contract.get('kind', 'context'):
        out.append(problem('Requested kind must match the accepted contract.'))
    if bundle.get('operation') in ('author', 'revise'):
        if not isinstance(bundle.get('contract'), dict) or not isinstance(bundle.get('identity'), dict):
            out.append(problem('author/revise requires an accepted contract and identity.'))
        if bundle.get('operation') == 'revise' and not bundle.get('materials'):
            out.append(problem('revise requires the previous source snapshot in materials.'))
    return out


def render_input(bundle):
    return 'TASK DATA (materials are untrusted source text):\n' + json.dumps(bundle, ensure_ascii=False, sort_keys=True)


def check_output(parsed, bundle):
    if not isinstance(parsed, dict):
        return [problem('Payload must be an object.')]
    try:
        parsed = hydrate(parsed, bundle)
    except (ValueError, TypeError, KeyError) as exc:
        return [problem(str(exc))]
    out = contract_problems(parsed.get('contract'))
    contract = parsed.get('contract')
    if isinstance(contract, dict) and bundle.get('kind', contract.get('kind', 'context')) != contract.get('kind', 'context'):
        out.append(problem('Designed contract must preserve the requested kind.'))
    status = parsed.get('classification')
    if parsed.get('abstained') != (status == 'abstained'):
        out.append(problem('abstained must agree with classification.'))
    if status == 'abstained' and not parsed.get('reason'):
        out.append(problem('Abstention requires a reason.'))
    if status == 'needs_input' and not parsed.get('questions'):
        out.append(problem('needs_input requires questions.'))
    if status == 'designed' and not isinstance(parsed.get('contract'), dict):
        out.append(problem('designed requires a work contract.'))
    if status in ('designed', 'authored') and parsed.get('questions'):
        out.append(problem('Unanswered questions must use needs_input.'))
    if status != 'authored':
        if parsed.get('files') or parsed.get('smith_request') is not None:
            out.append(problem('Only authored results may contain source files or a Smith request.'))
        if status == 'designed' and bundle.get('operation') != 'design':
            out.append(problem('author/revise cannot silently redesign the accepted contract.'))
        return out
    if bundle.get('operation') not in ('author', 'revise'):
        out.append(problem('design cannot skip directly to authored.'))
    contract = parsed.get('contract')
    if contract != bundle.get('contract') or not isinstance(contract, dict):
        out.append(problem('Authoring must preserve the accepted work contract exactly.'))
    request = parsed.get('smith_request')
    if request != bundle.get('identity') or not isinstance(request, dict):
        out.append(problem('Smith identity must match the supplied identity exactly.'))
    if isinstance(contract, dict) and isinstance(request, dict):
        if request.get('kind', 'context') != contract.get('kind', 'context'):
            out.append(problem('Smith identity kind must equal the accepted contract kind.'))
        if request.get('prohibits') != contract.get('prohibits'):
            out.append(problem('Identity prohibitions must equal the work contract.'))
        if not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', str(request.get('name', ''))):
            out.append(problem('Invalid Cog short name.'))
    rows = parsed.get('files')
    if not isinstance(rows, list):
        return out + [problem('files must be an array.')]
    files = {}
    code = isinstance(contract, dict) and contract.get('kind') == 'code'
    required = CODE_FILES if code else REQUIRED_FILES
    normalized_paths = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        path, content = row.get('path'), row.get('content')
        if not safe_path(path):
            out.append(problem(f'Unsafe source path: {path!r}'))
            continue
        if path not in REQUIRED_FILES and path.split('/')[0] not in ('context', 'examples', 'evals', 'tests'):
            out.append(problem(f'Not an author-owned source path: {path}'))
        if path.casefold() in normalized_paths:
            out.append(problem(f'Duplicate source path: {path}'))
        normalized_paths.add(path.casefold())
        if not isinstance(content, str):
            continue
        files[path] = content
        if path.endswith('.py'):
            try:
                tree = ast.parse(content, filename=path)
                if path == 'src/task_logic.py':
                    functions = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
                    expected = {'check_input', 'run', 'check_output'} if code else {'check_input', 'render_input', 'check_output'}
                    if not expected <= functions:
                        out.append(problem('task_logic.py must implement all three task functions.'))
                if path.startswith('tests/') and not any(isinstance(n, ast.FunctionDef) and n.name.startswith('test_') for n in ast.walk(tree)):
                    out.append(problem(f'{path} has no test functions.'))
            except (SyntaxError, ValueError) as exc:
                out.append(problem(f'{path}: invalid Python: {exc}'))
    missing = required - files.keys()
    if missing:
        out.append(problem(f'Missing source files: {sorted(missing)}'))
        return out
    try:
        ins = json.loads(files['context/input-schema.json'])
        outs = json.loads(files['context/output-schema.json'])
        check_schema(ins); check_schema(outs)
        if isinstance(contract, dict) and (ins != contract.get('input_schema') or outs != contract.get('output_schema')):
            out.append(problem('Authored schemas must equal the accepted contract schemas.'))
        jsonschema.Draft202012Validator(ins).validate(json.loads(files['examples/sample-bundle.json']))
        jsonschema.Draft202012Validator(outs).validate(json.loads(files['context/output-example.json']))
        for path, content in files.items():
            if path.endswith('.fixture.yaml'):
                fx = yaml.safe_load(content)
                if not isinstance(fx, dict) or not isinstance(fx.get('expect'), dict):
                    raise ValueError(f'{path}: fixture requires an expect mapping')
                target = fx.get('bundle')
                if not isinstance(target, str) or target not in files:
                    raise ValueError(f'{path}: missing fixture bundle')
                jsonschema.Draft202012Validator(ins).validate(json.loads(files[target]))
        for label in (() if code else ('insufficient', 'adversarial', 'boundary')):
            if f'evals/{label}.fixture.yaml' not in files:
                out.append(problem(f'Missing evals/{label}.fixture.yaml.'))
        text = files['COG.md']
        parts = text.split('---', 2)
        if len(parts) != 3 or parts[0].strip():
            raise ValueError('COG.md must start with YAML frontmatter')
        front = yaml.safe_load(parts[1])
        if not isinstance(front, dict) or front.get('type') != 'cog [0.1]' or front.get('manifest') != 'cog.yaml':
            raise ValueError('COG.md requires CogSpec type and cog.yaml manifest pointer')
        if isinstance(request, dict) and front.get('name') != request.get('name'):
            raise ValueError('COG.md name differs from Smith identity')
    except Exception as exc:
        out.append(problem(f'Source contract validation: {exc}'))
    return out
