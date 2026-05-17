# Results layout (canonical vs historical)

This directory mixes **live thesis outputs**, **secondary diagnostics**, and **archived** material. Use this page so prose and links do not drift toward stale paths.

## Canonical layer (cite these for the thesis pipeline)

| Location | Role |
| -------- | ---- |
| `results/core/` | Headline Eq. 1 / Eq. 2 artifacts: `*_key_terms.csv`, `run_metadata_*.json`, `wiod_first_results_summary.csv`, manifests. |
| `results/tables/` | Combined regression tables from `code/core/18_wiod_academic_tables.py` (wild-bootstrap stars by default). |
| `results/figures/` | Thesis-ready figure PDF/PNG + table `.tex` / `.csv` bundle from [`code/core/21_wiod_thesis_figures_tables.py`](../code/core/21_wiod_thesis_figures_tables.py). Regeneration commands: **[figures/README.md](figures/README.md)**. |
| `results/secondary/inference_robustness/` | Optional cluster-stars variants of the same tables (appendix / comparison only). |
| `results/secondary/` | Eq. 2b estimates, decomposition, common-sample tables, jackknife, VIF audit, bootstrap audit, `robustness/` reruns, etc. |

After changing code or re-estimating, run:

```bash
uv run python code/secondary/_validate_artifacts.py
```

## Exploration outputs (feasibility / gate scripts)

Scripts under `code/exploration/wiod_feasibility/` write to **`results/exploration/wiod_feasibility/`** when executed (gate tables, VIFs for Eq. 2b support checks, trade cache, etc.).

A **fresh clone** may have an empty `results/exploration/` tree until you rerun those scripts. For **committed** copies of the same filenames (Europe matrix, gate bundle, trade panel), use:

- **`results/archive/exploration/wiod_feasibility/`** — documented in the archive [README](archive/exploration/wiod_feasibility/README.md).

## Dated snapshots (`results/_snapshot_YYYYMMDD/`)

Folders such as `results/_snapshot_20260515/` are **point-in-time** bundles (e.g. meetings, `--compare-snapshot` in the validator). They are **not** the day-to-day source of truth for writing-up coefficients — prefer **`results/core/`** and **`results/secondary/`** aligned with a current `wiod_first_results_summary.csv`.

Embedded timestamps inside copied `run_manifest.json` files may not match the folder date; treat the **files and coefficients** as the freeze, not the JSON `generated_at` field.

Over time these snapshots may be moved under `results/archive/`; if a doc links to `_snapshot_*`, treat that link as **historical** unless you refresh the snapshot.

## Archive and legacy

- **`results/archive/exploration/wiod_feasibility/`** — retained feasibility and Europe-candidate audits (not the minimal Eq. 1–2-only path).
- **`results/archive/legacy_migration_*`** — pre-cleanup output tree snapshot.

## Top-level briefs

- `RESULTS_BRIEF.md` — short headline summary (check dates vs `wiod_first_results_summary.csv`).
- `interpretation_memo.md` — thesis drafting “single source of truth” for claims; keep file pointers in the §6.x table aligned with this README.
