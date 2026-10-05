#!/usr/bin/env python3
"""Bounded, local-only regression for the exact A249106 candidate."""
from __future__ import annotations

import os
import pathlib
import shutil
import signal
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
EXE = ROOT / "src/a249106"
OUT = HERE / "r4"


def run(args, cap=10, expected=0, log=None, env=None):
    p = subprocess.run(
        [str(a) for a in args], cwd=ROOT, capture_output=True, text=True,
        timeout=cap, env=env,
    )
    if log is not None:
        (OUT / log).write_text(p.stdout + p.stderr)
    if p.returncode != expected:
        raise RuntimeError(
            f"{args} returned {p.returncode}, expected {expected}: "
            f"{p.stderr[-1000:]}"
        )
    return p


def init(tag, low, high, group=1, workers=1, exe=EXE, env=None):
    d = OUT / tag
    run([exe, "init", d, low, high, 16384, group, workers], env=env)
    return d


def next_run(tag, d, exe=EXE, cap=30):
    return run(
        ["/usr/bin/time", "-f", "wall=%e cpu=%U+%S rss_kb=%M",
         exe, "next", d],
        cap=cap, log=f"{tag}.log",
    )


def complete(d, exe=EXE, env=None):
    p = run([exe, "verify", d], env=env)
    if "COMPLETE" not in p.stdout:
        raise RuntimeError(f"verify not complete: {d}")


def hits(d):
    return "".join((d / "hits.tsv").read_text().splitlines(keepends=True)[2:])


def oracle(low, high):
    return run([sys.executable, HERE / "oracle.py", low, high], cap=30).stdout


