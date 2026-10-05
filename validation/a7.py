#!/usr/bin/env python3
"""One new positive witness; inherits the frozen a(6) result without rescanning."""
import hashlib
import json
import math
from pathlib import Path
import sys

from a6 import factor_trial

ROOT = Path(__file__).resolve().parent.parent


def main():
    if len(sys.argv) > 2:
        raise SystemExit('usage: a7.py [HITS_FILE]')
    hit_path = Path(sys.argv[1]) if len(sys.argv) == 2 else ROOT / 'data/hit7.tsv'
    lines = hit_path.read_text().splitlines()
    previous = (ROOT / 'data/hit6.tsv').read_text().splitlines()
    if len(lines) != 4 or lines[:3] != previous:
        raise RuntimeError('expected unchanged a(6) prefix and exactly one new hit')
    row = list(map(int, lines[3].split('\t')))
    if len(row) != 6 or row[0] != 3945594513:
        raise RuntimeError('new witness identity mismatch')
    chain = [row[0]]
    factorizations = []
    for _ in range(4):
        n = chain[-1]
        factors = factor_trial(n)
        following = sum(e * (n // p) for p, e in factors)
        factorizations.append({'operand': n, 'factors': factors,
                               'derivative': following})
        chain.append(following)
    q = sum(x * x for x in chain)
    root = math.isqrt(q)
    if root * root != q or chain + [root] != row:
        raise RuntimeError('independent witness disagrees')
    print(json.dumps({
        'status': 'PASS', 'scope': 'ONE_NEW_POSITIVE_WITNESS_ONLY',
        'method': 'Python exact integers, exhaustive trial division, math.isqrt',
        'requested_inputs': 1, 'observed_inputs': 1, 'distinct_inputs': 1,
        'result_classes': {'hit': 1, 'miss': 0},
        'chain': chain, 'factorizations': factorizations,
        'sum_of_squares': q, 'square_root': root,
        'independent_enumeration_of_negative_interval': False,
        'previous_positive': 'inherited immutable a6 record; not recomputed',
        'input_sha256': hashlib.sha256(hit_path.read_bytes()).hexdigest(),
        'validator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'trial_division_implementation_sha256': hashlib.sha256(
            (ROOT / 'validation/a6.py').read_bytes()).hexdigest()
    }, indent=2))


if __name__ == '__main__':
    main()
