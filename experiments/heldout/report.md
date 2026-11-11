# Held-out evaluation report

This is validation of the value proposition, not evidence that the future v1 runtime has the prototype failure rates.

## execution-cost
- ci: 1.525779s measured (sum of per-run elapsed_seconds)
- ecosystem: 0.106281s measured (sum of per-run elapsed_seconds)
- host_ranges: 0.105325s measured (sum of per-run elapsed_seconds)
- py_declared: 2.704608s measured (sum of per-run elapsed_seconds)
- py_wild: 23.070505s measured (sum of per-run elapsed_seconds)
- wild: 0.406558s measured (sum of per-run elapsed_seconds)

## human-contract-maintenance-time
- intent-change: unavailable (basis: unavailable)
- migration-supplied: unavailable (basis: unavailable)
- platform-ineligibility: unavailable (basis: unavailable)
- transitive-addition: unavailable (basis: unavailable)
- py-flask-2.2.5--werkzeug-2.2.3: unavailable (basis: unavailable)
- py-flask-2.2.5--werkzeug-2.3.8: unavailable (basis: unavailable)
- py-flask-2.2.5--werkzeug-3.0.6: unavailable (basis: unavailable)
- py-flask-2.2.5--werkzeug-3.1.3: unavailable (basis: unavailable)
- py-flask-2.3.3--werkzeug-2.2.3: unavailable (basis: unavailable)
- py-flask-2.3.3--werkzeug-2.3.8: unavailable (basis: unavailable)
- py-flask-2.3.3--werkzeug-3.0.0: unavailable (basis: unavailable)
- py-flask-2.3.3--werkzeug-3.0.6: unavailable (basis: unavailable)
- py-flask-2.3.3--werkzeug-3.1.0: unavailable (basis: unavailable)
- py-flask-2.3.3--werkzeug-3.1.1: unavailable (basis: unavailable)
- py-flask-2.3.3--werkzeug-3.1.2: unavailable (basis: unavailable)
- py-flask-2.3.3--werkzeug-3.1.3: unavailable (basis: unavailable)
- py-flask-3.0.3--werkzeug-2.2.3: unavailable (basis: unavailable)
- py-flask-3.0.3--werkzeug-2.3.8: unavailable (basis: unavailable)
- py-flask-3.0.3--werkzeug-3.0.0: unavailable (basis: unavailable)
- py-flask-3.0.3--werkzeug-3.0.6: unavailable (basis: unavailable)
- py-flask-3.0.3--werkzeug-3.1.0: unavailable (basis: unavailable)
- py-flask-3.0.3--werkzeug-3.1.1: unavailable (basis: unavailable)
- py-flask-3.0.3--werkzeug-3.1.2: unavailable (basis: unavailable)
- py-flask-3.0.3--werkzeug-3.1.3: unavailable (basis: unavailable)
- py-flask-3.1.1--werkzeug-2.2.3: unavailable (basis: unavailable)
- py-flask-3.1.1--werkzeug-2.3.8: unavailable (basis: unavailable)
- py-flask-3.1.1--werkzeug-3.0.0: unavailable (basis: unavailable)
- py-flask-3.1.1--werkzeug-3.0.6: unavailable (basis: unavailable)
- py-flask-3.1.1--werkzeug-3.1.0: unavailable (basis: unavailable)
- py-flask-3.1.1--werkzeug-3.1.1: unavailable (basis: unavailable)
- py-flask-3.1.1--werkzeug-3.1.2: unavailable (basis: unavailable)
- py-flask-3.1.1--werkzeug-3.1.3: unavailable (basis: unavailable)
- py-requests-2.28.2--urllib3-1.26.18: unavailable (basis: unavailable)
- py-requests-2.28.2--urllib3-2.0.0: unavailable (basis: unavailable)
- py-requests-2.28.2--urllib3-2.0.7: unavailable (basis: unavailable)
- py-requests-2.28.2--urllib3-2.1.0: unavailable (basis: unavailable)
- py-requests-2.28.2--urllib3-2.2.3: unavailable (basis: unavailable)
- py-requests-2.28.2--urllib3-2.3.0: unavailable (basis: unavailable)
- py-requests-2.28.2--urllib3-2.4.0: unavailable (basis: unavailable)
- py-requests-2.28.2--urllib3-2.5.0: unavailable (basis: unavailable)
- py-requests-2.31.0--urllib3-1.26.18: unavailable (basis: unavailable)
- py-requests-2.31.0--urllib3-2.0.0: unavailable (basis: unavailable)
- py-requests-2.31.0--urllib3-2.0.7: unavailable (basis: unavailable)
- py-requests-2.31.0--urllib3-2.1.0: unavailable (basis: unavailable)
- py-requests-2.31.0--urllib3-2.2.3: unavailable (basis: unavailable)
- py-requests-2.31.0--urllib3-2.3.0: unavailable (basis: unavailable)
- py-requests-2.31.0--urllib3-2.4.0: unavailable (basis: unavailable)
- py-requests-2.31.0--urllib3-2.5.0: unavailable (basis: unavailable)
- py-requests-2.32.3--urllib3-1.26.18: unavailable (basis: unavailable)
- py-requests-2.32.3--urllib3-2.0.0: unavailable (basis: unavailable)
- py-requests-2.32.3--urllib3-2.0.7: unavailable (basis: unavailable)
- py-requests-2.32.3--urllib3-2.1.0: unavailable (basis: unavailable)
- py-requests-2.32.3--urllib3-2.2.3: unavailable (basis: unavailable)
- py-requests-2.32.3--urllib3-2.3.0: unavailable (basis: unavailable)
- py-requests-2.32.3--urllib3-2.4.0: unavailable (basis: unavailable)
- py-requests-2.32.3--urllib3-2.5.0: unavailable (basis: unavailable)
- unavailable entries are reported as null, never as fabricated zeros

