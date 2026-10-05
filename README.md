# A249106: exact extension and an infinite family

Carlo Corti — independent researcher — carlo.corti@outlook.com.

This is a local publication draft, prepared October 5, 2026 for author inspection.
The intended first release is **v1.0**, at
[carcorti/A249106](https://github.com/carcorti/A249106).
The DOI `10.5281/zenodo.xxxxxxxx` is a placeholder. No public release or Zenodo
deposit is certified by this directory. The date in `CITATION.cff` records this
local preparation and must be checked against the actual first release date.

## Result and mathematical scope

For the arithmetic derivative D, D(0)=D(1)=0, D(p)=1 for primes p,
and D(x*y)=x*D(y)+y*D(x). From the prime factorization,
D(n)=sum e*(n/p). Membership in [OEIS A249106](https://oeis.org/A249106)
means n>=2 and n^2+D(n)^2+D^2(n)^2+D^3(n)^2+D^4(n)^2 is an integer square.
There is no primitivity restriction.

The consolidated indexed prefix is:

```text
1 19164
2 129357
3 14971875
4 45316123
5 434325391
6 1102826289
7 3945594513
```

The first five terms are the accepted OEIS baseline supplied by the author.
An exact recorded C campaign tested every input in [434325392,10000000000]
(9,565,674,609 inputs) and found the sixth and seventh terms. Indexed completeness
is conditional on the accepted prefix and the correct complete execution of the
C search. Native record integrity checks do not independently repeat the negative
scan. All seven positive chains have independent Python trial-division checks.
The eighth indexed term remains unknown.

The manuscript proves that **4791*p^p is a member for every prime p**, with
full witness p^p times (4791,6391,7962,14603,15479,24084). This is an unconditional
mathematical result; it does not require the finite campaign or a machine bound.
The fixed-point scaling mechanism is historical. The manuscript explains the
specific seed, related sequences and the limits of the prior-art search;
absolute priority is not asserted.

`data/family.tsv` records the eight checked prime parameters 2,3,5,7,11,13,17,19.
Its first column is a prime parameter, **not a sequence index**. In particular,
the four larger members have no certified positions. No sparse OEIS a-file is
provided: there are no known later indexed terms beyond this contiguous prefix.

The C search sieves consecutive inputs to compute the first derivative, then
factors each of the next three operands using deterministic word-size primality
tests and Pollard-rho acceleration with exhaustive trial-division fallback.
The first four chain coordinates use 64-bit unsigned integers, the fourth
derivative uses an unsigned 128-bit extension, and GMP evaluates the square
sum and root exactly. OpenMP processes complete blocks; saved frontiers and
sealed segments record coverage. The finite negative result depends on this
complete exact execution, rather than on timing or digests alone.

## Contents

| Path | Purpose |
| --- | --- |
| `README.md` | Project overview, complete file inventory and public commands |
| `src/a249106.c`, `src/Makefile` | Exact campaign source and build recipe; stable names, no code changes |
| `paper/A249106_v4.tex` | Current English monolithic manuscript, including its bibliography; no external figures or `.bib` required |
| `data/b249106.txt` | Canonical contiguous b-file, indices 1 through 7 |
| `data/witnesses.tsv` | Indexed values, four derivatives and square roots |
| `data/family.tsv` | Positive examples of the proved prime family, without sequence indices |
| `data/hit6.tsv`, `data/hit7.tsv` | Frozen one-hit and two-hit inputs for the historical positive validators |
| `validation/run.py` | Fail-closed bounded public validation command |
| `validation/a6.py`, `validation/a7.py`, `validation/oracle.py`, `validation/families.py` | Independent arithmetic checks and finite-window oracle |
| `validation/backend.c` | Forced-fallback and wide-root harness using the C backend |
| `validation/replay.py` | Optional staged replay of retained implementation test suites |
| `validation/regress.py`, `validation/extra.py`, `validation/paths.py`, `validation/io.py` | Test suites staged by the replay command |
| `validation/inject.c`, `validation/tsan.c` | I/O fault injection and TSan controls for those suites |
| `validation/notes.md`, `validation/summary.md` | Evidence scopes, dependencies and preparation checks |
| `evidence/campaign.tar.gz` | Complete campaign states, original executable, environment, timing and historical result records |
| `evidence/tests.tar.gz` | Relevant earlier-build and final-build test evidence, exact earlier source/executable, original test scripts and consolidation record |
| `evidence/origins.tsv`, `evidence/renames.json` | Original/public name and hash map, and exact validator path substitutions |
| `evidence/sources.md` | Research source locators and provenance boundaries |
| `SHA256SUMS`, `CITATION.cff`, `LICENSE`, `.gitignore` | Package integrity, citation draft, existing author-supplied MIT license and generated-file exclusions |

Archive member names are short; long historical evidence names are mapped to
compact identifiers in `evidence/origins.tsv`. Original evidence bytes are
preserved. Native campaign filenames and configuration fields retain their
original names because they are part of the verified persistence contract.
The source and Makefile are byte-identical to the executed campaign versions.
A fresh build is checked separately from the archived campaign executable.

`SHA256SUMS` lists every public file, including `.gitignore`, except itself.
Only metadata beneath a root `.git/` directory is excluded from the public
file inventory in a clone. No other unexpected file is ignored by the validator;
Git ignore patterns do not exempt generated files from its checksum gate.
Refresh the manifest after any authorized change before repeating validation.

## Build and bounded validation

Requirements: Linux x86-64 for the archived executable; GCC with C17 and OpenMP,
GNU make, GMP and OpenSSL development headers/libraries; Python 3.10 or later
with SymPy and PyYAML. The preparation environment used GCC 13.3.0,
SymPy 1.12 and PyYAML 6.0.1. The archived environment record identifies the
historical campaign's runtime libraries. A different compiler or runtime does
not make a new executable identical to the historical one.

From the repository root, the complete **bounded package check** is:

```sh
python3 validation/run.py
```

This checks the exact package inventory, provenance of every archive member,
seven positive witnesses (28 factorizations), the historical sixth/seventh
validators and family examples in normal and optimized Python, the complete
historical campaign records with their original binary, and a fresh C build.
It compares the C results with SymPy on three windows of 499,31,31 inputs,
checks seven C singletons, compares one/four/eight threads on two 16384-input
windows, checks segment grouping, rejects a corrupt digest and runs the
fallback/wide-root harness. All extraction, compilation and generated states
use a temporary directory outside the package. The command does not resume
or extend the historical search and leaves the package bytes unchanged.

To build an executable for separate use:

```sh
make -C src
```

Remove that generated executable before the inventory check:

```sh
make -C src clean
```

The actual program interface is:

```text
a249106 init DIR START END BLOCK GROUP THREADS
a249106 next DIR
a249106 status DIR
a249106 verify DIR
```

`init` requires a new directory with an existing parent. Each `next` call advances
one configured segment; exit 2 indicates incompleteness/interruption, while
verification exit 0 requires a complete target. Block size is a supported power
of two; the bounded validation uses 16384. The certified technical input cap
is 900000000000000, a width bound rather than a feasible search commitment.
Historical configuration is recorded in `p1/run.cfg` and `p2/run.cfg` inside
`evidence/campaign.tar.gz`. Record verification requires the exact source,
Makefile and binary identities stored in those configurations.

Optional tests of the original operational and sanitizer remits are documented
in `validation/notes.md`. They have additional platform requirements and are
separate from the package's bounded check.

## Manuscript and references

The TeX manuscript keeps its provisional **v4** filename and DOI placeholder.
It was copied without content changes. Scientific review was closed on the
expanded v3; v4 adds a local clarification of the first-term assumptions, not
another full external review. No PDF is bundled or generated during preparation.
To check TeX syntax without creating a PDF, use a temporary output directory:

```sh
mkdir -p /tmp/a249106-tex
pdflatex -draftmode -halt-on-error -interaction=nonstopmode -output-directory=/tmp/a249106-tex paper/A249106_v4.tex
pdflatex -draftmode -halt-on-error -interaction=nonstopmode -output-directory=/tmp/a249106-tex paper/A249106_v4.tex
```

Citation guidance is in `CITATION.cff`: cite both the manuscript and the software.
The existing MIT license applies to the author-provided project material;
external dependencies retain their own licenses. No third-party shared-library
files are bundled. The historical Clang-instrumented executables retain embedded
compiler-runtime portions governed by LLVM's Apache-2.0 license with its
compilation exception.

The bibliography is inline. Literature texts, external reviews, private chat
prompts, older manuscript drafts and regenerable build caches are excluded.
`evidence/sources.md` gives the primary-source links; redistribution rights for
third-party full texts have not been established. Historical test logs may
record the original machine's paths; those are provenance and are not input
dependencies for any documented public command.

The historical seven `next` calls used eight threads and took approximately
7984 seconds on an AMD Ryzen 9 7940HS. Exact timings are retained in the archive.
The aggregate rate is approximately 1.20 million inputs per second for that
campaign, not a bound on another search. The earlier prefix was not rescanned,
and sanitizer tests were bounded, with the scopes in `validation/notes.md`.

This directory was prepared as **PACKAGE_DRAFT — AWAITING AUTHOR INSPECTION**.
Its preparation checks and any later preflight apply to local bytes. Upload,
release metadata finalization, DOI replacement and verification of the actual
GitHub/Zenodo downloads remain separate steps.
