# Validation scopes and replay

The finite campaign and positive mathematical checks are distinct evidence.
No command in the default package check enumerates the 9,565,674,609-input
campaign again. The accepted first five indexed terms were supplied by Carlo
Corti; the retained five-row baseline is labelled historical inside the archive.
`data/b249106.txt` is the sole current b-file and contains seven indexed terms.
The witness and family tables end with exactly one empty record, as does the
b-file. Native hit/state tables retain their original format.

## Frozen campaign

`evidence/campaign.tar.gz` contains `p1/` and `p2/`, every configuration,
segment, digest, manifest and hit table, `code/a249106.c`, `code/Makefile`,
`code/a249106`, `environment.json`, `time.tsv`, historical `result_record.json`,
`accepted_b249106.txt`, and the independent a6/a7 result records.
These are exact original bytes. Historical JSON describes the state when it
was recorded, before the seven-row b-file consolidation; its old b-file hash
is not the current data hash. The old runtime binary and its neighbouring
source/build recipe are preserved together. Native verification authenticates
record consistency and contiguous execution claims; it is correlated with
the search implementation and does not establish an independent negative scan.
The unkeyed digests are integrity records, not cryptographic signatures.

The seven segment intervals join exactly from 434325392 to 10000000000.
Their two hits join the accepted five-row baseline at indices 6 and 7.
`time.tsv` contains seven successful externally timed advances; its exact sum
is 7983.66 seconds. It excludes unrecorded setup/audits and operator overhead.
The performance figure is a campaign measurement, not a future guarantee.

## Positive mathematics and public runner

`a6.py` and `a7.py` are the historical validators with only filename, import,
usage and default-input paths changed. Their trial division, exact arithmetic,
identity checks and square tests are retained. The seventh validator imports
the sixth validator's factorization routine, compares the first hit with the
frozen one-hit state, and recomputes only the new seventh hit.
`run.py` additionally imports that routine and recomputes all seven chains.
These checks are independent of the C factorization backend, but not of each
other's Python routine or of the defining equation.

`families.py` is the original bounded exposition checker, renamed without
byte changes. It checks eight prime parameters, the shifted seeds 4791 and
128, constant chains and three twin-prime examples by direct trial division.
It corroborates examples, not the universal proof, and assigns no new indices.
`oracle.py` retains the original SymPy-based finite membership oracle with
only its usage name changed. `backend.c` includes the public C source and is
therefore a shared-backend stress harness, not an independent oracle.

`run.py` and `replay.py` are package orchestration added during preparation;
they are not the executables of the official campaign and have not received
independent external code review. Their bounds, failure cases, archive path
checks and normal/optimized-Python behavior are checked locally. Any future
change requires refreshing package integrity and affected validation evidence.
Original validator bytes, adapted helpers and substitutions are identifiable
through `evidence/origins.tsv`, `evidence/renames.json` and `tests.tar.gz`.

## Earlier and final implementation tests

`tests.tar.gz` retains the relevant earlier v4 test data (`r4/`, `extra/`),
final campaign-build pathname and I/O data (`paths/`, `io/`), planning samples
(`plan/`), original test scripts (`tools/`), the exact earlier source, Makefile
and executable (`v4/`), and the original consolidation record.
Long archival basenames are compactly addressed under `long/`; the complete
origin map joins every published archive member to its exact workspace bytes.
No external review reports or reviewer packet dossiers are bundled.

The earlier broad tests cover five baseline singletons, three SymPy windows,
thread comparisons, grouping, interrupted resume, corrupt active/sealed states,
CLI/config boundaries and the forced fallback/wide-root harness. Earlier
ASan/UBSan checks cover the first singleton and [2,500]; leak sanitization was
unavailable. Earlier Clang TSan covers a four-thread [19150,19180] interval,
with clean/startup/race controls and OpenMP instrumentation. It is not a full
campaign or final-build TSan run. The final code change was the initialization
path-length guard; arithmetic, block processing and thread behavior were retained.
Targeted final-build tests exercise that guard, sanitizer initialization,
readdir error/EOF handling, durable-state preservation and parent fsync.
Historical logs remain inherited evidence unless a named suite is replayed now.

Optional replay stages, each in a fresh temporary directory:

```sh
python3 validation/replay.py v4-core
python3 validation/replay.py v4-extra
python3 validation/replay.py v5-paths
python3 validation/replay.py v5-io
```

The two v4 modes use the archived earlier executable/source/Makefile;
the v5 modes build the exact public campaign source. Helpers have only path
and filename substitutions. Original tools are also archived byte for byte.
The archived `tools/plan.py` is a historical calibration script with its
original private review-closure guard; it is provenance, not a documented
public replay entry point. Its retained measurement records are under `plan/`.
The runner stages the adapted helpers and discards newly generated fixtures
when finished. Each inherited subprocess has its own bounded timeout; the
whole-suite cap is 600 seconds. These are optional local regression replays,
not a new full campaign, and may fail loudly on an incompatible target.

The core stage additionally requires `/usr/bin/time`, GCC, working ASan/UBSan
and the normal build dependencies. `v4-extra` needs Clang 18, LLVM OpenMP,
Clang TSan and Archer at `/usr/lib/llvm-18/lib/libarcher.so`, plus an environment
where the TSan startup and positive race control work. It includes two
1048576-input measured blocks, each capped at 30 seconds. The pathname stage
requires the recorded Linux x86-64 path/long limits, GCC, LD_PRELOAD and
ASan/UBSan. The I/O stage requires GCC, Linux LD_PRELOAD and writable temporary
storage. No dependency failure is interpreted as a passing sanitizer test.

## Retention boundary

Older drafts, external reviews, chat prompts, duplicate superseded test suites,
provisional planning reports and third-party full texts remain outside the
publication directory. Necessary current records and earlier-source evidence
are compressed, rather than represented by a claim-only summary. No PDF,
compiled public executable, cache, actual remote release or sparse a-file is
part of this draft.
