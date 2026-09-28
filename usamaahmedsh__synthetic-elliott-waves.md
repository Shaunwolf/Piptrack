# usamaahmedsh/synthetic-elliott-waves (dataset)

```json
{
  "kind": "dataset",
  "id": "usamaahmedsh/synthetic-elliott-waves",
  "url": "https://huggingface.co/datasets/usamaahmedsh/synthetic-elliott-waves",
  "meta": {
    "tags": [
      "language:en",
      "license:mit",
      "size_categories:10M<n<100M",
      "format:parquet",
      "modality:tabular",
      "modality:text",
      "library:datasets",
      "library:dask",
      "library:polars",
      "library:mlcroissant",
      "region:us",
      "elliott-wave",
      "synthetic",
      "finance",
      "time-series",
      "wave-pattern",
      "technical-analysis"
    ],
    "downloads": 28,
    "likes": 0,
    "cardData": {
      "license": "mit",
      "language": [
        "en"
      ],
      "tags": [
        "elliott-wave",
        "synthetic",
        "finance",
        "time-series",
        "wave-pattern",
        "technical-analysis"
      ],
      "size_categories": [
        "100K<n<1M"
      ]
    },
    "lastModified": "2026-03-18T21:57:15.000Z",
    "gated": false,
    "private": false
  },
  "files": [
    {
      "path": "data",
      "size": 0,
      "type": "directory"
    },
    {
      "path": ".gitattributes",
      "size": 2504,
      "type": "file"
    },
    {
      "path": "README.md",
      "size": 1937,
      "type": "file"
    },
    {
      "path": "data/synthetic_elliott_waves.parquet",
      "size": 767951562,
      "type": "file"
    },
    {
      "path": "run_info.txt",
      "size": 436,
      "type": "file"
    },
    {
      "path": "synthetic_elliott_waves.parquet",
      "size": 767951562,
      "type": "file"
    }
  ],
  "splits": {
    "splits": [
      {
        "dataset": "usamaahmedsh/synthetic-elliott-waves",
        "config": "default",
        "split": "train"
      }
    ],
    "pending": [],
    "failed": []
  },
  "first_rows": [
    {
      "config": "default",
      "split": "train",
      "features": [
        {
          "feature_idx": 0,
          "name": "rule",
          "type": {
            "dtype": "large_string",
            "_type": "Value"
          }
        },
        {
          "feature_idx": 1,
          "name": "is_synthetic",
          "type": {
            "dtype": "bool",
            "_type": "Value"
          }
        },
        {
          "feature_idx": 2,
          "name": "label",
          "type": {
            "dtype": "int64",
            "_type": "Value"
          }
        },
        {
          "feature_idx": 3,
          "name": "ensemble_score",
          "type": {
            "dtype": "float64",
            "_type": "Value"
          }
        },
        {
          "feature_idx": 4,
          "name": "fib_score",
          "type": {
            "dtype": "float64",
            "_type": "Value"
          }
        },
        {
          "feature_idx": 5,
          "name": "wave_config",
          "type": {
            "dtype": "large_string",
            "_type": "Value"
          }
        },
        {
          "feature_idx": 6,
          "name": "geo_0",
          "type": {
            "dtype": "float64",
            "_type": "Value"
          }
        },
        {
          "feature_idx": 7,
          "name": "geo_1",
          "type": {
            "dtype": "float64",
            "_type": "Value"
          }
        },
        {
          "feature_idx": 8,
          "name": "geo_2",
          "type": {
            "dtype": "float64",
            "_type": "Value"
          }
        },
        {
          "feature_idx": 9,
          "name": "geo_3",
          "type": {
            "dtype": "float64",
            "_type": "Value"
          }
        },
        {
          "feature_idx": 10,
          "name": "geo_4",
          "type": {
            "dtype": "float64",
            "_type": "Value"
          }
        },
        {
          "feature_idx": 11,
          "name": "has_geo4",
          "type": {
            "dtype": "bool",
            "_type": "Value"
          }
        }
      ],
      "rows": [
        {
          "rule": "Corrective",
          "is_synthetic": false,
          "label": 1,
          "ensemble_score": 0.9308568965517241,
          "fib_score": 0.9,
          "wave_config": "[10, 8, 14]",
          "geo_0": 0.4677088908072245,
          "geo_1": 0.6939167592858771,
          "geo_2": 0.2284482758610843,
          "geo_3": 0.8706896551686608,
          "geo_4": -1.0,
          "has_geo4": false
        },
        {
          "rule": "Corrective",
          "is_synthetic": false,
          "label": 1,
          "ensemble_score": 0.8057010989010988,
          "fib_score": 0.7,
          "wave_config": "[11, 9, 12]",
          "geo_0": 0.5298558511821833,
          "geo_1": 0.7919754286649594,
          "geo_2": 2.8571428571114597,
          "geo_3": 3.1648351648003863,
          "geo_4": -1.0,
          "has_geo4": false
        },
        {
          "rule": "Corrective",
          "is_synthetic": false,
          "label": 1,
          "ensemble_score": 0.9366142857142857,
          "fib_score": 0.9,
          "wave_config": "[9, 10, 13]",
          "geo_0": 0.5392499848137602,
          "geo_1": 0.9191428719055172,
          "geo_2": 0.2345013477082628,
          "geo_3": 0.5202156334217785,
          "geo_4": -1.0,
          "has_geo4": false
        },
        {
          "rule": "Corrective",
          "is_synthetic": false,
          "label": 1,
          "ensemble_score": 0.8433050847457626,
          "fib_score": 0.7,
          "wave_config": "[10, 8, 14]",
          "geo_0": 0.45630794584348183,
          "geo_1": 0.8006366438202559,
          "geo_2": 0.36864406779504816,
          "geo_3": 0.4025423728796503,
          "geo_4": -1.0,
          "has_geo4": false
        },
        {
          "rule": "Corrective",
          "is_synthetic": false,
          "label": 1,
          "ensemble_score": 0.9306515901060071,
          "fib_score": 0.9,
          "wave_config": "[13, 5, 14]",
          "geo_0": 0.5295426362321735,
          "geo_1": 0.6770427879416882,
          "geo_2": 0.1448763250878273,
          "geo_3": 0.6678445229658381,
          "geo_4": -1.0,
          "has_geo4": false
        }
      ]
    }
  ]
}
```

