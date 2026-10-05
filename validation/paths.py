#!/usr/bin/env python3
"""Bounded round-04 pathname regression; fresh private fixtures only."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PHASE = sys.argv[1] if len(sys.argv) == 2 else ""
if PHASE not in ("v4", "v5"):
    raise SystemExit("usage: paths.py v4|v5")
OUT = ROOT / "validation" / ("paths_" + PHASE +
                            ("" if PHASE == "v4" else ""))
OUT.mkdir(exist_ok=False)
RECORDS = []
KNOWN = "19164\t25564\t31848\t58412\t61916\t96336"


def need(ok, message):
    if not ok:
        raise RuntimeError(message)


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def call(label, cmd, expected=0, env=None, cwd=ROOT, seconds=10):
    p = subprocess.run([str(x) for x in cmd], cwd=cwd, env=env,
                       stdin=subprocess.DEVNULL, capture_output=True,
                       text=True, timeout=seconds)
    log = OUT / (label + ".log")
    log.write_text("exit=" + str(p.returncode) + "\nstdout:\n" + p.stdout
                   + "\nstderr:\n" + p.stderr)
    RECORDS.append({"label": label, "exit": p.returncode,
                    "log_sha256": digest(log)})
    need(p.returncode == expected, label + ": " + p.stderr)
    return p


def long_dir(label, length, unicode=False):
    """Return absent final DIR with exact UTF-8 byte length; create parents."""
    top = OUT / label
    top.mkdir()
    p = top
    while length - len(os.fsencode(p)) - 1 > 180:
        p = p / ("a" * 180)
        p.mkdir()
    remaining = length - len(os.fsencode(p)) - 1
    need(1 <= remaining <= 180, "final component capacity")
    name = ("é" * (remaining // 2) + "x" * (remaining % 2)
            if unicode else "x" * remaining)
    result = p / name
    need(len(os.fsencode(result)) == length, "path byte length mismatch")
    return top, result


def snapshot(directory):
    return {p.name: digest(p) for p in directory.iterdir() if p.is_file()}


def init(label, binary, directory, env=None, expected=0, cwd=ROOT):
    return call(label, [binary, "init", directory, 19164, 19164, 16384, 1, 1],
                expected, env, cwd)


def lifecycle(label, binary, spelling, physical, env=None):
    init(label + "_init", binary, spelling, env)
    p = call(label + "_zero", [binary, "status", spelling], env=env)
    need("checkpoint_frontier=19163" in p.stdout and "hits=0" in p.stdout,
         "zero-completion sentinel")
    call(label + "_zero_verify", [binary, "verify", spelling], 2, env)
    p = call(label + "_next", [binary, "next", spelling], env=env)
    need("CLOSED" in p.stderr, "no seal closure")
    p = call(label + "_verify", [binary, "verify", spelling], env=env)
    need("COMPLETE" in p.stdout and "checkpoint_frontier=19164" in p.stdout
         and "hits=1" in p.stdout, "completion counters")
    need((physical / "hits.tsv").read_text().splitlines()[2:] == [KNOWN],
         "known hit output mismatch")
    need(len((physical / "manifest.tsv").read_text().splitlines()) == 3,
         "manifest row count")
    state = physical / "s0000000000.tsv"
    seal = physical / "s0000000000.sha256"
    need(seal.read_text() == digest(state) + "\n", "seal digest mismatch")
    before = snapshot(physical)
    p = call(label + "_repeat", [binary, "next", spelling], env=env)
    need("already sealed" in p.stdout and snapshot(physical) == before,
         "completed next changed durable bytes")
    init(label + "_no_clobber", binary, spelling, env, 1)
    need(snapshot(physical) == before, "init clobbered existing run")


if PHASE == "v4":
    build = OUT / "build"
    build.mkdir()
    for name in ("a249106.c", "Makefile", "a249106"):
        shutil.copy2(ROOT / "src" / name, build / name)
    need(digest(build / "a249106.c") ==
         "0b00bbd4b3fd4b4aceedcdfba283b4917f029b2392b9996e82022693104a5ae9",
         "not exact v4 source")
    need(digest(build / "a249106") ==
         "84bd640d5d29e130019dff526f598d234abb9b7bffda53137d623579076233ff",
         "not exact v4 binary")
    binary = build / "a249106"
else:
    binary = ROOT / "src/a249106"

# Only getpid's filename use is interposed. No signal/cancellation probe uses it.
shim = OUT / "fixed_pid.c"
shim.write_text("#include <sys/types.h>\n#include <unistd.h>\n"
                "pid_t getpid(void) { return (pid_t)2147483647; }\n")
call("shim_build", ["gcc", "-std=c17", "-Wall", "-Wextra", "-Werror",
                    "-shared", "-fPIC", shim, "-o", OUT / "fixed_pid.so"],
     seconds=20)
fixed = os.environ.copy()
fixed["LD_PRELOAD"] = str(OUT / "fixed_pid.so")

# 10 PID digits: state temp at 4095 chars, seal temp at 4098 chars.
top, directory = long_dir("counterexample", 4064)
try:
    if PHASE == "v4":
        init("counter_init", binary, directory, fixed)
        call("counter_next", [binary, "next", directory], 1, fixed)
        p = call("counter_status", [binary, "status", directory], env=fixed)
        need("INCOMPLETE" in p.stdout and "checkpoint_frontier=19164" in p.stdout,
             "v4 counterexample not reproduced")
        call("counter_verify", [binary, "verify", directory], 2, fixed)
        need((directory / "s0000000000.tsv").is_file() and
             not (directory / "s0000000000.sha256").exists(), "v4 seal state")
        saved = OUT / "counterexample_state"
        saved.mkdir()
        for p in directory.iterdir():
            if p.is_file():
                shutil.copy2(p, saved / p.name)
    else:
        p = init("counter_init", binary, directory, fixed, 1)
        need("run directory path too long" in p.stderr and
             "initialized" not in p.stdout and not directory.exists(),
             "v5 counterexample side effect")
finally:
    shutil.rmtree(top)

if PHASE == "v5":
    # Linux x86-64 long has 19 decimal digits. Bytes incl trailing '/' count.
    maximum = 4095 - (1 + 18 + 5 + 19)
    need(maximum == 4052, "unexpected target long width")
    for length in (maximum - 1, maximum, maximum + 1, 4093):
        top, directory = long_dir("boundary_" + str(length), length,
                                  unicode=length == maximum)
        try:
            if length <= maximum:
                lifecycle("boundary_" + str(length), binary, directory,
                          directory, fixed)
            else:
                p = init("boundary_" + str(length), binary, directory, fixed, 1)
                need("run directory path too long" in p.stderr and
                     not directory.exists() and "initialized" not in p.stdout,
                     "boundary rejection not before mkdir")
        finally:
            shutil.rmtree(top)

    # Trailing separators and multibyte component bytes at the same limit.
    for label, length in (("trailing_ok", maximum - 1),
                          ("trailing_bad", maximum)):
        top, directory = long_dir(label, length)
        try:
            spelling = str(directory) + "/"
            if label == "trailing_ok":
                lifecycle(label, binary, spelling, directory)
            else:
                p = init(label, binary, spelling, expected=1)
                need("run directory path too long" in p.stderr and
                     not directory.exists(), "trailing byte not counted")
        finally:
            shutil.rmtree(top)

    # Short alternate spelling of an existing deep parent is usable throughout.
    top, directory = long_dir("symlink_parent", maximum)
    link = OUT / "short_parent"
    link.symlink_to(directory.parent, target_is_directory=True)
    spelling = str(link / directory.name)
    try:
        lifecycle("symlink", binary, spelling, directory)
    finally:
        link.unlink()
        shutil.rmtree(top)

    relative = os.path.relpath(OUT / "relative", ROOT)
    lifecycle("relative", binary, relative, OUT / "relative")
    empty = init("empty", binary, "", expected=1)
    need("initialized" not in empty.stdout, "empty path accepted")

    # Changed init guard under instrumented exact source in its own build dir.
    san = OUT / "sanitize_build"
    san.mkdir()
    shutil.copy2(ROOT / "src/a249106.c", san / "a249106.c")
    shutil.copy2(ROOT / "src/Makefile", san / "Makefile")
    call("san_build", ["gcc", "-O1", "-g", "-std=c17", "-fopenmp",
                       "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                       san / "a249106.c", "-o", san / "a249106",
                       "-lgmp", "-lcrypto"], seconds=30)
    env = os.environ.copy()
    env["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1"
    env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    for length in (maximum, maximum + 1):
        top, directory = long_dir("san_" + str(length), length)
        try:
            p = init("san_" + str(length), san / "a249106", directory, env,
                     0 if length == maximum else 1)
            need("AddressSanitizer" not in p.stderr and "runtime error" not in p.stderr,
                 "sanitizer finding")
            if length > maximum:
                need(not directory.exists() and
                     "run directory path too long" in p.stderr,
                     "sanitized rejection")
        finally:
            shutil.rmtree(top)

(OUT / "results.json").write_text(json.dumps({
    "phase": PHASE, "source_sha256": digest(binary.parent / "a249106.c"),
    "makefile_sha256": digest(binary.parent / "Makefile"),
    "binary_sha256": digest(binary), "checks": RECORDS, "result": "PASS"
}, indent=2) + "\n")
print(PHASE + " pathname matrix PASS (" + str(len(RECORDS)) + " processes)")
