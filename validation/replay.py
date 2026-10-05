#!/usr/bin/env python3
"""Optional original test suites, staged outside the publication directory."""
from pathlib import Path
import shutil
import sys
import tempfile
sys.dont_write_bytecode = True
from run import ROOT, call, integrity, require, unpack

def main():
    modes={'v4-core':('regress.py',[]), 'v4-extra':('extra.py',[]),
           'v5-paths':('paths.py',['v5']), 'v5-io':('io.py',['v5'])}
    require(len(sys.argv)==2 and sys.argv[1] in modes,
            'usage: python3 validation/replay.py v4-core|v4-extra|v5-paths|v5-io')
    mode=sys.argv[1]
    integrity()
    with tempfile.TemporaryDirectory(prefix='a249106-replay-') as tmp:
        root=Path(tmp);hist=root/'history';unpack('tests.tar.gz',hist)
        (root/'src').mkdir();(root/'validation').mkdir()
        source=hist/'v4' if mode.startswith('v4') else ROOT/'src'
        for name in ['a249106.c','Makefile']:
            shutil.copy2(source/name,root/'src'/name)
        if mode.startswith('v4'):
            shutil.copy2(source/'a249106',root/'src/a249106')
        else:
            call(['make','-C',root/'src'],root)
        for p in (ROOT/'validation').iterdir():
            if p.suffix in ['.py','.c']:
                shutil.copy2(p,root/'validation'/p.name)
        script,args=modes[mode]
        # Each inherited subprocess has its own short timeout; whole-suite cap only.
        print(call([sys.executable,root/'validation'/script,*args],root,cap=600).stdout)
    print(mode+' PASS; temporary replay removed')

if __name__=='__main__':
    try:
        main()
    except (RuntimeError,ValueError,OSError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr)
        raise SystemExit(1)
