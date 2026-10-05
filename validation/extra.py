#!/usr/bin/env python3
"""Prebounded, local-only checkpoint, TSan and complete-block controls."""
from __future__ import annotations

import os
import pathlib
import selectors
import shutil
import signal
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
HERE = ROOT / "validation"
EXE = ROOT / "src/a249106"
OUT = HERE / "extra"


def run(args, cap=30, expected=0, log=None, env=None):
    p = subprocess.run([str(x) for x in args], cwd=ROOT, text=True,
                       capture_output=True, timeout=cap, env=env)
    if log:
        (OUT / log).write_text(p.stdout + p.stderr)
    if p.returncode != expected:
        raise RuntimeError(f"{args} exit {p.returncode}, wanted {expected}: "
                           f"{p.stderr[-800:]}")
    return p


def init(tag, low, high, group, threads=1, exe=EXE, env=None):
    d = OUT / tag
    run([exe, "init", d, low, high, 16384, group, threads], env=env,
        log=f"{tag}_init.log")
    return d


def hit_rows(d):
    return "".join((d / "hits.tsv").read_text().splitlines(keepends=True)[2:])


def interrupt_after_start(d):
    p = subprocess.Popen([str(EXE), "next", str(d)], cwd=ROOT,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True)
    with selectors.DefaultSelector() as select:
        select.register(p.stderr, selectors.EVENT_READ)
        if not select.select(timeout=10):
            p.kill()
            raise RuntimeError("START deadline")
    first = p.stderr.readline()
    if not first.startswith("START segment="):
        p.kill()
        raise RuntimeError(f"unexpected first message: {first!r}")
    p.send_signal(signal.SIGINT)
    stdout, rest = p.communicate(timeout=30)
    (OUT / "zero_first.log").write_text(first + stdout + rest)
    if p.returncode != 2 or (d / "s0000000000.tsv").exists():
        raise RuntimeError("zero-block interruption certified work")


def interrupt_after_second(d):
    p = subprocess.Popen([str(EXE), "next", str(d)], cwd=ROOT,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True)
    state = d / "s0000000000.tsv"
    observed = False
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline and p.poll() is None:
        try:
            content = state.read_text()
        except FileNotFoundError:
            content = ""
        if "frontier\t899999999983616\n" in content:
            p.send_signal(signal.SIGINT)
            observed = True
            break
        time.sleep(0.005)
    if not observed:
        p.kill()
        raise RuntimeError("second durable checkpoint deadline")
    stdout, stderr = p.communicate(timeout=30)
    (OUT / "multi_first.log").write_text(stdout + stderr)
    if p.returncode != 2 or (d / "s0000000000.sha256").exists():
        raise RuntimeError("multi-block interruption result")


def checkpoint_depth():
    z = init("zero", 899999999983617, 900000000000000, 1)
    zfull = init("zero_full", 899999999983617, 900000000000000, 1)
    interrupt_after_start(z)
    run([EXE, "verify", z], expected=2, log="zero_verify.log")
    run([EXE, "next", z], log="zero_resume.log")
    run([EXE, "next", zfull], log="zero_full.log")
    run([EXE, "verify", z], log="zero_complete.log")
    if hit_rows(z) != hit_rows(zfull):
        raise RuntimeError("zero-block resume mismatch")

    m = init("multi", 899999999950849, 900000000000000, 3)
    mfull = init("multi_full", 899999999950849, 900000000000000, 3)
    interrupt_after_second(m)
    v = run([EXE, "verify", m], expected=2, log="multi_verify.log")
    if "checkpoint_frontier=899999999983616" not in v.stdout:
        raise RuntimeError("two-block checkpoint frontier")
    run([EXE, "next", m], log="multi_resume.log")
    run([EXE, "next", mfull], log="multi_full.log")
    run([EXE, "verify", m], log="multi_complete.log")
    if hit_rows(m) != hit_rows(mfull):
        raise RuntimeError("two-block resume mismatch")
    print("zero/two checkpoint resume PASS", flush=True)


def tsan():
    d = OUT / "tsan"
    d.mkdir()
    controls = d / "controls"
    run(["clang-18", "-O1", "-g", "-std=c17", "-fopenmp=libomp",
         "-fsanitize=thread", "-fno-omit-frame-pointer", "-o", controls,
         HERE / "tsan.c"], cap=20, log="tsan_control_build.log")
    archer = pathlib.Path("/usr/lib/llvm-18/lib/libarcher.so")
    env = {**os.environ, "OMP_TOOL": "enabled", "OMP_TOOL_LIBRARIES": str(archer),
           "TSAN_OPTIONS": "ignore_noninstrumented_modules=1:halt_on_error=1:exitcode=66"}
    run([controls, "startup"], cap=20, log="tsan_startup.log", env=env)
    clean = run([controls, "clean"], cap=20, log="tsan_clean.log", env=env)
    if "WARNING: ThreadSanitizer" in clean.stderr:
        raise RuntimeError("TSan clean control warning")
    race = run([controls, "race"], cap=20, expected=66,
               log="tsan_race.log", env=env)
    if "data race" not in race.stderr or "tsan.c:" not in race.stderr:
        raise RuntimeError("TSan positive control did not locate the race")

    build = d / "build"
    build.mkdir()
    for name in ("a249106.c", "Makefile"):
        shutil.copy2(ROOT / "src" / name, build / name)
    run(["make", "-C", build, "CC=clang-18",
         "CFLAGS=-O1 -g -std=c17 -Wall -Wextra -Werror -fopenmp=libomp "
         "-fsanitize=thread -fno-omit-frame-pointer",
         "LDFLAGS=-fopenmp=libomp -fsanitize=thread"], cap=30,
        log="tsan_candidate_build.log")
    candidate = build / "a249106"
    target = init("tsan_run", 19150, 19180, 1, 4, candidate, env)
    run([candidate, "next", target], cap=30, log="tsan_candidate_next.log", env=env)
    run([candidate, "verify", target], cap=30,
        log="tsan_candidate_verify.log", env=env)
    print("qualified TSan PASS", flush=True)


def measured_blocks():
    for tag, low, high in [
        ("near_default", 434325392, 435373967),
        ("high_default", 899999998951425, 900000000000000),
    ]:
        d = OUT / tag
        run([EXE, "init", d, low, high, 1048576, 1, 8], cap=10)
        p = run(["/usr/bin/time", "-f", "wall=%e cpu=%U+%S rss_kb=%M",
                 EXE, "next", d], cap=30, log=f"{tag}.log")
        if "CLOSED segment=0" not in p.stderr or "fallbacks=0" not in p.stderr:
            raise RuntimeError(f"measurement closure: {tag}")
        run([EXE, "verify", d], cap=10, log=f"{tag}_verify.log")
        print(tag, "PASS", flush=True)


def main():
    if OUT.exists():
        raise RuntimeError(f"refuse to overwrite {OUT}")
    OUT.mkdir()
    checkpoint_depth()
    tsan()
    measured_blocks()
    print("CYCLE4 EXTRA PASS", flush=True)


if __name__ == "__main__":
    main()
