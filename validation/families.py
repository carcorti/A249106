"""Bounded positive mathematics checks; not an OEIS enumeration."""
import json
from functools import reduce
from math import gcd, isqrt

def require(condition, message):
    if not condition:
        raise ValueError(message)

def factors(n):
    result = []
    d = 2
    while d <= n // d:
        e = 0
        while n % d == 0:
            n //= d
            e += 1
        if e:
            result.append([d, e])
        d = 3 if d == 2 else d + 2
    if n > 1:
        result.append([n, 1])
    return result

def derivative(n):
    return sum(e * (n // p) for p, e in factors(n)) if n > 1 else 0

def orbit(m, h, shifted=False):
    out = [m]
    for _ in range(h):
        out.append(derivative(out[-1]) + (out[-1] if shifted else 0))
    return out

seed = orbit(4791, 4, True)
require(seed == [4791,6391,7962,14603,15479], '4791 orbit')
require(sum(x*x for x in seed) == 24084**2 == 580039056, 'seed square')
rows = []
known = {2:19164,3:129357,5:14971875,7:3945594513,
         11:1366928213897301,13:1451074635683484123,
         17:3963308094697439437172007,19:9478608570268562405492983389}
for p, n in known.items():
    require(factors(p) == [[p,1]], 'prime parameter')
    t = p**p
    require(derivative(t) == t, 'fixed point')
    chain = orbit(4791*t,4)
    require(chain == [t*x for x in seed], 'direct scaled derivative chain')
    root = 24084*t
    require(n == chain[0] and sum(x*x for x in chain) == root*root, 'witness')
    require(reduce(gcd, chain+[root]) == t, 'full gcd')
    rows.append(dict(p=p,t=t,n=n,chain=chain,root=root))
comparison = orbit(128,2,True)
require(comparison == [128,576,2688], '128 orbit')
require(sum(x*x for x in comparison) == 2752**2, '128 square')
for p in (2,3,5,7):
    t=p**p
    require(orbit(128*t,2) == [t*x for x in comparison], 'A230543 scaling')
fixed = {}
for h in (3,4,8):
    fixed[str(h)] = dict(seed_sum=h+1,is_square=isqrt(h+1)**2==h+1)
    require(orbit(27,h) == [27]*(h+1), 'constant chain')
twins=[]
for p in (3,5,11):
    n=p*(p+2)
    require(derivative(n)==2*(p+1), 'twin derivative')
    require(n*n+derivative(n)**2==(n+2)**2, 'twin square')
    require(gcd(n,derivative(n))==1, 'twin primitivity')
    twins.append(dict(p=p,n=n,root=n+2))
print(json.dumps(dict(status='PASS',seed=seed,
    seed_factorizations=[factors(x) for x in seed[:4]],family=rows,
    comparison_A230543=dict(seed=comparison,root=2752,
        members=[128*p**p for p in (2,3,5,7)]),
    constant_chain_depths=fixed,twin_examples=twins,
    scope='Explicit positive witnesses only; no indexing or negative scan.'),indent=2))
