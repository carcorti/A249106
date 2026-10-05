#!/usr/bin/env python3
"""Round-04 v5 regression of the inherited v4 I/O boundaries."""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent
PHASE=sys.argv[1]
if PHASE not in ('v3','v5'):
    raise SystemExit('phase must be v3 or v5')
OUT=ROOT/'validation'/f'io_{PHASE}'
if OUT.exists():
    raise SystemExit('refuse to overwrite evidence')
OUT.mkdir()
BUILD=OUT/'build'
BUILD.mkdir()
for name in ('a249106.c','Makefile','a249106'):
    shutil.copy2(ROOT/'src'/name,BUILD/name)
B=BUILD/'a249106'
SO=OUT/'libio.so'

def need(ok,msg):
    if not ok:
        raise RuntimeError(msg)

def call(name,args,env=None,cwd=OUT):
    p=subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True,timeout=10)
    (OUT/f'{name}.log').write_text(f'exit={p.returncode}\n'+p.stdout+p.stderr)
    return p

def cmd(name,mode,d,env=None):
    return call(name,[str(B),mode,str(d)],env)

def init(name,d,env=None,hi=19164,group=1):
    return call(name,[str(B),'init',str(d),'19164',str(hi),'16384',str(group),'1'],env)

def snap(d):
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in d.iterdir() if p.is_file()}

p=call('inject_build',['gcc','-std=c17','-Wall','-Wextra','-Wpedantic','-Werror',
                       '-shared','-fPIC','-o',str(SO),str(ROOT/'validation/inject.c'),'-ldl'])
need(p.returncode==0,p.stderr)
base=dict(os.environ,LD_PRELOAD=str(SO))
d=OUT/'complete'
need(init('init_complete',d).returncode==0,'init complete')
need(cmd('next_complete','next',d).returncode==0,'next complete')
need(cmd('verify_complete','verify',d).returncode==0,'verify healthy EOF')
orphan=d/'s000000000a.tsv'
orphan.write_text('unexpected state\n')
before=snap(d)
for mode in ('status','verify','next'):
    p=cmd(f'orphan_{mode}',mode,d)
    need(p.returncode==1 and 'orphan/future' in p.stderr,'ordinary orphan refusal')
    for kind in ('eio','eintr'):
        env=dict(base,A249106_TEST_READDIR_AT='2' if mode=='next' else '1',
                 A249106_TEST_READDIR_KIND=kind)
        p=cmd(f'injected_{kind}_{mode}',mode,d,env)
        need('INJECT readdir error' in p.stderr,'injector missed scan')
        expected=0 if PHASE=='v3' else 1
        need(p.returncode==expected,f'{PHASE} {mode} {kind}: {p.returncode}')
        if PHASE=='v5':
            need('read run directory' in p.stderr and 'COMPLETE' not in p.stdout,'failed audit accepted')
        need(snap(d)==before,'failed audit modified durable state')
if PHASE=='v5':
    env=dict(base,A249106_TEST_READDIR_AT='2',A249106_TEST_READDIR_KIND='signal')
    p=cmd('injected_signal_next','next',d,env)
    need(p.returncode==2 and 'COMPLETE' not in p.stdout,'handled EINTR classification')
    need(snap(d)==before,'signal audit changed state')
orphan.unlink()
need(cmd('clean_after_fault','verify',d).returncode==0,'clean EOF after fault')
if PHASE=='v5':
    for state in ('zero','multiple','unsealed'):
        q=OUT/state
        if state=='unsealed':
            shutil.copytree(d,q)
            (q/'s0000000000.sha256').unlink()
            for table in ('manifest.tsv','hits.tsv'):
                f=q/table
                f.write_text(''.join(f.read_text().splitlines(keepends=True)[:2]))
        else:
            need(init('init_'+state,q,hi=51931).returncode==0,'state init')
            if state=='multiple':
                for j in range(2):
                    need(cmd(f'next_{state}_{j}','next',q).returncode==0,'multi seal')
        normal=cmd('healthy_'+state,'verify',q)
        need(normal.returncode==(0 if state=='multiple' else 2),'state EOF control')
        (q/'s000000000a.tsv').write_text('orphan\n')
        expected=snap(q)
        for mode in ('status','verify'):
            env=dict(base,A249106_TEST_READDIR_AT='1',A249106_TEST_READDIR_KIND='eio')
            p=cmd(f'fault_{state}_{mode}',mode,q,env)
            need(p.returncode==1 and 'read run directory' in p.stderr and
                 'COMPLETE' not in p.stdout,'state audit error accepted')
            need(snap(q)==expected,'state audit changed files')
parent=OUT/'parent'
parent.mkdir()
env=dict(base,A249106_TEST_PARENT=str(parent.resolve()),A249106_TEST_PARENT_FAIL='1')
p=init('parent_failure',parent/'failed',env)
need(p.returncode==(0 if PHASE=='v3' else 1),'parent sync error result')
if PHASE=='v3':
    need(f'SYNC {parent}\n' not in p.stderr,'v3 unexpectedly synced parent')
else:
    need(f'SYNC {parent}\n' in p.stderr and 'initialized' not in p.stdout,'parent not synced before success')
    need(not (parent/'failed/run.cfg').exists(),'config emitted before parent sync failure')
    (parent/'nested').mkdir()
    (OUT/'linked_parent').symlink_to(parent,target_is_directory=True)
    paths=[('relative',Path('parent/relative')),('nested',Path('parent/nested/run')),
           ('absolute_trailing',str(parent/'absolute')+'///'),('symlink',Path('linked_parent/run'))]
    for name,path in paths:
        actual=(OUT/path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
        env=dict(base,A249106_TEST_PARENT=str(actual.parent))
        p=init('parent_'+name,path,env)
        need(p.returncode==0 and f'SYNC {actual.parent}\n' in p.stderr,'parent path resolution')
        need(cmd('next_'+name,'next',actual).returncode==0,'next path')
        need(cmd('verify_'+name,'verify',actual).returncode==0,'verify path')
print(f'{PHASE}: directory error/EOF, state preservation and parent fsync checks PASS')
