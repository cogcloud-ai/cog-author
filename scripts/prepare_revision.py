"""Prepare a source/contract-bound request for the existing revise operation."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import cog_core
import task_logic


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, help='JSON with author_request, author_envelope, review_request, review_envelope and allowed_change_scope')
    args = parser.parse_args()
    try:
        document = json.loads(Path(args.request).read_text())
        request = task_logic.prepare_revision(**document)
        result = cog_core._envelope('prepare-revision', True, payload={'request': request}, binding={'source': 'deterministic-revision-handoff'})
        code = 0
    except (ValueError, TypeError, KeyError, OSError, AttributeError) as exc:
        result = cog_core._fail('prepare-revision', 'invalid-revision', str(exc))
        code = 1
    print(json.dumps(result))
    return code


if __name__ == '__main__':
    sys.exit(main())