## README

---
license: mit
language:
- en
tags:
- elliott-wave
- synthetic
- finance
- time-series
- wave-pattern
- technical-analysis
size_categories:
- 100K<n<1M
---

# Synthetic Elliott Wave Dataset

High-quality synthetic Elliott Wave patterns generated via rejection sampling
with Fibonacci-ratio constraints and multivariate-normal density scoring.

## Dataset Summary

| Field | Value |
|---|---|
| Total rows | 15,000,779 |
| Real patterns | 779 |
| Synthetic patterns | 15,000,000 |
| Wave types | Corrective, bearish_impulse, impulse |
| All label=1 (good) | Yes — all samples passed all 4 tiers |
| Run | `run_20260318_135833_t5000000` |

## Wave Type Counts

| rule | is_synthetic | count |
|---|---|---|
| Corrective | False | 729 |
| Corrective | True | 5,000,000 |
| bearish_impulse | False | 11 |
| bearish_impulse | True | 5,000,000 |
| impulse | False | 39 |
| impulse | True | 5,000,000 |

## Schema

| Column | Description |
|---|---|
| `rule` | Wave type: `Corrective`, `impulse`, `bearish_impulse` |
| `wave_config` | Wave config string |
| `geo_0..geo_4` | Geometry ratios (wave retracements / extensions) |
| `ensemble_score` | MVN-based quality score (≥0.80 for all synthetic rows) |
| `fib_score` | Fibonacci proximity score |
| `is_synthetic` | `True` for generated, `False` for real market patterns |
| `label` | `1` for all rows in this dataset (good samples only) |

## Generation

- **Tier 1**: Structural EW geometry constraints (wave ordering, direction)
- **Tier 1b**: Monotonicity / non-overlap checks
- **Tier 2**: Fibonacci ratio gates (tolerance per wave type)
- **Tier 3**: Multivariate-normal density score ≥ 0.80 vs real-data distribution
- **Tier 4**: BallTree diversity filter (min distance from existing samples)

## Related Dataset

For scorer training (good + bad samples): [`usamaahmedsh/elliott-wave-scorer-training`](https://huggingface.co/datasets/usamaahmedsh/elliott-wave-scorer-training)

