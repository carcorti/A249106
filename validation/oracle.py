#!/usr/bin/env python3
"""Independent finite membership oracle; not a production search."""
import math
import sys
from sympy import factorint

def derivative(n: int) -> int:
    if n < 2:
        return 0
    return sum(e * (n // p) for p, e in factorint(n).items())

def row(n: int):
    chain = [n]
    for _ in range(4):
        chain.append(derivative(chain[-1]))
    q = sum(x * x for x in chain)
    root = math.isqrt(q)
    return chain, root if root * root == q else None

def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: oracle.py LOW HIGH")
    low, high = map(int, sys.argv[1:])
    if low < 2 or high < low or high - low > 40000:
        raise SystemExit("oracle window outside bounded local domain")
    for n in range(low, high + 1):
        chain, root = row(n)
        if root is not None:
            print("\t".join(map(str, [*chain, root])))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
