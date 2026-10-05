# Local package validation

Status: **PACKAGE_DRAFT — AWAITING AUTHOR INSPECTION**.
Prepared October 5, 2026; intended initial version v1.0.
The DOI remains `10.5281/zenodo.xxxxxxxx`. No upload/release is asserted.

## Frozen inputs and identities

PERSONAL IDENTITY PASS: Carlo Corti, as instructed by the author and declared
in the existing MIT LICENSE, TeX author block, CFF and README.
The existing LICENSE bytes are preserved. There is no personal copyright
field in the C source to normalize.

The public `src/a249106.c` and `src/Makefile` are byte-identical to the frozen
campaign sources, with stable unversioned names and no lifecycle labels.
The archived original binary is preserved. The fresh GCC build on this host
also matched its hash; verification nevertheless checks the original executable
separately. All exact package hashes are in the root `SHA256SUMS`.
`paper/A249106_v4.tex` is an unchanged copy of the current manuscript.

CANONICAL B-FILE PASS: the selected consolidation record provides seven rows,
indices 1 through 7. `data/b249106.txt` is byte-identical to the workspace
canonical file; its five-row common prefix agrees with the accepted historical
baseline. The workspace's old five-row copy remains history outside this
package. The archive's `accepted_b249106.txt` is explicitly historical input,
not a current b-file. There is no superseded public b-file.

FINAL BLANK-LINE PASS: public b-file, indexed witness table and prime-family
table end with exactly `0a 0a`, without a third newline. The skill's original
framing checker was run as well as the public runner's checks.
AUXILIARY A-FILE: NO, because there are no known later indexed values;
the prime-family rows are positive members without certified indices.

## Executed package checks

The bounded command `python3 validation/run.py` passed. It checks the inventory
and all archive provenance entries; recomputes seven positive chains and their
28 operand factorizations; runs the sixth/seventh and eight-prime family
validators in normal and optimized Python; verifies the complete p1/p2 records
with the original binary; and reconciles seven adjacent segments,
9,565,674,609 inputs, two hits and the exact 7983.66-second timing sum.
The fresh C build passed seven singletons, three independent SymPy windows
(499,31,31 inputs), one/four/eight-thread equality on two 16384-input windows,
segment grouping, corrupt-digest rejection and the forced fallback/wide-root
harness. These checks leave no public executable, cache or generated state.

All documented optional replay stages passed from staged package inputs:

```sh
python3 validation/replay.py v4-core
python3 validation/replay.py v4-extra
python3 validation/replay.py v5-paths
python3 validation/replay.py v5-io
```

The v4 core includes interrupted resume, corruption/config boundaries and
ASan/UBSan (leak sanitizer unavailable). The extra stage includes the qualified
Clang/OpenMP TSan startup, clean and positive race controls, the small four-thread
candidate test and two bounded measurement blocks. The final-source pathname
stage passed its 44-process matrix, including initialization sanitizer checks;
the I/O stage passed fault/EOF, durable-state preservation and parent fsync
checks. These are finite test suites, not full-campaign sanitizer coverage.

CFF YAML parsing and the required identity/repository/version/license/DOI fields
passed. This is a draft with a syntactically retained placeholder, not a verified
DOI or actual release-date receipt. No external CFF schema validator was installed.
TeX passed two `pdflatex -draftmode -halt-on-error` passes from the extracted
package; no PDF was created.

## Local distribution and failure checks

RAW DISTRIBUTION-SHAPE PASS applies to the exact frozen local inventory,
including `.gitignore`, copied to an unrelated root and extracted from a
simulated provider-style archive. The README command
`python3 validation/run.py` passed in both forms. A clone-shaped copy with
provider-created `.git/` metadata also passed its inventory check.
The public command passed under `python3 -O` as well.

Negative controls rejected changed input bytes, an absent required file,
an unlisted file, an unexpected symlink, an altered C source, altered
compressed evidence and a hostile archive member. A coherent rehashed change
of a witness coordinate was rejected by the arithmetic check, rather than only
by checksum comparison. The package orchestration passed local failure-path and
no-change closure checks. It prevents Python bytecode caches during the public
commands and leaves the frozen inventory unchanged.

## Package size and limits

The campaign archive contains 33 files totalling 127895 bytes before tar
packaging and 46131 bytes after gzip compression. The test archive contains
535 files totalling 4660037 bytes, compressed to 1496703 bytes. Published file
basenames, including archive members, are at most 25 characters. Renamings and
exact unchanged archival bytes are documented in `evidence/origins.tsv` and
`evidence/renames.json`.

Completeness of negative intervals is inherited from the finite exact C
campaign, not independently rescanned. The first five terms remain accepted
baseline evidence. General family statements rely on the manuscript proofs;
finite examples do not establish priority or sequence positions.
New orchestration scripts received local checks, not an external code review.
The raw package requires author inspection and a separate final pre-upload
audit before publication. No campaign, PDF, remote mutation or submission was
performed during package preparation.
