#!/usr/bin/env python3
"""Bounded package checks. No full-range enumeration or published-release claim."""
from pathlib import Path, PurePosixPath
import csv
from decimal import Decimal
import hashlib
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

sys.dont_write_bytecode = True
from a6 import factor_trial
import yaml

ROOT = Path(__file__).resolve().parents[1]

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def integrity():
    expected = {}
    for line in (ROOT / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        p = PurePosixPath(name)
        require(not p.is_absolute() and '..' not in p.parts, 'unsafe inventory path')
        require(name not in expected and len(digest) == 64, 'invalid inventory')
        expected[name] = digest
    actual = set()
    for p in ROOT.rglob('*'):
        rel = p.relative_to(ROOT)
        if rel.parts[0] == '.git':
            continue  # Provider-created clone metadata only.
        require(not p.is_symlink(), 'unexpected symlink: ' + str(rel))
        if p.is_file() and str(rel) != 'SHA256SUMS':
            actual.add(rel.as_posix())
    require(actual == set(expected), 'package inventory mismatch')
    for name, digest in expected.items():
        require(sha(ROOT / name) == digest, 'checksum mismatch: ' + name)
    return len(expected)

def unpack(name, target):
    with tarfile.open(ROOT / 'evidence' / name, 'r:gz') as archive:
        names = set()
        members = archive.getmembers()
        for m in members:
            p = PurePosixPath(m.name)
            require(m.isfile() and not p.is_absolute() and '..' not in p.parts,
                    'unsafe archive member: ' + m.name)
            require(m.name not in names, 'duplicate archive member')
            names.add(m.name)
        for m in members:
            p = target / m.name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(archive.extractfile(m).read())
            p.chmod(m.mode & 0o777)
    return names

def call(args, cwd, expected=0, cap=60):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    p = subprocess.run([str(a) for a in args], cwd=cwd, env=env,
                       stdin=subprocess.DEVNULL, capture_output=True, text=True,
                       timeout=cap)
    require(p.returncode == expected,
            'command failed: ' + ' '.join(map(str, args)) + '\n' + p.stdout + p.stderr)
    return p

def table(name, header):
    raw = (ROOT / 'data' / name).read_bytes()
    require(raw.endswith(b'\n\n') and not raw.endswith(b'\n\n\n') and b'\r' not in raw,
            'terminal blank record: ' + name)
    lines = raw.decode().splitlines()
    require(lines[0] == header and lines[-1] == '', 'table framing: ' + name)
    return [list(map(int, line.split('\t'))) for line in lines[1:-1]]

def positive_checks():
    b = (ROOT / 'data/b249106.txt').read_bytes()
    require(b.endswith(b'\n\n') and not b.endswith(b'\n\n\n') and b'\r' not in b,
            'b-file framing')
    indices = [list(map(int, line.split())) for line in b.decode().splitlines()[:-1]]
    rows = table('witnesses.tsv', 'i\tn\tx1\tx2\tx3\tx4\troot')
    require(len(rows) == 7 and [r[0] for r in rows] == list(range(1, 8)), 'indexed rows')
    require(indices == [r[:2] for r in rows], 'b-file/witness join')
    factorizations = []
    for r in rows:
        require(len(r) == 7 and r[1] >= 2, 'witness schema')
        chain = [r[1]]
        for _ in range(4):
            n = chain[-1]
            f = factor_trial(n)
            chain.append(sum(e * (n // p) for p, e in f))
            factorizations.append({'operand': n, 'factors': f})
        q = sum(n*n for n in chain)
        root = math.isqrt(q)
        require(root*root == q and chain + [root] == r[1:], 'positive witness disagreement')
    scripts = {}
    for name in ['a6.py', 'a7.py', 'families.py']:
        normal = json.loads(call([sys.executable, ROOT/'validation'/name], ROOT).stdout)
        optimized = json.loads(call([sys.executable, '-O', ROOT/'validation'/name], ROOT).stdout)
        require(normal == optimized and normal['status'] == 'PASS', 'normal/optimized: ' + name)
        scripts[name] = normal
    family = table('family.tsv', 'p\tn\tx1\tx2\tx3\tx4\troot')
    require(family == [[r['p'], *r['chain'], r['root']]
                       for r in scripts['families.py']['family']], 'family table')
    return rows, {'indexed_positive_inputs': len(rows), 'factorizations': factorizations,
                  'normal_optimized_checks': list(scripts), 'prime_parameters': len(family)}

def c_checks(work, rows):
    build = work / 'build'
    build.mkdir()
    for name in ['a249106.c', 'Makefile']:
        shutil.copy2(ROOT / 'src' / name, build / name)
    call(['make', '-C', build], work)
    exe = build / 'a249106'
    def run_case(name, lo, hi, threads=1, group=1):
        d = work / name
        call([exe, 'init', d, lo, hi, 16384, group, threads], work)
        # next commits one operational segment per call. Every test is bounded.
        segments = ((hi-lo+16384)//16384 + group-1)//group
        for _ in range(segments):
            call([exe, 'next', d], work)
        require('COMPLETE' in call([exe, 'verify', d], work).stdout, 'incomplete smoke')
        return d, (d / 'hits.tsv').read_text().splitlines()[2:]
    for r in rows:
        _, hits = run_case('n'+str(r[0]), r[1], r[1])
        require(hits == ['\t'.join(map(str, r[1:]))], 'C singleton mismatch')
    counts=[]
    for j, (lo,hi) in enumerate([(2,500),(19150,19180),(129340,129370)]):
        _, hits = run_case('w'+str(j), lo, hi)
        oracle = call([sys.executable, ROOT/'validation/oracle.py', lo, hi], ROOT).stdout.splitlines()
        require(hits == oracle, 'SymPy window mismatch')
        counts.append(hi-lo+1)
    for label,lo,hi in [('low',19100,35483),('high',899999999983617,900000000000000)]:
        baseline = None
        for threads in [1,4,8]:
            _, hits = run_case(label+str(threads), lo, hi, threads)
            if baseline is None:
                baseline = hits
            require(hits == baseline, 'thread-mode mismatch')
    d, a = run_case('seg3', 2, 33000)
    _, b = run_case('seg1', 2, 33000, group=3)
    require(a == b, 'segment-grouping mismatch')
    # A corrupt digest must fail closed, even under optimized Python.
    (d/'s0000000000.sha256').write_text('0'*64+'\n')
    call([exe,'verify',d],work,expected=1)
    layout = work/'harness'
    (layout/'validation').mkdir(parents=True)
    (layout/'src').mkdir()
    shutil.copy2(ROOT/'src/a249106.c', layout/'src/a249106.c')
    shutil.copy2(ROOT/'validation/backend.c', layout/'validation/backend.c')
    harness = layout/'backend'
    call(['gcc','-O2','-std=c17','-Wall','-Wextra','-Wno-unused-function',
          '-fopenmp', '-o',harness, layout/'validation/backend.c',
          '-fopenmp','-lgmp','-lcrypto'],work)
    require('BACKEND PASS' in call([harness],work).stdout,'backend harness')
    return {'public_binary_sha256':sha(exe),'C_positive_singletons':7,
            'SymPy_window_inputs':counts,'thread_modes':[1,4,8],
            'thread_windows_each':16384,'segment_grouping':'PASS',
            'altered_digest':'REJECTED','fallback_wide_root':'PASS'}

def main():
    require(len(sys.argv) == 1, 'usage: python3 validation/run.py')
    count = integrity()
    print('Package inventory PASS',flush=True)
    cff = yaml.safe_load((ROOT/'CITATION.cff').read_text())
    require(cff['cff-version']=='1.2.0' and cff['authors']==[
        {'family-names':'Corti','given-names':'Carlo','email':'carlo.corti@outlook.com'}], 'CFF identity')
    require(cff['version']=='v1.0.1' and cff['license']=='MIT' and
            cff['repository-code']=='https://github.com/carcorti/A249106' and
            cff['doi']=='10.5281/zenodo.23155533' and
            cff['preferred-citation']['doi']==cff['doi'] and
            cff['url']==cff['preferred-citation']['url']=='https://doi.org/'+cff['doi'],
            'release citation metadata')
    rows, positives = positive_checks()
    print('Seven positives and eight prime parameters PASS (normal / -O)',flush=True)
    with tempfile.TemporaryDirectory(prefix='a249106-') as tmp:
        work = Path(tmp)
        campaign = work/'campaign'; tests=work/'tests'
        cmembers = unpack('campaign.tar.gz',campaign)
        tmembers = unpack('tests.tar.gz',tests)
        provenance=list(csv.DictReader((ROOT/'evidence/origins.tsv').open(),delimiter='\t'))
        covered={'campaign.tar.gz':set(),'tests.tar.gz':set()}
        for r in provenance:
            dest=r['public_path_or_member']
            if ':' in dest:
                arch,member=dest.split(':',1)
                name=Path(arch).name
                require(name in covered,'unknown evidence archive')
                base=campaign if name=='campaign.tar.gz' else tests
                require(sha(base/member)==r['source_sha256']==r['public_sha256'],'archive provenance')
                covered[name].add(member)
            else:
                require(sha(ROOT/dest)==r['public_sha256'],'public provenance')
        require(covered['campaign.tar.gz']==cmembers and covered['tests.tar.gz']==tmembers,
                'incomplete archive provenance map')
        require((campaign/'code/a249106.c').read_bytes()==(ROOT/'src/a249106.c').read_bytes()
                and (campaign/'code/Makefile').read_bytes()==(ROOT/'src/Makefile').read_bytes(),
                'historical/public source mismatch')
        baseline=(campaign/'accepted_b249106.txt').read_text().splitlines()
        current=(ROOT/'data/b249106.txt').read_text().splitlines()
        require([x for x in baseline if x]==current[:5], 'accepted baseline common prefix')
        record=json.loads((campaign/'result_record.json').read_text())
        coverage=record['coverage']; frontier=434325392; total=0; hits=0
        for item in coverage:
            require(item['low']==frontier and item['high']>=frontier, 'coverage gap')
            state=campaign/item['phase']/('s'+str(item['id']).zfill(10)+'.tsv')
            require(sha(state)==item['state_sha256'],'sealed state identity')
            total+=item['high']-item['low']+1;hits+=item['hits'];frontier=item['high']+1
        require(frontier==10000000001 and total==record['total_inputs']==9565674609
                and hits==2 and len(coverage)==7,'coverage totals')
        times=[line.split() for line in (campaign/'time.tsv').read_text().splitlines()]
        require(len(times)==7 and all(r[2]=='0' for r in times) and
                sum(Decimal(r[1]) for r in times)==Decimal('7983.66'), 'timing reconciliation')
        original=campaign/'code/a249106'
        require(sha(original)==record['canonical_sha256']['src/a249106'],'historical binary')
        for phase in ['p1','p2']:
            require('COMPLETE' in call([original,'verify',campaign/phase],work).stdout,
                    'historical native integrity')
        print('Original executable / complete campaign records PASS',flush=True)
        checks=c_checks(work,rows)
        print('Public C build, small oracles, thread modes, grouping and fallback PASS',flush=True)
    integrity()
    print(json.dumps({'status':'PASS','scope':'LOCAL_BOUNDED_REPRODUCIBILITY',
        'inventory_files':count,'positive_checks':positives,'C_checks':checks,
        'negative_interval_independently_rescanned':False,
        'historical_sanitizers':'retained evidence; optional original-runner replay',
        'campaign_inputs':9565674609,'indexed_terms':7,'next_index':8},indent=2))

if __name__=='__main__':
    try:
        main()
    except (RuntimeError, ValueError, KeyError, OSError, subprocess.TimeoutExpired) as exc:
        print('FAIL: '+str(exc),file=sys.stderr)
        raise SystemExit(1)
