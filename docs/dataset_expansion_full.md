# Full dataset expansion

Dataset expansion is exposed through:

```bash
python -m neo_ange.cli expand max --target 1000 --skip-existing --resume
python -m neo_ange.cli expand coverage
python -m neo_ange.cli expand rebuild-all --target 1000
```

## Safe defaults

- Default target: 1000 objects.
- Minimum recommended objects: 300.
- Maximum safe default target: 3000.
- Batch size: 100.
- Checkpoint cadence: every 50 attempted objects.
- Request delay: 0.15 seconds by default.

## Discovery order

The max workflow combines SBDB Query, silver CAD, silver Sentry, bronze CAD, bronze Sentry, and curated
seeds. Sources are deduplicated with stable ordering. Missing local tables are warnings, not hard failures.

## Resume and manifests

Expansion writes batch manifests and `expansion_checkpoint_*.json` files under `reports/manifests`.
With `--resume`, successful objects from previous checkpoints are skipped.

## Readiness

`expand coverage` writes:

- `reports/data_quality/dataset_readiness.json`
- `reports/data_quality/dataset_readiness.md`

Readiness statuses are `not_ready`, `minimal`, `usable`, and `strong`.