def main():
    if OUT.exists():
        raise RuntimeError(f"refuse to overwrite {OUT}")
    OUT.mkdir()
    known = [19164, 129357, 14971875, 45316123, 434325391]
    for n in known:
        tag = f"known_{n}"
        d = init(tag, n, n)
        next_run(tag, d, cap=15)
        complete(d)
        if hits(d) != oracle(n, n):
            raise RuntimeError(f"known witness mismatch {n}")
        print(tag, "PASS", flush=True)

    for low, high in [(2, 500), (19150, 19180), (129340, 129370)]:
        tag = f"oracle_{low}_{high}"
        d = init(tag, low, high)
        next_run(tag, d, cap=15)
        complete(d)
        if hits(d) != oracle(low, high):
            raise RuntimeError(f"oracle mismatch {tag}")
        print(tag, "PASS", flush=True)

    d3 = init("seg_three", 2, 33000)
    for j in range(3):
        next_run(f"seg_three_{j}", d3)
        p = run([EXE, "verify", d3], expected=2 if j < 2 else 0)
        if j < 2 and "INCOMPLETE" not in p.stdout:
            raise RuntimeError("partial verification not explicit")
    d1 = init("seg_one", 2, 33000, group=3)
    next_run("seg_one", d1)
    complete(d1)
    if hits(d3) != hits(d1):
        raise RuntimeError("segment union mismatch")
    print("segmentation PASS", flush=True)

    for scale, low, high in [
        ("low", 19100, 35483),
        ("high", 899999999983617, 900000000000000),
    ]:
        reference = None
        for workers in (1, 4, 8):
            tag = f"bench_{scale}_{workers}"
            d = init(tag, low, high, workers=workers)
            next_run(tag, d)
            complete(d)
            content = hits(d)
            if reference is None:
                reference = content
            elif reference != content:
                raise RuntimeError(f"worker mismatch {tag}")
            print(tag, "PASS", flush=True)

    low, high = 899999999967233, 900000000000000
    interrupted = init("interrupted", low, high, group=2)
    whole = init("whole", low, high, group=2)
    p = subprocess.Popen(
        [str(EXE), "next", str(interrupted)], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    state = interrupted / "s0000000000.tsv"
    deadline = time.monotonic() + 30
    observed = False
    while time.monotonic() < deadline and p.poll() is None:
        if state.exists() and "frontier\t899999999983616\n" in state.read_text():
            p.send_signal(signal.SIGINT)
            observed = True
            break
        time.sleep(0.005)
    if not observed:
        p.kill()
        raise RuntimeError("durable first block not observed")
    stdout, stderr = p.communicate(timeout=30)
    (OUT / "interrupted_first.log").write_text(stdout + stderr)
    if p.returncode != 2:
        raise RuntimeError("interrupted next did not report incomplete")
    status = run([EXE, "status", interrupted]).stdout
    if ("sealed_frontier=899999999967232" not in status or
            "checkpoint_frontier=899999999983616" not in status):
        raise RuntimeError("frontier separation after interruption")
    run([EXE, "verify", interrupted], expected=2)
    active_source = OUT / "active_source"
    shutil.copytree(interrupted, active_source)

    def reject_active(tag, source, mutate):
        d = OUT / f"active_corrupt_{tag}"
        shutil.copytree(source, d)
        statefile = d / "s0000000000.tsv"
        mutate(statefile)
        before = [(d / name).read_bytes()
                  for name in ("manifest.tsv", "hits.tsv")]
        for mode in ("verify", "next"):
            p = subprocess.run(
                [str(EXE), mode, str(d)], cwd=ROOT,
                capture_output=True, text=True, timeout=10,
            )
            (OUT / f"active_corrupt_{tag}_{mode}.log").write_text(
                p.stdout + p.stderr)
            if p.returncode != 1:
                raise RuntimeError(f"active corruption accepted by {mode}: {tag}")
            if (d / "s0000000000.sha256").exists():
                raise RuntimeError(f"active corruption sealed: {tag}")
            after = [(d / name).read_bytes()
                     for name in ("manifest.tsv", "hits.tsv")]
            if after != before:
                raise RuntimeError(f"active corruption promoted: {tag}")

    def replace_once(path, old, new):
        content = path.read_bytes()
        if content.count(old) != 1:
            raise RuntimeError(f"mutation anchor absent or ambiguous: {old!r}")
        path.write_bytes(content.replace(old, new, 1))

    def flip_hash_digit(path, key):
        content = bytearray(path.read_bytes())
        marker = key + b"\t"
        if content.count(marker) != 1:
            raise RuntimeError(f"hash mutation anchor: {key!r}")
        offset = content.index(marker) + len(marker)
        content[offset] = ord("1") if content[offset] != ord("1") else ord("0")
        path.write_bytes(content)

    reject_active("aligned_frontier", active_source,
                  lambda p: replace_once(p,
                      b"frontier\t899999999983616\n",
                      b"frontier\t900000000000000\n"))
    reject_active("hit_count", active_source,
                  lambda p: replace_once(p,b"hits\t0\n",b"hits\t1\n"))
    reject_active("config_hash", active_source,
                  lambda p: flip_hash_digit(p,b"cfg_sha"))
    reject_active("footer_digest", active_source,
                  lambda p: flip_hash_digit(p,b"state_sha"))
    reject_active("footer_inside_truncate", active_source,
                  lambda p: p.write_bytes(p.read_bytes()[:-8]))
    reject_active("footer_missing", active_source,
                  lambda p: p.write_bytes(
                      p.read_bytes().split(b"state_sha\t",1)[0]))

    active_hit = init("active_hit_source", 19164, 19164)
    shutil.copy2(OUT / "known_19164" / "s0000000000.tsv",
                 active_hit / "s0000000000.tsv")
    reject_active("hit_digit", active_hit,
                  lambda p: replace_once(p,b"19164\t",b"19165\t"))
    print("active checkpoint mutations REJECTED", flush=True)

    next_run("interrupted_resume", interrupted)
    next_run("whole", whole)
    complete(interrupted)
    complete(whole)
    if hits(interrupted) != hits(whole):
        raise RuntimeError("resume mismatch")
    print("interruption/resume PASS", flush=True)

    changes = {
        "truncate": lambda d: (d / "s0000000000.tsv").write_bytes(
            (d / "s0000000000.tsv").read_bytes()[:-8]),
        "checksum": lambda d: (d / "s0000000001.sha256").write_text(
            "0" * 64 + "\n"),
        "gap": lambda d: (d / "s0000000000.tsv").unlink(),
        "duplicate": lambda d: (d / "s0000000001.tsv").write_bytes(
            (d / "s0000000000.tsv").read_bytes()),
        "future": lambda d: (d / "s0000000004.tsv").write_bytes(
            (d / "s0000000000.tsv").read_bytes()),
    }
    for tag, change in changes.items():
        d = OUT / f"corrupt_{tag}"
        shutil.copytree(d3, d)
        change(d)
        p = subprocess.run(
            [str(EXE), "verify", str(d)], cwd=ROOT,
            capture_output=True, text=True, timeout=10,
        )
        (OUT / f"corrupt_{tag}.log").write_text(p.stdout + p.stderr)
        if p.returncode == 0:
            raise RuntimeError(f"corrupt state accepted: {tag}")
    bad_table = OUT / "corrupt_manifest"
    shutil.copytree(d3, bad_table)
    manifest = bad_table / "manifest.tsv"
    lines = manifest.read_text().splitlines(keepends=True)
    lines[2] = lines[2].replace("0000000000", "0000000001", 1)
    manifest.write_text("".join(lines))
    for mode in ("verify", "next"):
        p = subprocess.run(
            [str(EXE), mode, str(bad_table)], cwd=ROOT,
            capture_output=True, text=True, timeout=10,
        )
        if p.returncode == 0:
            raise RuntimeError(f"corrupt aggregate accepted by {mode}")
        (OUT / f"corrupt_manifest_{mode}.log").write_text(p.stdout + p.stderr)
    stale = OUT / "stale_valid_prefix"
    shutil.copytree(d3, stale)
    manifest = stale / "manifest.tsv"
    manifest.write_text("".join(manifest.read_text().splitlines(keepends=True)[:3]))
    hitfile = stale / "hits.tsv"
    hitfile.write_text("".join(hitfile.read_text().splitlines(keepends=True)[:2]))
    p = run([EXE, "verify", stale], expected=2)
    if "REPAIRABLE" not in p.stderr:
        raise RuntimeError("valid aggregate prefix not classified as repairable")
    run([EXE, "next", stale], log="stale_prefix_repair.log")
    complete(stale)
    print("corrupt states REJECTED", flush=True)

    empty = init("empty_config", 899999999999999, 900000000000000)
    run([EXE, "verify", empty], expected=2)
    changed = OUT / "changed_config"
    shutil.copytree(empty, changed)
    cfg = changed / "run.cfg"
    cfg.write_text(cfg.read_text().replace(
        "start\t899999999999999\n", "start\t899999999999998\n"))
    for mode in ("status", "next"):
        p = subprocess.run(
            [str(EXE), mode, str(changed)], cwd=ROOT,
            capture_output=True, text=True, timeout=10,
        )
        if p.returncode == 0:
            raise RuntimeError("changed config accepted")
        (OUT / f"changed_config_{mode}.log").write_text(p.stdout + p.stderr)
    for label, value in [
        ("overcap", "900000000000001"),
        ("one", "1"),
        ("overflow", "18446744073709551616"),
    ]:
        target = OUT / label
        p = subprocess.run(
            [str(EXE), "init", str(target), value, value, "16384", "1", "1"],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
        if p.returncode == 0 or target.exists():
            raise RuntimeError(f"bad CLI admission {label}")
    print("numeric/config boundaries PASS", flush=True)

    harness = OUT / "backend_harness"
    run([
        "cc", "-O2", "-std=c17", "-Wall", "-Wextra", "-Wno-unused-function",
        "-fopenmp", "-o", harness, HERE / "backend.c",
        "-fopenmp", "-lgmp", "-lcrypto",
    ], cap=20, log="backend_build.log")
    if "BACKEND PASS" not in run([harness], cap=20).stdout:
        raise RuntimeError("backend harness")
    print("factor/capacity harness PASS", flush=True)

    san = OUT / "sanitize_build"
    san.mkdir()
    for name in ("a249106.c", "Makefile"):
        shutil.copy2(ROOT / "src" / name, san / name)
    run([
        "make", "-C", san,
        "CFLAGS=-O1 -g -std=c17 -Wall -Wextra -Werror -fopenmp "
        "-fsanitize=address,undefined -fno-omit-frame-pointer",
        "LDFLAGS=-fopenmp -fsanitize=address,undefined",
    ], cap=30, log="sanitizer_build.log")
    sanexe = san / "a249106"
    sanenv = {**os.environ, "ASAN_OPTIONS": "detect_leaks=0"}
    for tag, low, high in [("san_known", 19164, 19164),
                           ("san_small", 2, 500)]:
        d = init(tag, low, high, exe=sanexe, env=sanenv)
        run([sanexe, "next", d], cap=30, log=f"{tag}.log", env=sanenv)
        complete(d, exe=sanexe, env=sanenv)
    print("ASan/UBSan PASS (LSan unavailable)", flush=True)
    print("LOCAL REGRESSION PASS", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"LOCAL REGRESSION FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
