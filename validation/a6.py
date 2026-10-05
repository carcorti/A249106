#!/usr/bin/env python3
"""One independently factored positive witness; no enumeration or campaign."""
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent


def factor_trial(n):
    residual = n
    factors = []
    p = 2
    while p * p <= residual:
        e = 0
        while residual % p == 0:
            residual //= p
            e += 1
        if e:
            factors.append((p, e))
        p = 3 if p == 2 else p + 2
    if residual > 1:
        factors.append((residual, 1))
    if math.prod(p ** e for p, e in factors) != n:
        raise RuntimeError('factor product mismatch')
    return factors


def main():
    if len(sys.argv) > 2:
        raise SystemExit('usage: a6.py [HITS_FILE]')
    hit_path = Path(sys.argv[1]) if len(sys.argv) == 2 else ROOT / 'data/hit6.tsv'
    lines = hit_path.read_text().splitlines()
    if len(lines) != 3 or lines[1] != 'n\tx1\tx2\tx3\tx4\troot':
        raise RuntimeError('expected exactly one recorded hit')
    row = list(map(int, lines[2].split('\t')))
    if len(row) != 6 or row[0] != 1102826289:
        raise RuntimeError('witness identity mismatch')
    chain = [row[0]]
    factorizations = []
    for _ in range(4):
        n = chain[-1]
        factors = factor_trial(n)
        next_value = sum(e * (n // p) for p, e in factors)
        factorizations.append({'operand': n, 'factors': factors,
                               'derivative': next_value})
        chain.append(next_value)
    q = sum(x * x for x in chain)
    root = math.isqrt(q)
    if root * root != q or chain + [root] != row:
        raise RuntimeError('independent witness disagrees')
    print(json.dumps({
        'status': 'PASS', 'scope': 'ONE_POSITIVE_WITNESS_ONLY',
        'method': 'Python exact integers, exhaustive trial division, math.isqrt',
        'primality_basis': 'all trial divisors tested in increasing order; final residual has no divisor up to its integer square root',
        'requested_inputs': 1, 'observed_inputs': 1, 'distinct_inputs': 1,
        'result_classes': {'hit': 1, 'miss': 0},
        'chain': chain, 'factorizations': factorizations,
        'sum_of_squares': q, 'square_root': root,
        'independent_enumeration_of_negative_interval': False,
        'input_sha256': hashlib.sha256(hit_path.read_bytes()).hexdigest(),
        'validator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    }, indent=2))


if __name__ == '__main__':
    main()
