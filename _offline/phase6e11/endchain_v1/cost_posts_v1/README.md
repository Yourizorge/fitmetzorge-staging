# Source-bound cost post review

Standalone offline compiler for the 47 unresolved posts retained at checkpoint
32c7d891. No connection, SQL, platform start, CI dispatch or execution authority.

From this directory, set COST_SOURCE_ROOT to the repository's absolute path and
run `python -B -m unittest -v test_cost_post_closure`. On Windows long paths,
use the extended absolute path. To create an immutable result directory:

```text
python -B cost_post_closure.py --source-root ABSOLUTE_REPOSITORY --out NEW_DIRECTORY
```

The compiler checks 149 source pins and the retained original register. Its
own source hashes are bound separately. It executes only selected, pinned
source fragments with recording capabilities; no database counters are
invented. Generated coverage, program and subprogram files must be treated
as a source model, never as original PG/Auth execution receipts.

The normal path and all fourteen original fault selectors retain uncertainty.
Unknown dispatches are not refunded. Unknown mandatory closure reserve denies
the next mutation. A numerically feasible reservation is only ARITHMETIC_ONLY.

Current result: 0/47 complete cost posts closed. Five explicit subprograms and
seven conditional native-zero routes are separately useful. Conditional zero
is neither a measured zero nor proof of WAL coverage. Existing root provenance,
effective route binding and missing platform/managed costs remain open.
Independent wheel/OCI attestation is not introduced as a new approval gate.

No fourth legacy WAL probe, flush, timeout increase or hosted budget increase.
The cap remains 2349. Original exports and historical failures remain unchanged.