## checker: ci

### missed-breakage
- count: 0
- denominator: 1 (definite-break cases this checker ran on)
- ratio: {"ratio": 0.0, "denominator": 1}

### false-block
- count: 1
- denominator: 3 (definite-ok cases this checker ran on)
- ratio: {"ratio": 0.3333, "denominator": 3}

### unknown-rate
- count: 0
- denominator: 4 (cases run for this checker)
- ratio: {"ratio": 0.0, "denominator": 4}

### coverage
- count: 4
- denominator: 4 (cases run for this checker)
- ratio: {"ratio": 1.0, "denominator": 4}

### aggregate-accuracy
- correct (correct-accept + correct-reject): 3
- missed-breakage: 0; false-block: 1; unknown: 0
- denominator: 4 cases this checker ran on (1 oracle-break + 3 oracle-ok); aggregate is recorded alongside, never instead of, the separate metrics above
- ratio: {"ratio": 0.75, "denominator": 4}

## checker: ecosystem

### missed-breakage
- count: 1
- denominator: 1 (definite-break cases this checker ran on)
- ratio: {"ratio": 1.0, "denominator": 1}

### false-block
- count: 1
- denominator: 3 (definite-ok cases this checker ran on)
- ratio: {"ratio": 0.3333, "denominator": 3}

### unknown-rate
- count: 0
- denominator: 4 (cases run for this checker)
- ratio: {"ratio": 0.0, "denominator": 4}

### coverage
- count: 4
- denominator: 4 (cases run for this checker)
- ratio: {"ratio": 1.0, "denominator": 4}

### aggregate-accuracy
- correct (correct-accept + correct-reject): 2
- missed-breakage: 1; false-block: 1; unknown: 0
- denominator: 4 cases this checker ran on (1 oracle-break + 3 oracle-ok); aggregate is recorded alongside, never instead of, the separate metrics above
- ratio: {"ratio": 0.5, "denominator": 4}

## checker: host_ranges

### missed-breakage
- count: 0
- denominator: 1 (definite-break cases this checker ran on)
- ratio: {"ratio": 0.0, "denominator": 1}

### false-block
- count: 2
- denominator: 3 (definite-ok cases this checker ran on)
- ratio: {"ratio": 0.6667, "denominator": 3}

