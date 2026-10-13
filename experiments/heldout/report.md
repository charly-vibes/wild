# Held-out evaluation report

This is validation of the value proposition, not evidence that the future v1 runtime has the prototype failure rates.

## execution-cost
- ci: 1.930075s measured (sum of per-run elapsed_seconds)
- ecosystem: 0.18326s measured (sum of per-run elapsed_seconds)
- host_ranges: 0.188305s measured (sum of per-run elapsed_seconds)
- wild: 0.517697s measured (sum of per-run elapsed_seconds)

## human-contract-maintenance-time
- intent-change: unavailable (basis: unavailable)
- migration-supplied: unavailable (basis: unavailable)
- platform-ineligibility: unavailable (basis: unavailable)
- transitive-addition: unavailable (basis: unavailable)
- unavailable entries are reported as null, never as fabricated zeros

## checker: ci

### missed-breakage
- count: 0
- denominator: 1 (definite-break cases)
- ratio: {"ratio": 0.0, "denominator": 1}

### false-block
- count: 1
- denominator: 3 (definite-ok cases)
- ratio: {"ratio": 0.3333, "denominator": 3}

### unknown-rate
- count: 0
- denominator: 4 (cases run for this checker)
- ratio: {"ratio": 0.0, "denominator": 4}

### coverage
- count: 4
- denominator: 4 (cases run for this checker)
- ratio: {"ratio": 1.0, "denominator": 4}

## checker: ecosystem

### missed-breakage
- count: 1
- denominator: 1 (definite-break cases)
- ratio: {"ratio": 1.0, "denominator": 1}

### false-block
- count: 1
- denominator: 3 (definite-ok cases)
- ratio: {"ratio": 0.3333, "denominator": 3}

### unknown-rate
- count: 0
- denominator: 4 (cases run for this checker)
- ratio: {"ratio": 0.0, "denominator": 4}

### coverage
- count: 4
- denominator: 4 (cases run for this checker)
- ratio: {"ratio": 1.0, "denominator": 4}

## checker: host_ranges

### missed-breakage
- count: 0
- denominator: 1 (definite-break cases)
- ratio: {"ratio": 0.0, "denominator": 1}

### false-block
- count: 2
- denominator: 3 (definite-ok cases)
- ratio: {"ratio": 0.6667, "denominator": 3}

### unknown-rate
- count: 0
- denominator: 4 (cases run for this checker)
- ratio: {"ratio": 0.0, "denominator": 4}

### coverage
- count: 4
- denominator: 4 (cases run for this checker)
- ratio: {"ratio": 1.0, "denominator": 4}

## checker: wild

### missed-breakage
- count: 0
- denominator: 1 (definite-break cases)
- ratio: {"ratio": 0.0, "denominator": 1}

### false-block
- count: 0
- denominator: 3 (definite-ok cases)
- ratio: {"ratio": 0.0, "denominator": 3}

### unknown-rate
- count: 1
- denominator: 4 (cases run for this checker)
- ratio: {"ratio": 0.25, "denominator": 4}

### coverage
- count: 3
- denominator: 4 (cases run for this checker)
- ratio: {"ratio": 0.75, "denominator": 4}

