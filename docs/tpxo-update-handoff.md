# Harmonica TPXO Update — Handoff

**From:** Alex Zundel (azundel@aquaveo.com)
**To:** Andrew Clark (aclark@aquaveo.com)
**Date:** 2026-07-08

Handing this project off to you. Goal: update the Harmonica tidal-database library so
SMS users can select the current OSU TPXO products (TPXO9-atlas-v5, TPXO10v2,
TPXO10-atlas-v2) and default to TPXO10-atlas.

---

## TL;DR

- **Phase A (harmonica 2.2.0) is DONE and pushed** — branch `master_update_tpxo`
  (HEAD `d49fedc`) on `Aquaveo/harmonica`, 21/21 tests, review-approved. **No PR opened yet.**
- **Phases B and C remain** (xmstides dialog wiring, then xmsdev_trunk pins + SMS smoke test).
- **The full design spec and implementation plan are on this branch** —
  `docs/2026-05-12-harmonica-tpxo-update-design.md` (304 lines) and
  `docs/2026-05-14-harmonica-tpxo-update-implementation.md` (1692 lines), copied from their
  canonical home in Alex's local-only `engineering-design-docs` repo. This handoff is a
  map/summary; those two are the detailed source of truth.
- **OSU TPXO data is now in hand** (Alex obtained it 2026-07-08) — the earlier data-access
  blocker is gone; all three models can be downloaded and tested end to end.

---

## Verified current state (2026-07-08)

