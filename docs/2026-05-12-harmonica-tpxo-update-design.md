# Harmonica TPXO Update — Design Spec

**Date**: 2026-05-12
**Author**: azundel@aquaveo.com (drafted with Claude)
**Status**: Draft — pending implementation

## 1. Goal

Add TPXO9-atlas-v5, TPXO10, and TPXO10-atlas to harmonica, and expose them as selectable tidal databases in the SMS Tidal dialog. The TPXO data shipping with SMS today (TPXO8 and the legacy 3-file TPXO9v2) is two generations behind the current OSU releases.

## 2. Scope

### In scope
- New tidal database options selectable in SMS: TPXO9-atlas-v5, TPXO10v2 (1/6°), TPXO10-atlas-v2 (1/30°).
- Change harmonica's default model to `tpxo10_atlas`.
- Backward compatibility for existing TPXO8 / TPXO9v2 users and existing saved `tidal_comp.nc` files.

### TPXO9 v5 choice
The OSU site currently distributes two v5 products: `TPXO9v5a` (non-atlas, 1/30° global refinement of the original TPXO9) and `TPXO9-atlas-v5` (1/30° global solution with thirty 1/30° coastal patches blended in). This spec adds only `TPXO9-atlas-v5` (model name `tpxo9_atlas`), because the atlas variant supersedes the non-atlas variant for SMS's typical coastal use cases. Adding `TPXO9v5a` as a separate model can be a follow-up if a user need surfaces.

### Out of scope (separate future projects)
- FES2014 → FES2022 upgrade. Larger work: requires switching from harmonica's current LIBES-style interpolation to PyFES per CNES guidance.
- Adding ENPAC15 (ADCIRC Eastern North Pacific). Note: ADCIRC's published tidal databases (EC2015 for Western North Atlantic / Caribbean / Gulf of Mexico, ENPAC15 for Eastern Pacific) were reviewed during scoping; both are 2015-vintage and remain the current releases per `adcirc.org/products/adcirc-tidal-databases/`. harmonica's existing `adcirc2015` already matches the latest WNAT release, so no ADCIRC update is available. Adding ENPAC15 as a sibling model is a possible enhancement but is not a version upgrade and is not part of this project.
- Removing legacy TPXO8 / TPXO9v2. Will be done in a later cleanup once usage is confirmed dropped.
- Currents/transports support. Harmonica remains elevation-only.

### Non-goals
- No C++ changes in SMS. The Tidal dialog is implemented in Python (PySide2) inside the `xmstides` package; SMS C++ just launches it.

## 3. Success criteria

- A user in SMS can select "TPXO10-atlas" from the Tidal dialog, point harmonica at a valid data directory, and receive amplitude/phase results at chosen point locations.
- Existing project files containing `source = 3` (TPXO8) or `source = 4` (TPXO9v2) continue to load with their original models.
- Harmonica unit/integration tests pass, including a new test exercising the per-constituent loader against a sample TPXO10 file.

## 4. Background

### Current state (2026-05)
SMS ships harmonica 2.1.0 in each app's bundled Python (`Dev/{SMS,GMS,WMS}/APP/bin64/hidden.python/Lib/site-packages/harmonica`). Harmonica 2.1.0 supports five tidal models: `adcirc2015`, `leprovost`, `fes2014`, `tpxo8`, `tpxo9`. The `tpxo9` entry refers to the legacy 3-file TPXO9 (v1/v2) distribution.