### unknown-rate
- count: 0
- denominator: 4 (cases run for this checker)
- ratio: {"ratio": 0.0, "denominator": 4}

### coverage
- count: 4
- denominator: 4 (cases run for this checker)
- ratio: {"ratio": 1.0, "denominator": 4}

### aggregate-accuracy
- correct (correct-accept + correct-reject): 2
- missed-breakage: 0; false-block: 2; unknown: 0
- denominator: 4 cases this checker ran on (1 oracle-break + 3 oracle-ok); aggregate is recorded alongside, never instead of, the separate metrics above
- ratio: {"ratio": 0.5, "denominator": 4}

## checker: py_declared

### missed-breakage
- count: 1
- denominator: 5 (definite-break cases this checker ran on)
- ratio: {"ratio": 0.2, "denominator": 5}

### false-block
- count: 10
- denominator: 47 (definite-ok cases this checker ran on)
- ratio: {"ratio": 0.2128, "denominator": 47}

### unknown-rate
- count: 0
- denominator: 52 (cases run for this checker)
- ratio: {"ratio": 0.0, "denominator": 52}

### coverage
- count: 52
- denominator: 52 (cases run for this checker)
- ratio: {"ratio": 1.0, "denominator": 52}

### aggregate-accuracy
- correct (correct-accept + correct-reject): 41
- missed-breakage: 1; false-block: 10; unknown: 0
- denominator: 52 cases this checker ran on (5 oracle-break + 47 oracle-ok); aggregate is recorded alongside, never instead of, the separate metrics above
- ratio: {"ratio": 0.7885, "denominator": 52}

## checker: py_wild

### missed-breakage
- count: 4
- denominator: 5 (definite-break cases this checker ran on)
- ratio: {"ratio": 0.8, "denominator": 5}

### false-block
- count: 0
- denominator: 47 (definite-ok cases this checker ran on)
- ratio: {"ratio": 0.0, "denominator": 47}

### unknown-rate
- count: 0
- denominator: 52 (cases run for this checker)
- ratio: {"ratio": 0.0, "denominator": 52}

### coverage
- count: 52
- denominator: 52 (cases run for this checker)
- ratio: {"ratio": 1.0, "denominator": 52}

### aggregate-accuracy
- correct (correct-accept + correct-reject): 48
- missed-breakage: 4; false-block: 0; unknown: 0
- denominator: 52 cases this checker ran on (5 oracle-break + 47 oracle-ok); aggregate is recorded alongside, never instead of, the separate metrics above
- ratio: {"ratio": 0.9231, "denominator": 52}

## checker: wild

### missed-breakage
- count: 0
- denominator: 1 (definite-break cases this checker ran on)
- ratio: {"ratio": 0.0, "denominator": 1}

### false-block
- count: 0
- denominator: 3 (definite-ok cases this checker ran on)
- ratio: {"ratio": 0.0, "denominator": 3}

### unknown-rate
- count: 1
- denominator: 4 (cases run for this checker)
- ratio: {"ratio": 0.25, "denominator": 4}

### coverage
- count: 3
- denominator: 4 (cases run for this checker)
- ratio: {"ratio": 0.75, "denominator": 4}

### aggregate-accuracy
- correct (correct-accept + correct-reject): 3
- missed-breakage: 0; false-block: 0; unknown: 1
- denominator: 4 cases this checker ran on (1 oracle-break + 3 oracle-ok); aggregate is recorded alongside, never instead of, the separate metrics above
- ratio: {"ratio": 0.75, "denominator": 4}

## corpus-aggregate-accuracy (all checkers pooled)
- correct: 99
- missed-breakage: 6
- false-block: 14
- unknown: 1
- denominator: 120 checker×case runs (6 oracle-break + 50 oracle-ok pool cases × applicable checkers); 216 checker×case pairs skipped by ecosystem applicability and excluded from every denominator
- aggregate-accuracy: {"ratio": 0.8319, "denominator": 119} (correct / decided — unknown runs excluded from numerator and denominator and counted separately above)
- aggregate accuracy is recorded for wild-zfw; the per-checker separate metrics above remain the safety analysis