- **harmonica:** `D:\quick\git\harmonica\`, branch `master_update_tpxo`, HEAD `d49fedc`
  ("Bump harmonica to 2.2.0"). Local HEAD == `origin/master_update_tpxo` (pushed).
  15 commits ahead of `master`. Working tree has only untracked `tests/*.out` artifacts,
  `.idea/`, and the `docs/` folder (this handoff + the Phase-0 doc).
- **PR:** none yet. Create via `https://github.com/Aquaveo/harmonica/pull/new/master_update_tpxo`
  or `gh pr create`.
- **xmstides:** not yet cloned (`https://github.com/Aquaveo/xmstides.git` → `D:\quick\git\xmstides\`).
- **xmsdev_trunk:** SVN. No harmonica-related changes committed yet.

---

## What's where

| Artifact | Status |
|---|---|
| `master_update_tpxo` branch (Phase A code + tests) | ✅ pushed, intact |
| `harmonica/docs/tpxo-update-phase0.md` (schema findings) | ✅ committed with this handoff |
| Design spec — `docs/2026-05-12-harmonica-tpxo-update-design.md` (304 lines) | ✅ copied onto this branch (canonical home: Alex's local-only `engineering-design-docs`) |
| Implementation plan — `docs/2026-05-14-harmonica-tpxo-update-implementation.md` (1692 lines) | ✅ copied onto this branch (same) |

Read spec §11 ("Phase 0 closure") and §12 ("Phase A implementation conventions") for the
reasoning behind the five TPXO resource classes; the plan has the full Task B1–B9 / C1–C4
breakdown. The summaries below are just a map into those documents.

---

## Phase 0 — schema findings (canonical)

Full table is in `docs/tpxo-update-phase0.md` (now on the branch). Summary:

- **TPXO9-atlas-v5** and **TPXO10-atlas-v2**: per-constituent files, 1/30°, 15 constituents
  each, int-millimeter storage (`units_multiplier=0.001`); data subdirs `tpxo9_atlas_v5` and
  `tpxo10_atlas_v2`.
- **TPXO10v2**: **consolidated** (single file `h_tpxo10.v2.nc`, NOT per-constituent — the
  original spec was wrong here and §11 corrected it), 1/6°, 25 constituents, double-meter
  storage (`units_multiplier=1.0`); data subdir `tpxo10v2`.
- All three reuse harmonica's existing variable names `lat_z`/`lon_z`/`hRe`/`hIm` — no
  per-resource var-name attribute needed.
- `Model_tpxo10v2.nc` is a 3-line legacy OTIS Fortran text manifest, not netCDF — ignore it
  in the loader.

---

## Phase A — what shipped (harmonica 2.2.0, 15 commits on `master_update_tpxo`)

| Commit | Task | Subject |
|---|---|---|
| `d8ceab7` | A1 | Add `is_consolidated_file` and `data_dir_name` resource attributes |
| `34e6f29` | A1 fix | Address review for `is_consolidated_file` refactor (`data_dir_exists`, etc.) |
| `c62c170` | A2 | Generalize TPXO loader to dispatch via `is_consolidated_file` |
| `38d4f01` | A3 | Add `Tpxo9AtlasResources` (TPXO9-atlas-v5) |
| `b8cb857` | A3 fix | Return list from `Tpxo9AtlasResources.available_constituents` |
| `f53eb1f` | A4 | Add `Tpxo10Resources` (TPXO10v2, consolidated) |
| `2acc215` | A4 fix | Inline comments on `Tpxo10Resources.resource_attributes` |
| `e32042a` | A5 | Add `Tpxo10AtlasResources` (TPXO10-atlas-v2) |
| `48b1139` | A5 | Inline comments on `Tpxo9AtlasResources.resource_attributes` |
| `0e6607c` | A6 | Change `DEFAULT_RESOURCE` to `tpxo10_atlas` |
| `3af7efe` | A6 doc | Update doc default-model reference |
| `84d8d91` | A7 | tpxo9_atlas integration test + `.base` fixture |
| `cd292ab` | A8 | tpxo10 integration test + `.base` fixture |
| `df888de` | A9 | tpxo10_atlas integration test + `.base` fixture |
| `d49fedc` | A10 | Bump to 2.2.0 (also fixes pre-existing setup.py/__init__.py version drift) |

**Verification:** 21/21 tests pass; coverage 81% with tox-style
`--omit harmonica/cli/*,harmonica/__main__.py`.

**M2 integration sanity baselines** (for future re-bless cycles):

| Location | tpxo9 | tpxo9_atlas | tpxo10 | tpxo10_atlas |
|---|---|---|---|---|
| NJ (39.74, -74.07) | 0.5220 | 0.4211 | 0.4890 | 0.4488 |
| MA (42.32, -70.0) | 1.1330 | 1.1408 | 1.1500 | 1.1607 |
| Bay of Fundy (45.44, -65.0) | 4.6500 | 4.0884 | 3.8889 | 4.0712 |
| OR (43.63, -124.55) | 0.8070 | 0.8151 | 0.7996 | 0.8113 |
| WA (46.18, -124.38) | 0.9040 | 0.8755 | 0.9075 | 0.8958 |

---

## What remains

### Immediate: dev-test Phase A, then open the PR
1. Dev-install local harmonica from `D:\quick\git\harmonica\` into the SMS Python and
   confirm the three new models resolve and extract correctly.
2. Open the PR on `Aquaveo/harmonica` for `master_update_tpxo`. Suggested title:
   *"Add TPXO9-atlas-v5, TPXO10v2, TPXO10-atlas-v2; bump to 2.2.0."*

### Phase B — xmstides 3.4.0 (9 tasks — summary; see implementation plan for full detail)
The SMS Tidal dialog is Python/PySide2 inside **xmstides**, not C++.
1. Clone `https://github.com/Aquaveo/xmstides.git` → `D:\quick\git\xmstides\`; branch `master_update_tpxo`.
2. Dev-install local harmonica 2.2.0 into the xmstides env.
3. Add three new dialog indexes + display strings. **Append only** — indexes persist into
   `tidal_comp.nc` as `info.attrs['source']`, so never insert/renumber:
   `TPX09_ATLAS_INDEX=6`, `TPX10_INDEX=7`, `TPX10_ATLAS_INDEX=8` in
   `xms/tides/data/tidal_data.py`. Display strings use `(1/6 deg)` / `(1/30 deg)` (ASCII —
   avoid the `°` glyph in PySide2 strings).
4. Extend the license-warning handling and the extractor dispatch for the new models.
5. Model-string switch to update: `_get_harmonica_model_string()` in
   `xms/tides/gui/tidal_dlg.py`.
6. Version bump to 3.4.0; final test pass; hand off.

### Phase C — xmsdev_trunk (4 tasks, SVN)
1. Bump `Dev/python_requirements.txt` (harmonica → 2.2.0, xmstides → 3.4.0).
2. Run `Dev/update_dev_python.bat` (or `update_conan` — see the XMS python-env notes; the pin
   is applied by the conan step, not update_dev_python alone).
3. Manual SMS smoke test of the Tidal dialog with the new models.
4. `svn add` / `svn commit` the pin change.

---

## Key design decisions (from spec §12)

- **`data_dir_name` resource attribute** (defaults to `None` → falls back to `self.model`):
  chosen over renaming the network-share subdirs (`tpxo9_atlas_v5` / `tpxo10v2` /
  `tpxo10_atlas_v2`) to match clean model names. Less data-store impact.
- **`data_dir_exists` must also honor `data_dir_name`** (review caught this on A1). Otherwise
  `available_models()` joins on `self.model` (e.g. `tpxo10`) instead of the real subdir
  (`tpxo10v2`) and reports installed models as "not installed."
- **`available_constituents()` return type:** list for per-constituent models, set for the
  consolidated one.
- **Ochi-Hubble / double-TMA note does NOT apply here** (that's the spectral project) — ignore.

---

## Gotchas / environment

- **tox is NOT on PATH.** Run tests with the SMS-bundled Python:
  `"D:/quick/xmsdev_trunk/Dev/SMS/APP/bin64/python/python.exe" -m pytest tests/test_harmonica.py -v`
  from the harmonica repo root (has pytest 9.0.3 + pytest-cov 7.1.0). Full suite ~270–420 s
  (atlas tests load 15 netCDF files each from `\\f\sms\tidal_databases\`).
- **`tests/*.out`** are produced by `_run_case()` every run and are NOT gitignored — they show
  as untracked; do **not** commit them. (Candidate housekeeping: add `tests/*.out` to `.gitignore`.)
- **Test fixture pattern:** `_run_case(model)` writes `<model>.out` and byte-compares against
  `<model>.base` (`filecmp.cmp`). Bless `.out` → `.base` once values look right.
- Aquaveo's harmonica fork was originally an ERDC repo (Kevin Winters); upstream untouched ~8
  years — Aquaveo can change it freely.

---

## Known follow-ups / out of scope

**Deferred bugs (pre-existing, don't block the PR):**
- `ResourceManager.data_dir_exists` empty-string guard gap: `os.path.join('', dir)` collapses
  to a relative path that `os.path.isdir` tests against cwd (was spec §12.5).
- `Tpxo9Resources.resource_attributes()` returns `'archive': 'gz'` though `url=None` (harmless;
  cosmetic inconsistency vs the new classes' explicit `archive: None`).

**Out of scope for this drop:**
- FES2014 → FES2022 (needs LIBES → PyFES rewrite per CNES).
- Currents/transports extraction (harmonica `get_components()` is elevation-only).
- TPXO9v5a (non-atlas) — same loader path as TPXO9-atlas-v5 if a need surfaces.
- ENPAC15 ADCIRC sibling; removing legacy TPXO8 / TPXO9v2.

---

*Questions on any of the above — ask Alex. The branch is the source of truth for what Phase A
actually does; this doc is the map.*