The TPXO portion of harmonica is structured around per-model `Resources` subclasses in [`harmonica/resource.py`](https://github.com/Aquaveo/harmonica) and a single loader class `TpxoDB` in [`harmonica/tpxo_database.py`](https://github.com/Aquaveo/harmonica). The loader supports two code paths:
- **Multi-file path** (used by TPXO8): one netCDF file per constituent, looked up via `{CON: filename}` dict.
- **Consolidated-file path** (used by TPXO9v2): one netCDF holding all constituents stacked along a `con` dimension. Selected via hard-coded check `single_file = self.model == 'tpxo9'`.

The Aquaveo harmonica fork at `https://github.com/Aquaveo/harmonica` (default branch `master`, current version 2.1.0) is the source-of-truth repo for changes.

### Latest TPXO products
Per `tpxo.net/tpxo-products-and-registration` as of 2026-05:

| Product | Resolution | Domain | File layout |
|---|---|---|---|
| TPXO9v2 (legacy) | 1/6° | global | consolidated (3 files: grid + h + u,v) |
| TPXO9v5a | 1/30° | global | per-constituent |
| TPXO9-atlas-v5 | 1/30° atlas | global | per-constituent |
| **TPXO10v2 / v2a** | **1/6°** | **global** | **per-constituent** |
| **TPXO10-atlas-v2** | **1/30°** | **global** | **per-constituent** |

TPXO10 and TPXO10-atlas are both global — the atlas is the same global coverage at higher resolution, achieved by blending a 1/6° base with thirty 1/30° local coastal patches.

## 5. Architecture

### Affected repos

| Repo | Role | Changes |
|---|---|---|
| `Aquaveo/harmonica` | Core Python library | New `Resources` subclasses; loader generalization; version bump 2.1.0 → 2.2.0 |
| `Aquaveo/xmstides` | SMS Python wrapper / Qt dialog | New index constants; combobox additions; harmonica model-string mappings; version bump 3.3.0 → 3.4.0 |
| `xmsdev_trunk` (SVN) | SMS build/distribution | Update `python_requirements.txt` / Conan references to pull new harmonica + xmstides versions |

### Repo 1 — `Aquaveo/harmonica`

#### `harmonica/resource.py`

Add three new `Resources` subclasses, each following the existing `Tpxo8Resources` shape:

| New class | Model name | Resolution | Constituents (to be confirmed in Phase 0) | File pattern (best guess, confirm in Phase 0) |
|---|---|---|---|---|
| `Tpxo9AtlasResources` | `tpxo9_atlas` | 1/30° | 15 existing + v5 additions | `h_<con>_tpxo9_atlas_30_v5.nc` |
| `Tpxo10Resources` | `tpxo10` | 1/6° | 17 (8 primary + 2 LP + 3 NL + 2N2 + S1 + 2 minor) | `h_<con>_tpxo10_v2.nc` |
| `Tpxo10AtlasResources` | `tpxo10_atlas` | 1/30° | same 17 | `h_<con>_tpxo10_atlas_v2.nc` |

Each subclass implements:
- `available_constituents()` — returns the constituent list
- `constituent_groups()` — returns `[group]` lists; mirrors any resolution-tier splits the actual data uses (TPXO8 splits 9 primary cons at 1/30° from 4 long-period cons at 1/6° — TPXO10 grouping to be confirmed in Phase 0)
- `constituent_resource(con)` — maps constituent name to filename
- `resource_attributes()` — `url=None` (licensed, same as TPXO8/9 today), `archive=None`
- `dataset_attributes()` — at minimum `units_multiplier`
- New flag `is_consolidated_file = False` (see loader change below)

#### `harmonica/tpxo_database.py`

Generalize the loader to remove the hard-coded model-name check at [tpxo_database.py:61](https://github.com/Aquaveo/harmonica/blob/master/harmonica/tpxo_database.py#L61):

```python
# Before
single_file = self.model == 'tpxo9'

# After
single_file = getattr(self.resources, 'is_consolidated_file', False)
```

`Tpxo9Resources` overrides `is_consolidated_file = True`; all other resource classes leave the default `False`. The per-constituent code path is already exercised by TPXO8 and works unchanged for the three new models.

If Phase 0 reveals that TPXO10's netCDF schema renames the variables harmonica reads (`lat_z`, `lon_z`, `hRe`, `hIm`), add per-resource var-name attributes (e.g. `lat_var`, `lon_var`, `h_re_var`, `h_im_var`) consumed by the loader. If the names match TPXO8's, no further loader changes are needed.

#### `ResourceManager`

In `harmonica/resource.py`, update the registry:

```python
RESOURCES = {
    'tpxo8': Tpxo8Resources(),
    'tpxo9': Tpxo9Resources(),
    'tpxo9_atlas': Tpxo9AtlasResources(),   # new
    'tpxo10': Tpxo10Resources(),            # new
    'tpxo10_atlas': Tpxo10AtlasResources(), # new
    'leprovost': LeProvostResources(),
    'fes2014': FES2014Resources(),
    'adcirc2015': Adcirc2015Resources(),
}
TPXO_MODELS = {'tpxo8', 'tpxo9', 'tpxo9_atlas', 'tpxo10', 'tpxo10_atlas'}
DEFAULT_RESOURCE = 'tpxo10_atlas'  # was 'tpxo9'
```

### Repo 2 — `Aquaveo/xmstides`

#### `xms/tides/data/tidal_data.py`

Append new index constants. **Do not reorder or insert**, because the integer index is persisted into `tidal_comp.nc` as `info.attrs['source']` ([tidal_data.py:144](Dev/GMS/APP/bin64/hidden.python/Lib/site-packages/xms/tides/data/tidal_data.py#L144)).

```python
ADCIRC_INDEX = 0
LEPROVOST_INDEX = 1
FES2014_INDEX = 2
TPX08_INDEX = 3
TPX09_INDEX = 4
USER_DEFINED_INDEX = 5
TPX09_ATLAS_INDEX = 6   # new
TPX10_INDEX = 7         # new
TPX10_ATLAS_INDEX = 8   # new
```

`TDB_SOURCES` gains three appended display strings in the same order:

```python
TDB_SOURCES = [
    'ADCIRC2015',
    'LeProvost',
    'FES2014',
    'TPXO8',
    'TPXO9',
    'User defined',
    'TPXO9-atlas (v5)',
    'TPXO10 (1/6°)',
    'TPXO10-atlas (1/30°)',
]
```

#### `xms/tides/gui/tidal_dlg.py`

Extend `_get_harmonica_model_string()` ([tidal_dlg.py:180](Dev/GMS/APP/bin64/hidden.python/Lib/site-packages/xms/tides/gui/tidal_dlg.py#L180)) with the three new mappings.

Extend the license-warning check at [tidal_dlg.py:103](Dev/GMS/APP/bin64/hidden.python/Lib/site-packages/xms/tides/gui/tidal_dlg.py#L103) — all three new models are licensed (no free distribution URL), so they need the same "license required" red-text treatment as TPXO8/9/FES2014.

#### `xms/tides/data/tidal_extractor.py`

Extend the source-to-harmonica-model dispatch ([tidal_extractor.py:45](Dev/GMS/APP/bin64/hidden.python/Lib/site-packages/xms/tides/data/tidal_extractor.py#L45)) with the three new cases.

### Repo 3 — `xmsdev_trunk` (SVN)

- Update `Dev/python_requirements.txt` (or whichever requirements file the dev install workflow consumes) to pull harmonica 2.2.0 and xmstides 3.4.0.
- Refresh each app's bundled Python via `Dev/update_dev_python.bat`.
- No C++ source changes.

## 6. Data flow

```
SMS C++ launches Python Tidal dialog
  └─ tidal_dlg.py:  user picks "TPXO10-atlas" → index 8
        └─ _get_harmonica_model_string(8) → "tpxo10_atlas"
            └─ harmonica.Constituents("tpxo10_atlas")
                └─ ResourceManager → Tpxo10AtlasResources
                    └─ get_datasets([cons]) → xr.open_dataset(h_<con>_tpxo10_atlas_v2.nc)
                        └─ TpxoDB.get_components(locs, cons)
                            └─ bilinear interp of (hRe, hIm) at (lat, lon)
                                → DataFrame(amplitude, phase, speed) per location
```

Saved project files store index 8 in `info.attrs['source']`. Older files with `source ∈ {0..5}` continue to resolve to their original models because the existing indices are unchanged.

## 7. Phase 0 — verify-before-coding

Before writing the new resource classes, verify against one real downloaded constituent file from each of the three new products:

1. **NetCDF variable names**. Harmonica reads `lat_z`, `lon_z`, `hRe`, `hIm`. OSU notes their format "is different from TMD3 consolidated netcdf format" — verify whether these names match TPXO8's pattern, and add per-resource var-name attributes if they don't.
2. **Exact filename convention** for TPXO9-atlas-v5 / TPXO10v2 / TPXO10-atlas-v2. Best guesses above are derived from v1 conventions; we need a directory listing from a real download.
3. **Constituent grouping**. TPXO8 splits constituents into a 1/30° group (9 cons) and a 1/6° group (4 long-period cons), each with its own file resolution. Determine whether TPXO10 follows the same split or stores all constituents at a uniform resolution.
4. **Exact constituent list per product**. Confirm the names for the 17 advertised TPXO10 constituents.

Output of Phase 0: a small markdown note (committed to harmonica repo) recording the verified filenames, variable names, and constituent lists. This note feeds directly into the resource-class implementation.

## 8. Testing

- Test framework follows existing harmonica conventions (to be confirmed once repo is cloned).
- Per-model integration test: a small sample file (one constituent, ~tens of MB) fixture per new model, comparing interpolated amplitude/phase at a handful of named tide-gauge locations against a reference. Use the existing TPXO8 test as the template.
- Unit test for the `is_consolidated_file` attribute: confirm `Tpxo9Resources` returns `True`, all others return `False`, and the legacy `tpxo9` model still loads from a consolidated file.
- Smoke test from the xmstides side: open the Tidal dialog with each new model selected, confirm the constituent list populates correctly, save and reload a project file containing each new `source` index.

## 9. Release plan

1. **Phase 0** — download sample data, verify schema/filenames/constituents, commit notes.
2. **Harmonica 2.2.0** — implement, test, release.
3. **xmstides 3.4.0** — implement, test, release. Depends on harmonica 2.2.0.
4. **xmsdev_trunk** — bump requirements; rerun `update_dev_python.bat`; commit via SVN per existing workflow.

Each step is independently mergeable. Bottom-up follows the same dev-install pattern Aquaveo uses for other xms-* packages.

## 10. Open questions deferred to implementation plan

- Exact test data hosting strategy (private S3? Shared drive?) for licensed sample files used in CI.
- Whether to keep the `Tpxo9Resources` class with the consolidated-file path under a new alias (e.g. `tpxo9_legacy`) before removal in the next major release.

## 11. Phase 0 closure (2026-05-14)

Phase 0 verification is complete. OSU approved Aquaveo non-commercial use on 2026-05-14 and provided the netCDF distributions for all three new products. Full sample data sits at `\\f\sms\tidal_databases\{tpxo9_atlas_v5,tpxo10v2,tpxo10_atlas_v2}\`.

**Verified findings** are in the harmonica repo at `docs/tpxo-update-phase0.md` — that note is the canonical reference for the implementation plan.

**Corrections to this spec** surfaced by Phase 0:

- **TPXO10v2 is consolidated, not per-constituent.** Single file (`h_tpxo10.v2.nc`) holding all 25 constituents stacked on an `nc` dim, same internal layout as the legacy TPXO9v2. The §4 table row and the §5 `Tpxo10Resources` entry should be read as consolidated. The loader's `is_consolidated_file` flag is `True` for this resource.
- **Filename guesses were partially wrong.** Actual patterns: `h_tpxo10.v2.nc` (dot, not underscore, between `tpxo10` and `v2`); `h_<con>_tpxo9_atlas_30_v5.nc`; `h_<con>_tpxo10_atlas_30_v2.nc` (the `_30_` segment encoding 1/30° resolution was not in the §5 guesses).
- **Constituent counts.** TPXO10v2: 25 cons. Both atlases: 15 cons (same set as the legacy TPXO9). The "17 advertised TPXO10 constituents" figure in §5 was wrong.
- **Variable names match.** All three new products use `lat_z` / `lon_z` / `hRe` / `hIm`, the same names harmonica's loader already reads. The §5 contingency for per-resource var-name attributes is moot.
- **Unit multipliers.** Atlases: `0.001` (int mm storage). TPXO10v2: `1.0` (double m storage).

**Spec sections that remain correct as written**: §5 loader-change pattern (`is_consolidated_file` attribute), §5 ResourceManager registry sketch, §6 data flow diagram, §7 phase plan, §8 testing approach, §9 release sequence.

**Status**: ready for Phase 1 (implementation plan via writing-plans skill, then execution via executing-plans skill).

## 12. Phase A implementation conventions (2026-05-15)

Decisions surfaced during Phase A execution that weren't in the original §5 architecture and are now baked into the shipped code. Documented here so the next person adding a TPXO resource class (e.g., `TPXO9v5a` non-atlas, future TPXO11) doesn't re-derive them.

### 12.1 `data_dir_name` resource attribute (alongside `is_consolidated_file`)

The original §5 architecture assumed every model's data directory under `config['pre_existing_data_dir']` would be named identically to its harmonica model key. Reality: the new OSU distributions live in version-suffixed subdirectories on `\\f\sms\tidal_databases\`:

| Model key | On-disk subdir |
|---|---|
| `tpxo9_atlas` | `tpxo9_atlas_v5` |
| `tpxo10` | `tpxo10v2` |
| `tpxo10_atlas` | `tpxo10_atlas_v2` |

Two options were considered:

1. **Rename the share subdirs** to match model keys. Rejected — requires admin op on a shared network resource and would break any other tool relying on the OSU-canonical naming.
2. **Add a `data_dir_name` attribute on each Resources subclass** that, when set, overrides the model-key default in path joins. Chosen — additive, backward-compatible (existing models inherit `None` and continue using `self.model`), and matches the principle that the harmonica model key is a stable identity separate from the on-disk version-suffixed directory name.

Implementation: class attribute on `Resources` base (defaults `None`); five sites in `ResourceManager` resolve `self.model_atts.data_dir_name or self.model` before joining: `get_datasets` (two sites), `download_model`, `remove_model`, `data_dir_exists`.

**Future work hook**: when bumping a TPXO model to a new on-disk version (e.g., when a TPXO10-atlas-v3 ships and replaces v2), update `Tpxo10AtlasResources.data_dir_name = 'tpxo10_atlas_v3'` rather than changing the harmonica model key. Existing saved `tidal_comp.nc` files store the integer source index from xmstides — the harmonica model key is the bridge between that integer and the data location, so it must remain stable.

### 12.2 `data_dir_exists` must do a registry lookup

`ResourceManager.data_dir_exists(model)` is a `@staticmethod` that takes a plain model-key string (it's called from `available_models()` before any `ResourceManager` instance exists). Because it can't reach `self.model_atts`, it does a registry lookup directly:

```python
resource = ResourceManager.RESOURCES.get(model)
data_dir = (resource.data_dir_name if resource is not None else None) or model
```

This was originally missed in §5 — the §5 loader-generalization sketch covered `get_datasets` but not the availability-check path. Caught by code review of Task A1. The bug it would have introduced: `available_models()` would silently report new models as "not installed" because it joined on the model key (`'tpxo10'`) instead of the actual subdir (`'tpxo10v2'`). Now fixed.

### 12.3 `available_constituents()` return type by peer class

The base class `Resources.available_constituents` abstract returns `[]` (suggesting list semantics), but the existing concrete classes are inconsistent:
- `Tpxo8Resources`: returns a `list` (flattened from grouped dicts)
- `Tpxo9Resources`: returns the underlying `set`
- `FES2014Resources`: returns `dict_keys`
- `LeProvostResources`, `Adcirc2015Resources`: return underlying `set`

Convention adopted in Phase A:
- **Per-constituent classes** (file-per-con dict): return `list(self.<DICT>.keys())`. Matches `Tpxo8Resources`. Applied to `Tpxo9AtlasResources` and `Tpxo10AtlasResources`.
- **Consolidated classes** (single-file, set of supported cons): return the underlying `set` directly. Matches `Tpxo9Resources`. Applied to `Tpxo10Resources`.

All downstream callers tolerate either type (`in` testing, `set(constituents) & set(group)`), so this is a maintainability/predictability choice rather than a correctness one. `FES2014Resources` remains inconsistent (still returns `dict_keys`) — pre-existing gap, not retroactively fixed.

### 12.4 Inline comments on `resource_attributes` license/archive fields

For every licensed resource class (`Tpxo8`, `Tpxo9`, `Tpxo9Atlas`, `Tpxo10`, `Tpxo10Atlas`), `resource_attributes` returns `{'url': None, 'archive': ...}` with inline comments:

```python
'url': None,  # Resources must already exist. Licensing restrictions prevent hosting files.
'archive': None,  # OSU ships TPXO<version> as a plain directory; no archive wrapper.
```

The `url=None` comment is pre-existing from `Tpxo8Resources` / `Tpxo9Resources`. The `archive` comment was added in Phase A — Phase A's new OSU products arrive as plain directories on the network share, not `.tar.gz` (which `Tpxo9Resources` still uses, marked `'archive': 'gz'`). The comment documents the per-product packaging convention so a future contributor doesn't need to dig into `ResourceManager.download` to understand why `archive=None` means "extract directly" vs. `archive='gz'` means "untar".

### 12.5 Pre-existing gap noted but deferred: `data_dir_exists` empty-string guard

`data_dir_exists` calls `os.path.join(config['pre_existing_data_dir'], data_dir)`. When `pre_existing_data_dir` is the empty-string default (set in `harmonica/__init__.py`), `os.path.join('', dir)` collapses to a bare relative path, and `os.path.isdir` then tests it against the process cwd. If the process happens to be run from a directory containing a folder with that name, `data_dir_exists` spuriously returns `True`.

This bug predates Phase A — pre-A code at `resource.py:419` of master had the same shape. Phase A preserved the behavior faithfully through the `data_dir_name` refactor. **Track as a separate follow-up** rather than expanding Phase A scope. The `get_datasets` path guards correctly (`if config['pre_existing_data_dir']:`) so end-to-end extraction is safe; only the availability-check predicate is affected.
