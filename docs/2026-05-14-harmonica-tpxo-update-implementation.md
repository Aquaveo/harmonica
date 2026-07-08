# Harmonica TPXO Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add TPXO9-atlas-v5, TPXO10v2, and TPXO10-atlas-v2 as selectable tidal databases in SMS, with `tpxo10_atlas` as the new harmonica default. Backward compatibility for existing TPXO8 / TPXO9v2 users is preserved.

**Architecture:** Three sequential repo deliveries — bottom up. (A) Harmonica gains three new `Resources` subclasses plus a tiny loader generalization (`is_consolidated_file` resource attribute replacing hardcoded model check). (B) xmstides gains three appended dialog indexes, three display strings, three loader-dispatch cases, and three license-warning entries. (C) xmsdev_trunk bumps Python requirements and rebuilds the bundled SMS Python.

**Tech Stack:** Python 3.10, pytest + tox (test framework), netCDF4 + xarray (file I/O), pandas (DataFrame output). harmonica fork at `https://github.com/Aquaveo/harmonica` (git). xmstides at `https://github.com/Aquaveo/xmstides` (git). xmsdev_trunk in SVN. PySide2 for the SMS Tidal dialog.

**Companion documents:**
- Design spec: `docs/superpowers/specs/2026-05-12-harmonica-tpxo-update-design.md`
- Phase 0 schema findings: `D:\quick\git\harmonica\docs\tpxo-update-phase0.md`

**Reference memory:**
- `dev_install_workflow.md` — how to swap a released Python library for a dev install from `D:\quick\git\` into the SMS Python environment.
- `feedback_svn_add_reminder.md` — for xmsdev_trunk changes: stage changes (incl. `svn add`), then hand off to user for build + commit; do NOT run `svn commit` or build batch files directly.
- `xmstool_practices.md` — branch naming conventions if needed (not strictly applicable here but useful for cross-reference).

---

## File structure

### Phase A — harmonica (git, `D:\quick\git\harmonica\`, branch `master_update_tpxo`)

| Path | Role | Action |
|---|---|---|
| `harmonica/resource.py` | Resource registry + per-model classes | Modify: add 3 new classes; add `is_consolidated_file` + `data_dir_name` attrs; update registry; change `DEFAULT_RESOURCE`; tweak path-join to honor `data_dir_name`. |
| `harmonica/tpxo_database.py` | TPXO loader | Modify: replace hardcoded `single_file = self.model == 'tpxo9'` with attribute lookup. |
| `harmonica/__init__.py` | Package init / version | Modify: bump `__version__` from `2.0.1` to `2.2.0` (fixes existing drift; was out of sync with setup.py's `2.1.0`). |
| `setup.py` | Package metadata | Modify: bump `version` from `2.1.0` to `2.2.0`. |
| `tests/test_harmonica.py` | Test class | Modify: add tests for three new models + a unit test for the loader's `is_consolidated_file` dispatch. |
| `tests/tpxo9_atlas.base` | Regression fixture | Create: blessed `.out` from first successful integration run. |
| `tests/tpxo10.base` | Regression fixture | Create: blessed `.out`. |
| `tests/tpxo10_atlas.base` | Regression fixture | Create: blessed `.out`. |

### Phase B — xmstides (git, `D:\quick\git\xmstides\`, branch `master_update_tpxo`)

| Path | Role | Action |
|---|---|---|
| `xms/tides/data/tidal_data.py` | Dialog index constants + display strings | Modify: append three new indexes + three new entries in `TDB_SOURCES`. |
| `xms/tides/gui/tidal_dlg.py` | Tidal dialog | Modify: extend `_get_harmonica_model_string()` with three new cases; extend license-warning check with three new licensed models. |
| `xms/tides/data/tidal_extractor.py` | Source-to-harmonica dispatch | Modify: add three new source→model cases. |
| `tests/...` (location TBD by repo layout) | Unit tests | Modify or create: round-trip tests for each new source index. |
| `setup.py` (or equivalent version location) | Version metadata | Modify: 3.3.0 → 3.4.0. |

### Phase C — xmsdev_trunk (SVN, `D:\quick\xmsdev_trunk\`)

| Path | Role | Action |
|---|---|---|
| `Dev/python_requirements.txt` | SMS Python requirements pin | Modify: bump harmonica → 2.2.0 and xmstides → 3.4.0. |
| (no source changes) | | |

---

# Phase A — Harmonica 2.2.0

**Status (2026-05-15): Implemented and pushed** — branch `master_update_tpxo` at HEAD `d49fedc`, pushed to `origin` on `Aquaveo/harmonica`. 15 commits, 21/21 tests passing, 81% coverage. PR not opened yet (user is dev-testing locally first). Implementation conventions surfaced during execution are captured in spec §12.

Working tree: `D:\quick\git\harmonica\`, on branch `master_update_tpxo`.

## Task A1: Add `is_consolidated_file` + `data_dir_name` attributes to existing resource classes

Establishes the per-resource attributes the loader will read in Task A2. Touches existing classes only; no new models yet.

**Files:**
- Modify: `harmonica/resource.py` (existing `Tpxo8Resources`, `Tpxo9Resources` classes; `ResourceManager.get_datasets` path join)
- Test: `tests/test_harmonica.py`

- [ ] **Step 1: Write failing unit test for the resource-attribute pattern**

Add to `tests/test_harmonica.py` (inside `class TestHarmonica`, after the existing tests):

```python
def test_resource_is_consolidated_file_flags(self):
    """Each TPXO resource declares whether its data is consolidated into one file."""
    from harmonica.resource import (
        ResourceManager, Tpxo8Resources, Tpxo9Resources,
    )
    assert Tpxo8Resources().is_consolidated_file is False
    assert Tpxo9Resources().is_consolidated_file is True

def test_resource_data_dir_name_defaults_to_none(self):
    """data_dir_name defaults to None so existing models keep using self.model as dir."""
    from harmonica.resource import Tpxo8Resources, Tpxo9Resources
    assert getattr(Tpxo8Resources(), 'data_dir_name', None) is None
    assert getattr(Tpxo9Resources(), 'data_dir_name', None) is None
```

- [ ] **Step 2: Run the new tests; verify they fail**

```
cd D:\quick\git\harmonica
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_resource_is_consolidated_file_flags tests/test_harmonica.py::TestHarmonica::test_resource_data_dir_name_defaults_to_none -v
```

Expected: FAIL with `AttributeError: 'Tpxo8Resources' object has no attribute 'is_consolidated_file'` (or similar). The `data_dir_name` test should pass because of `getattr(..., None)` — that's intentional, it documents the default behavior.

- [ ] **Step 3: Add `is_consolidated_file = False` to the base `Resources` class**

In `harmonica/resource.py`, modify the base `Resources` class (around line 22):

```python
class Resources(object):
    """Abstract base class for model resources."""

    # Default: data is one file per constituent. Override to True for single-file models.
    is_consolidated_file = False
    # Default: data subdirectory under pre_existing_data_dir matches the model name.
    # Override (e.g. 'tpxo9_atlas_v5') when the on-disk dir is version-suffixed.
    data_dir_name = None

    def __init__(self):
        """Base constructor."""
        pass
```

- [ ] **Step 4: Override `is_consolidated_file = True` on `Tpxo9Resources` only**

In `harmonica/resource.py`, in `Tpxo9Resources` (around line 142), after `TPXO9_CONS`:

```python
class Tpxo9Resources(Resources):
    """TPXO9 resources."""
    TPXO9_CONS = {'2N2', 'K1', 'K2', 'M2', 'M4', 'MF', 'MM', 'MN4', 'MS4', 'N2', 'O1', 'P1', 'Q1', 'S1', 'S2'}
    DEFAULT_RESOURCE_FILE = 'tpxo9_netcdf/h_tpxo9.v1.nc'
    is_consolidated_file = True
```

`Tpxo8Resources` inherits `is_consolidated_file = False` from the base — no change needed.

- [ ] **Step 5: Run the same unit tests; verify they pass**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_resource_is_consolidated_file_flags tests/test_harmonica.py::TestHarmonica::test_resource_data_dir_name_defaults_to_none -v
```

Expected: PASS for both.

- [ ] **Step 6: Update `ResourceManager.get_datasets` to honor `data_dir_name`**

In `harmonica/resource.py`, in `ResourceManager.get_datasets()` (around line 535-547), replace the two path-join sites that use `self.model` as the directory name:

```python
# Around line 537 — replace:
#     path = os.path.join(config['pre_existing_data_dir'], self.model, r)
# with:
data_dir = self.model_atts.data_dir_name or self.model
path = os.path.join(config['pre_existing_data_dir'], data_dir, r)

# And around line 547 — replace:
#     resource_dir = os.path.join(config['data_dir'], self.model)
# with:
data_dir = self.model_atts.data_dir_name or self.model
resource_dir = os.path.join(config['data_dir'], data_dir)
```

Also update `ResourceManager.download_model` at the top of the method (around line 499) and `ResourceManager.remove_model` (around line 508) for consistency — they also build paths using `self.model`:

```python
# In download_model, replace:
#     resource_dir = os.path.join(config['data_dir'], self.model)
# with:
data_dir = self.model_atts.data_dir_name or self.model
resource_dir = os.path.join(config['data_dir'], data_dir)

# In remove_model, replace:
#     resource_dir = os.path.join(config['data_dir'], self.model)
# with:
data_dir = self.model_atts.data_dir_name or self.model
resource_dir = os.path.join(config['data_dir'], data_dir)
```

**Also update `ResourceManager.data_dir_exists`** (around line 416, the `@staticmethod`). It takes a plain `model` string argument and is called from `available_models` (line 441) before any `ResourceManager` instance exists, so it cannot read `self.model_atts`. Instead, look up the resource class from the registry:

```python
# Replace the existing body:
@staticmethod
def data_dir_exists(model):
    """..."""
    resource = ResourceManager.RESOURCES.get(model)
    data_dir = (resource.data_dir_name if resource else None) or model
    if os.path.isdir(os.path.join(config['data_dir'], data_dir)):
        return True
    if os.path.isdir(os.path.join(config['pre_existing_data_dir'], data_dir)):
        return True
    return False
```

Why this matters: `available_models()` builds the dict-of-flags `{model: data_dir_exists(model)}` consumed by the Tidal dialog. If we skip this update, then any new resource class with a non-`None` `data_dir_name` (e.g. `Tpxo10Resources` with `'tpxo10v2'`) will show "not installed" even when its data is present, because `data_dir_exists` would look under `<share>\tpxo10\` instead of `<share>\tpxo10v2\`. The bug surfaces only once Task A4 lands new models with `data_dir_name` set, but it's cheaper to fix here while the refactor scope is small.

- [ ] **Step 7: Run the full existing test suite to confirm no regression**

```
tox -e py310
```

Expected: All existing tests still pass (TPXO8, TPXO9, ADCIRC, LeProvost, FES2014, the nodal-factor tests). Coverage report prints at the end. If `test_tpxo8` or `test_tpxo9` fails, the path-join change broke something — re-inspect.

- [ ] **Step 8: Commit (user-owned, see workflow note)**

Per `feedback_svn_add_reminder.md` for SVN and equivalent care for git: review the diff, then commit yourself. Suggested message:

```
Add is_consolidated_file and data_dir_name resource attributes

Replaces the per-resource convention of hardcoding model-specific behavior in
the loader with explicit attributes on each Resources subclass. Prep for
adding TPXO9-atlas, TPXO10, TPXO10-atlas models.
```

---

## Task A2: Generalize `TpxoDB.get_components()` to use the new resource attribute

Removes the hardcoded `self.model == 'tpxo9'` check in favor of the resource attribute introduced in Task A1. Functional behavior unchanged for existing models.

**Files:**
- Modify: `harmonica/tpxo_database.py` (line 61)
- Test: `tests/test_harmonica.py`

- [ ] **Step 1: Write a unit test that the loader dispatches on the resource attribute**

Add to `tests/test_harmonica.py`:

```python
def test_loader_dispatches_on_is_consolidated_file(self):
    """The TPXO loader chooses its file path based on resource attribute, not model name."""
    from harmonica.tidal_constituents import Constituents
    # The legacy tpxo9 model is consolidated and must still resolve correctly.
    c = Constituents()
    df_list = c.get_components(self.LOCS, self.CONS, True, 'tpxo9')
    assert len(df_list.data) == len(self.LOCS)
    # TPXO8 is per-constituent and must continue to work too.
    c2 = Constituents()
    df_list2 = c2.get_components(self.LOCS, self.CONS, True, 'tpxo8')
    assert len(df_list2.data) == len(self.LOCS)
```

This test exercises both code paths end-to-end. It's an integration test (reads the network share) but serves as the safety check that the generalization didn't break either path.

- [ ] **Step 2: Run the new test; expect it to currently pass (we haven't changed the loader yet)**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_loader_dispatches_on_is_consolidated_file -v
```

Expected: PASS. The test will be a regression guard once we change the loader.

- [ ] **Step 3: Modify the loader**

In `harmonica/tpxo_database.py`, replace line 61:

```python
# Before:
single_file = self.model == 'tpxo9'

# After:
single_file = self.resources.model_atts.is_consolidated_file
```

Note: `self.resources` here is the `ResourceManager` (set up in `TidalDB.__init__`). The model-specific Resources object is `self.resources.model_atts`. (Confirm by reading the parent `TidalDB.__init__` in `harmonica/tidal_database.py`; if the attribute path differs, adjust accordingly.)

- [ ] **Step 4: Run the test again; expect it to still pass**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_loader_dispatches_on_is_consolidated_file -v
```

Expected: PASS. Both TPXO9 (consolidated path) and TPXO8 (per-con path) must work.

- [ ] **Step 5: Run the full suite as a safety net**

```
tox -e py310
```

Expected: All existing tests pass. If TPXO9 fails, the `self.resources.model_atts.is_consolidated_file` reference is wrong; inspect the actual ResourceManager → Resources access path and fix.

- [ ] **Step 6: Commit**

Suggested message:

```
Generalize TPXO loader to dispatch via is_consolidated_file attribute

Removes the hardcoded `self.model == 'tpxo9'` check. Each TPXO resource
declares whether its data is stored in one consolidated netCDF (TPXO9-style,
all constituents stacked on the `nc` dim) or one file per constituent
(TPXO8-style).
```

---

## Task A3: Add `Tpxo9AtlasResources` class

Adds the first of three new model resource classes. Per-constituent layout (15 cons), 1/30° grid, int millimeter storage, data subdir `tpxo9_atlas_v5`.

**Files:**
- Modify: `harmonica/resource.py` (new class + registry entry + `TPXO_MODELS` set entry)
- Test: `tests/test_harmonica.py`

- [ ] **Step 1: Write failing unit tests for the new class**

Add to `tests/test_harmonica.py`:

```python
def test_tpxo9_atlas_resource_class(self):
    """Tpxo9AtlasResources has the 15 expected constituents and per-con filenames."""
    from harmonica.resource import ResourceManager, Tpxo9AtlasResources
    r = Tpxo9AtlasResources()
    cons = set(r.available_constituents())
    expected = {'2N2', 'K1', 'K2', 'M2', 'M4', 'MF', 'MM', 'MN4', 'MS4', 'N2', 'O1', 'P1', 'Q1', 'S1', 'S2'}
    assert cons == expected
    assert r.is_consolidated_file is False
    assert r.data_dir_name == 'tpxo9_atlas_v5'
    assert r.dataset_attributes()['units_multiplier'] == 0.001
    assert r.constituent_resource('M2') == 'h_m2_tpxo9_atlas_30_v5.nc'
    assert r.constituent_resource('2N2') == 'h_2n2_tpxo9_atlas_30_v5.nc'
    assert r.constituent_resource('UNKNOWN') is None
    # Registry membership
    assert 'tpxo9_atlas' in ResourceManager.RESOURCES
    assert 'tpxo9_atlas' in ResourceManager.TPXO_MODELS
```

- [ ] **Step 2: Run the test; verify it fails**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_tpxo9_atlas_resource_class -v
```

Expected: FAIL with `ImportError: cannot import name 'Tpxo9AtlasResources'`.

- [ ] **Step 3: Add the `Tpxo9AtlasResources` class**

In `harmonica/resource.py`, after the `Tpxo9Resources` class (around line 186), add:

```python
class Tpxo9AtlasResources(Resources):
    """TPXO9-atlas-v5 resources (1/30 degree global atlas, per-constituent files)."""
    TPXO9_ATLAS_CONS = {
        '2N2': 'h_2n2_tpxo9_atlas_30_v5.nc',
        'K1': 'h_k1_tpxo9_atlas_30_v5.nc',
        'K2': 'h_k2_tpxo9_atlas_30_v5.nc',
        'M2': 'h_m2_tpxo9_atlas_30_v5.nc',
        'M4': 'h_m4_tpxo9_atlas_30_v5.nc',
        'MF': 'h_mf_tpxo9_atlas_30_v5.nc',
        'MM': 'h_mm_tpxo9_atlas_30_v5.nc',
        'MN4': 'h_mn4_tpxo9_atlas_30_v5.nc',
        'MS4': 'h_ms4_tpxo9_atlas_30_v5.nc',
        'N2': 'h_n2_tpxo9_atlas_30_v5.nc',
        'O1': 'h_o1_tpxo9_atlas_30_v5.nc',
        'P1': 'h_p1_tpxo9_atlas_30_v5.nc',
        'Q1': 'h_q1_tpxo9_atlas_30_v5.nc',
        'S1': 'h_s1_tpxo9_atlas_30_v5.nc',
        'S2': 'h_s2_tpxo9_atlas_30_v5.nc',
    }
    is_consolidated_file = False
    data_dir_name = 'tpxo9_atlas_v5'

    def __init__(self):
        """Constructor."""
        super().__init__()

    def resource_attributes(self):
        """Disabled (TPXO9-atlas-v5 is licensed; registration required, no free distribution)."""
        return {
            'url': None,
            'archive': None,
        }

    def dataset_attributes(self):
        """Dataset attributes (mm storage, scale to m)."""
        return {
            'units_multiplier': 0.001,
        }

    def available_constituents(self):
        """The 15 constituents in TPXO9-atlas-v5."""
        return self.TPXO9_ATLAS_CONS.keys()

    def constituent_groups(self):
        """Single uniform-resolution group."""
        return [self.available_constituents()]

    def constituent_resource(self, con):
        """Map constituent name to per-con filename, or None if unsupported."""
        return self.TPXO9_ATLAS_CONS.get(con.upper())
```

- [ ] **Step 4: Update `ResourceManager.RESOURCES` and `TPXO_MODELS`**

In `harmonica/resource.py`, in `ResourceManager` (around line 376):

```python
RESOURCES = {
    'tpxo8': Tpxo8Resources(),
    'tpxo9': Tpxo9Resources(),
    'tpxo9_atlas': Tpxo9AtlasResources(),  # new
    'leprovost': LeProvostResources(),
    'fes2014': FES2014Resources(),
    'adcirc2015': Adcirc2015Resources(),
}
TPXO_MODELS = {'tpxo8', 'tpxo9', 'tpxo9_atlas'}  # appended
```

- [ ] **Step 5: Run the unit test again; verify it passes**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_tpxo9_atlas_resource_class -v
```

Expected: PASS.

- [ ] **Step 6: Run the full suite; verify no regression**

```
tox -e py310
```

Expected: All existing tests still pass.

- [ ] **Step 7: Commit**

```
Add Tpxo9AtlasResources for TPXO9-atlas-v5 (1/30 degree global)

Per-constituent 15-component model; data on \\f\sms\tidal_databases\tpxo9_atlas_v5.
Licensed via OSU registration.
```

---

## Task A4: Add `Tpxo10Resources` class

Adds the second new model. Consolidated single-file layout (25 cons), 1/6° grid, double meter storage, data subdir `tpxo10v2`.

**Files:**
- Modify: `harmonica/resource.py` (new class + registry entry + `TPXO_MODELS` set entry)
- Test: `tests/test_harmonica.py`

- [ ] **Step 1: Write failing unit tests**

Add to `tests/test_harmonica.py`:

```python
def test_tpxo10_resource_class(self):
    """Tpxo10Resources has 25 constituents in a single consolidated file."""
    from harmonica.resource import ResourceManager, Tpxo10Resources
    r = Tpxo10Resources()
    cons = set(r.available_constituents())
    expected = {
        'M2', 'S2', 'N2', 'K2', 'K1', 'O1', 'P1', 'Q1', 'MM', 'MF',
        'MSF', 'M4', 'MN4', 'MS4', '2N2', 'S1', '2Q1', 'J1', 'L2', 'M3',
        'MU2', 'NU2', 'OO1', 'T2', 'M1',
    }
    assert cons == expected
    assert r.is_consolidated_file is True
    assert r.data_dir_name == 'tpxo10v2'
    assert r.dataset_attributes()['units_multiplier'] == 1.0
    # Consolidated: every supported con maps to the same single file.
    assert r.constituent_resource('M2') == 'h_tpxo10.v2.nc'
    assert r.constituent_resource('M1') == 'h_tpxo10.v2.nc'
    assert r.constituent_resource('UNKNOWN') is None
    assert 'tpxo10' in ResourceManager.RESOURCES
    assert 'tpxo10' in ResourceManager.TPXO_MODELS
```

- [ ] **Step 2: Run the test; verify it fails**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_tpxo10_resource_class -v
```

Expected: FAIL with `ImportError: cannot import name 'Tpxo10Resources'`.

- [ ] **Step 3: Add the `Tpxo10Resources` class**

In `harmonica/resource.py`, after `Tpxo9AtlasResources`:

```python
class Tpxo10Resources(Resources):
    """TPXO10v2 resources (1/6 degree global, consolidated single-file layout)."""
    TPXO10_CONS = {
        'M2', 'S2', 'N2', 'K2', 'K1', 'O1', 'P1', 'Q1', 'MM', 'MF',
        'MSF', 'M4', 'MN4', 'MS4', '2N2', 'S1', '2Q1', 'J1', 'L2', 'M3',
        'MU2', 'NU2', 'OO1', 'T2', 'M1',
    }
    DEFAULT_RESOURCE_FILE = 'h_tpxo10.v2.nc'
    is_consolidated_file = True
    data_dir_name = 'tpxo10v2'

    def __init__(self):
        """Constructor."""
        super().__init__()

    def resource_attributes(self):
        """Disabled (TPXO10v2 is licensed; registration required, no free distribution)."""
        return {
            'url': None,
            'archive': None,
        }

    def dataset_attributes(self):
        """Dataset attributes (m storage, no scaling)."""
        return {
            'units_multiplier': 1.0,
        }

    def available_constituents(self):
        """The 25 constituents in TPXO10v2."""
        return self.TPXO10_CONS

    def constituent_groups(self):
        """Single uniform-resolution group."""
        return [self.available_constituents()]

    def constituent_resource(self, con):
        """All supported cons live in the consolidated file."""
        if con.upper() in self.TPXO10_CONS:
            return self.DEFAULT_RESOURCE_FILE
        return None
```

- [ ] **Step 4: Update `ResourceManager.RESOURCES` and `TPXO_MODELS`**

```python
RESOURCES = {
    'tpxo8': Tpxo8Resources(),
    'tpxo9': Tpxo9Resources(),
    'tpxo9_atlas': Tpxo9AtlasResources(),
    'tpxo10': Tpxo10Resources(),  # new
    'leprovost': LeProvostResources(),
    'fes2014': FES2014Resources(),
    'adcirc2015': Adcirc2015Resources(),
}
TPXO_MODELS = {'tpxo8', 'tpxo9', 'tpxo9_atlas', 'tpxo10'}  # appended
```

- [ ] **Step 5: Run the unit test; verify it passes**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_tpxo10_resource_class -v
```

Expected: PASS.

- [ ] **Step 6: Run the full suite**

```
tox -e py310
```

Expected: All existing tests still pass.

- [ ] **Step 7: Commit**

```
Add Tpxo10Resources for TPXO10v2 (1/6 degree global, consolidated)

Single-file model with 25 constituents on \\f\sms\tidal_databases\tpxo10v2.
Uses is_consolidated_file=True for the same code path as legacy TPXO9.
Licensed via OSU registration.
```

---

## Task A5: Add `Tpxo10AtlasResources` class

Adds the third new model. Per-constituent layout (15 cons), 1/30° atlas grid, int millimeter storage, data subdir `tpxo10_atlas_v2`.

**Files:**
- Modify: `harmonica/resource.py` (new class + registry entry + `TPXO_MODELS` set entry)
- Test: `tests/test_harmonica.py`

- [ ] **Step 1: Write failing unit tests**

Add to `tests/test_harmonica.py`:

```python
def test_tpxo10_atlas_resource_class(self):
    """Tpxo10AtlasResources has 15 constituents and per-con filenames."""
    from harmonica.resource import ResourceManager, Tpxo10AtlasResources
    r = Tpxo10AtlasResources()
    cons = set(r.available_constituents())
    expected = {'2N2', 'K1', 'K2', 'M2', 'M4', 'MF', 'MM', 'MN4', 'MS4', 'N2', 'O1', 'P1', 'Q1', 'S1', 'S2'}
    assert cons == expected
    assert r.is_consolidated_file is False
    assert r.data_dir_name == 'tpxo10_atlas_v2'
    assert r.dataset_attributes()['units_multiplier'] == 0.001
    assert r.constituent_resource('M2') == 'h_m2_tpxo10_atlas_30_v2.nc'
    assert r.constituent_resource('2N2') == 'h_2n2_tpxo10_atlas_30_v2.nc'
    assert r.constituent_resource('UNKNOWN') is None
    assert 'tpxo10_atlas' in ResourceManager.RESOURCES
    assert 'tpxo10_atlas' in ResourceManager.TPXO_MODELS
```

- [ ] **Step 2: Run the test; verify it fails**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_tpxo10_atlas_resource_class -v
```

Expected: FAIL with `ImportError`.

- [ ] **Step 3: Add the `Tpxo10AtlasResources` class**

In `harmonica/resource.py`, after `Tpxo10Resources`:

```python
class Tpxo10AtlasResources(Resources):
    """TPXO10-atlas-v2 resources (1/30 degree global atlas, per-constituent files)."""
    TPXO10_ATLAS_CONS = {
        '2N2': 'h_2n2_tpxo10_atlas_30_v2.nc',
        'K1': 'h_k1_tpxo10_atlas_30_v2.nc',
        'K2': 'h_k2_tpxo10_atlas_30_v2.nc',
        'M2': 'h_m2_tpxo10_atlas_30_v2.nc',
        'M4': 'h_m4_tpxo10_atlas_30_v2.nc',
        'MF': 'h_mf_tpxo10_atlas_30_v2.nc',
        'MM': 'h_mm_tpxo10_atlas_30_v2.nc',
        'MN4': 'h_mn4_tpxo10_atlas_30_v2.nc',
        'MS4': 'h_ms4_tpxo10_atlas_30_v2.nc',
        'N2': 'h_n2_tpxo10_atlas_30_v2.nc',
        'O1': 'h_o1_tpxo10_atlas_30_v2.nc',
        'P1': 'h_p1_tpxo10_atlas_30_v2.nc',
        'Q1': 'h_q1_tpxo10_atlas_30_v2.nc',
        'S1': 'h_s1_tpxo10_atlas_30_v2.nc',
        'S2': 'h_s2_tpxo10_atlas_30_v2.nc',
    }
    is_consolidated_file = False
    data_dir_name = 'tpxo10_atlas_v2'

    def __init__(self):
        """Constructor."""
        super().__init__()

    def resource_attributes(self):
        """Disabled (licensed; registration required)."""
        return {
            'url': None,
            'archive': None,
        }

    def dataset_attributes(self):
        """Dataset attributes (mm storage)."""
        return {
            'units_multiplier': 0.001,
        }

    def available_constituents(self):
        """The 15 constituents in TPXO10-atlas-v2."""
        return self.TPXO10_ATLAS_CONS.keys()

    def constituent_groups(self):
        """Single uniform-resolution group."""
        return [self.available_constituents()]

    def constituent_resource(self, con):
        """Map constituent name to per-con filename, or None if unsupported."""
        return self.TPXO10_ATLAS_CONS.get(con.upper())
```

- [ ] **Step 4: Update `ResourceManager.RESOURCES` and `TPXO_MODELS`**

```python
RESOURCES = {
    'tpxo8': Tpxo8Resources(),
    'tpxo9': Tpxo9Resources(),
    'tpxo9_atlas': Tpxo9AtlasResources(),
    'tpxo10': Tpxo10Resources(),
    'tpxo10_atlas': Tpxo10AtlasResources(),  # new
    'leprovost': LeProvostResources(),
    'fes2014': FES2014Resources(),
    'adcirc2015': Adcirc2015Resources(),
}
TPXO_MODELS = {'tpxo8', 'tpxo9', 'tpxo9_atlas', 'tpxo10', 'tpxo10_atlas'}  # appended
```

- [ ] **Step 5: Run the unit test; verify it passes**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_tpxo10_atlas_resource_class -v
```

Expected: PASS.

- [ ] **Step 6: Run the full suite**

```
tox -e py310
```

Expected: All existing tests still pass.

- [ ] **Step 7: Commit**

```
Add Tpxo10AtlasResources for TPXO10-atlas-v2 (1/30 degree global atlas)

Per-constituent 15-component model; data on
\\f\sms\tidal_databases\tpxo10_atlas_v2. Licensed via OSU registration.
```

---

## Task A6: Change `DEFAULT_RESOURCE` to `tpxo10_atlas`

Per spec §5, the new default model becomes TPXO10-atlas. This is a one-line change but worth its own task so the regression risk is bounded.

**Files:**
- Modify: `harmonica/resource.py` (one line)
- Modify: `harmonica/tpxo_database.py` (one line — `DEFAULT_TPXO_RESOURCE`)
- Test: `tests/test_harmonica.py`

- [ ] **Step 1: Write failing unit test for the default**

Add to `tests/test_harmonica.py`:

```python
def test_default_resource_is_tpxo10_atlas(self):
    """harmonica's default tidal model is now TPXO10-atlas (was TPXO9)."""
    from harmonica.resource import ResourceManager
    from harmonica.tpxo_database import DEFAULT_TPXO_RESOURCE
    assert ResourceManager.DEFAULT_RESOURCE == 'tpxo10_atlas'
    assert DEFAULT_TPXO_RESOURCE == 'tpxo10_atlas'
```

- [ ] **Step 2: Run the test; verify it fails**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_default_resource_is_tpxo10_atlas -v
```

Expected: FAIL (current values are `'tpxo9'`).

- [ ] **Step 3: Update the defaults**

In `harmonica/resource.py` (around line 386):

```python
DEFAULT_RESOURCE = 'tpxo10_atlas'  # was 'tpxo9'
```

In `harmonica/tpxo_database.py` (line 17):

```python
DEFAULT_TPXO_RESOURCE = 'tpxo10_atlas'  # was 'tpxo9'
```

- [ ] **Step 4: Run the test; verify it passes**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_default_resource_is_tpxo10_atlas -v
```

Expected: PASS.

- [ ] **Step 5: Run the full suite**

```
tox -e py310
```

Expected: All existing tests pass. None of the existing tests depend on the default model name — they all pass an explicit model — but if any are surfaced as broken here, that's a useful signal.

- [ ] **Step 6: Commit**

```
Change DEFAULT_RESOURCE to tpxo10_atlas

TPXO10-atlas-v2 is the highest-resolution and most current OSU TPXO product;
make it the default. Existing callers that pass an explicit model name are
unaffected.
```

---

## Task A7: Integration test for `tpxo9_atlas` (end-to-end + `.base` fixture)

End-to-end test exercising the new resource through the existing `Constituents` extractor. First run creates the `.out` file; bless it as the `.base` fixture and commit.

**Files:**
- Modify: `tests/test_harmonica.py` (add test method)
- Create: `tests/tpxo9_atlas.base` (after blessing)

- [ ] **Step 1: Add the test method (it will fail the first time — no `.base` exists yet)**

Add to `tests/test_harmonica.py`:

```python
def test_tpxo9_atlas(self):
    """Test tidal extraction for the TPXO9-atlas-v5 model."""
    self._run_case('tpxo9_atlas')
```

- [ ] **Step 2: Run the test; expect a meaningful failure**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_tpxo9_atlas -v
```

Expected: One of two failure modes:
- `FileNotFoundError: tpxo9_atlas.base` (existing `.base` file missing — this is the expected fail). The `.out` file will have been created in `tests/`.
- A different exception means something is broken in the resource class or path-join change — investigate before blessing.

If the run produced a `tpxo9_atlas.out` file in `tests/`, inspect it manually:

```
type tests\tpxo9_atlas.out
```

Sanity check: the file should contain 5 blocks (one per location in `self.LOCS`), each a DataFrame-as-text with rows for M2, S2, N2, K1, and columns `amplitude`, `phase`, `speed`. Values should be plausible tidal magnitudes (e.g., M2 amplitude in the US East Coast points ≈ 0.3-1.5 m, phase in degrees). If amplitudes are 1000× too large or too small, the `units_multiplier` is wrong.

- [ ] **Step 3: Bless the output as `.base` if it looks right**

```
copy tests\tpxo9_atlas.out tests\tpxo9_atlas.base
```

(PowerShell: `Copy-Item tests\tpxo9_atlas.out tests\tpxo9_atlas.base`)

- [ ] **Step 4: Re-run the test; expect it to pass**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_tpxo9_atlas -v
```

Expected: PASS. `filecmp.cmp` now sees identical `.out` and `.base`.

- [ ] **Step 5: Commit**

```
Add tpxo9_atlas integration test + .base fixture
```

---

## Task A8: Integration test for `tpxo10` (end-to-end + `.base` fixture)

Same pattern as Task A7. This exercises the consolidated-file code path (`is_consolidated_file=True`) on a new dataset.

**Files:**
- Modify: `tests/test_harmonica.py`
- Create: `tests/tpxo10.base`

- [ ] **Step 1: Add the test method**

Add to `tests/test_harmonica.py`:

```python
def test_tpxo10(self):
    """Test tidal extraction for the TPXO10v2 model."""
    self._run_case('tpxo10')
```

- [ ] **Step 2: Run the test; expect failure (no `.base`)**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_tpxo10 -v
```

Expected: `FileNotFoundError: tpxo10.base`. The `tpxo10.out` file will have been created.

Inspect `tests/tpxo10.out`. Amplitudes for M2 at US coast points should be plausible (0.3-1.5 m). If they're 1000× off, units_multiplier is wrong. If they're identical to the `tpxo9.base` values, the consolidated-file dispatch is bugged (likely reading from the wrong dataset).

- [ ] **Step 3: Bless the output**

```
copy tests\tpxo10.out tests\tpxo10.base
```

- [ ] **Step 4: Re-run; expect pass**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_tpxo10 -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```
Add tpxo10 integration test + .base fixture
```

---

## Task A9: Integration test for `tpxo10_atlas` (end-to-end + `.base` fixture)

Same pattern. This is the new default model — important that the test passes.

**Files:**
- Modify: `tests/test_harmonica.py`
- Create: `tests/tpxo10_atlas.base`

- [ ] **Step 1: Add the test method**

Add to `tests/test_harmonica.py`:

```python
def test_tpxo10_atlas(self):
    """Test tidal extraction for the TPXO10-atlas-v2 model (default)."""
    self._run_case('tpxo10_atlas')
```

- [ ] **Step 2: Run; expect failure (no `.base`)**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_tpxo10_atlas -v
```

Expected: `FileNotFoundError: tpxo10_atlas.base`.

Inspect `tests/tpxo10_atlas.out`. Same sanity checks as before. The atlas resolution is 1/30°, so values may differ from tpxo10 (which is 1/6°) — that's expected.

- [ ] **Step 3: Bless the output**

```
copy tests\tpxo10_atlas.out tests\tpxo10_atlas.base
```

- [ ] **Step 4: Re-run; expect pass**

```
tox -e py310 -- tests/test_harmonica.py::TestHarmonica::test_tpxo10_atlas -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```
Add tpxo10_atlas integration test + .base fixture
```

---

## Task A10: Bump version to 2.2.0 (and fix existing drift)

`setup.py` is at `2.1.0`; `harmonica/__init__.py` is at `2.0.1` (pre-existing drift). Sync both to `2.2.0`.

**Files:**
- Modify: `setup.py` (line 46)
- Modify: `harmonica/__init__.py` (line 21)

- [ ] **Step 1: Update `setup.py`**

In `setup.py` (line 46):

```python
version = '2.2.0'
```

- [ ] **Step 2: Update `harmonica/__init__.py`**

In `harmonica/__init__.py` (line 21):

```python
__version__ = '2.2.0'
```

- [ ] **Step 3: Verify both report the same version**

```
python -c "import harmonica; print(harmonica.__version__)"
```

Expected output:

```
2.2.0
```

Also run:

```
python -c "import setup; print(setup.version)" 2>nul
```

(May not work depending on how `setup.py` exposes `version`; the import-and-print of `harmonica.__version__` is the canonical check.)

- [ ] **Step 4: Commit**

```
Bump harmonica to 2.2.0

Adds TPXO9-atlas-v5, TPXO10v2, TPXO10-atlas-v2 models; changes default to
tpxo10_atlas. Also fixes pre-existing drift between setup.py (2.1.0) and
__init__.py (2.0.1) — both now report 2.2.0.
```

---

## Task A11: Final full-suite run + coverage check

Per `tox.ini`, the suite runs `pytest --cov harmonica` and enforces `--fail-under 75` coverage. Verify nothing new dipped below the threshold.

- [ ] **Step 1: Run the full tox suite**

```
cd D:\quick\git\harmonica
tox -e py310
```

Expected: All tests pass; coverage ≥ 75%. If coverage failed (the new resource classes might pull the percentage down), inspect `coverage report` output for which files are under-covered and add unit tests as needed. New code in `resource.py` should be exercised by Tasks A3-A5 + A7-A9; verify the coverage report shows those classes hit.

- [ ] **Step 2: Inspect HTML coverage**

```
start coverage_html\index.html
```

(Or `Invoke-Item coverage_html\index.html` in PowerShell.)

Confirm `harmonica/resource.py` shows the new classes' branches and methods exercised.

- [ ] **Step 3: (No commit needed; this is a verification step.)**

---

## Task A12: Phase A delivery handoff

- [ ] **Step 1: Push branch and open PR (user-owned)**

```
git push -u origin master_update_tpxo
```

Then open a PR titled "Add TPXO9-atlas-v5, TPXO10v2, TPXO10-atlas-v2 support; bump to 2.2.0" linking back to the design spec.

- [ ] **Step 2: After PR merge: tag the release**

```
git checkout master
git pull origin master
git tag -a v2.2.0 -m "harmonica 2.2.0 - add TPXO9-atlas-v5, TPXO10v2, TPXO10-atlas-v2"
git push origin v2.2.0
```

- [ ] **Step 3: Publish to Aquaveo's package index per existing release workflow**

(Out of scope for this plan — follow the standard Aquaveo Python release procedure used for the previous harmonica 2.1.0 release.)

---

# Phase B — xmstides 3.4.0

Working tree: `D:\quick\git\xmstides\` (to be cloned in Task B1). Depends on harmonica 2.2.0 being either released (Phase A complete) or dev-installed.

## Task B1: Clone xmstides and dev-install harmonica 2.2.0

**Files:**
- Create: `D:\quick\git\xmstides\` (clone)

- [ ] **Step 1: Clone the repo**

```
git clone https://github.com/Aquaveo/xmstides.git D:\quick\git\xmstides
```

- [ ] **Step 2: Create work branch**

```
cd D:\quick\git\xmstides
git checkout -b master_update_tpxo
```

- [ ] **Step 3: Verify current xmstides version is 3.3.0 per spec**

```
grep -r "3\.3\.0" setup.py
```

(Or inspect `setup.py` manually.) Expected: a line like `version = '3.3.0'`.

- [ ] **Step 4: Dev-install local harmonica 2.2.0 into xmstides's tox environment**

Per `dev_install_workflow.md`: the xmstides tox env will pull `harmonica` from PIP_INDEX_URL by default. To override and use the local harmonica:

```
cd D:\quick\git\xmstides
tox --notest -e py310
# After the env is created, manually pip-install local harmonica:
.tox\py310\Scripts\pip.exe install -e D:\quick\git\harmonica
.tox\py310\Scripts\python.exe -c "import harmonica; print(harmonica.__version__)"
```

Expected output: `2.2.0`.

- [ ] **Step 5: (No commit; this is environment setup.)**

---

## Task B2: Read xmstides file structure to confirm line numbers

The spec referenced file paths in the SMS-bundled site-packages copy (`Dev/{SMS,GMS,WMS}/APP/bin64/hidden.python/Lib/site-packages/xms/tides/`). Confirm the same code exists at the same relative paths in the upstream git source — line numbers may have drifted.

**Files:** Read-only exploration.

- [ ] **Step 1: Verify file existence and locate key landmarks**

```
cd D:\quick\git\xmstides
grep -n "TPX08_INDEX\|TPX09_INDEX\|TDB_SOURCES" xms\tides\data\tidal_data.py
grep -n "_get_harmonica_model_string\|license" xms\tides\gui\tidal_dlg.py
grep -n "source\|tidal_extractor" xms\tides\data\tidal_extractor.py
```

Record the actual line numbers — the rest of Phase B's edits will anchor on string content rather than line numbers, so drift is OK; this step is just to confirm the targets exist.

If any of the three files is missing or moved, stop and re-discover by searching the repo:

```
git grep -l "TPX08_INDEX"
git grep -l "_get_harmonica_model_string"
```

- [ ] **Step 2: (No commit; this is exploration.)**

---

## Task B3: Append new dialog index constants + display strings

**Files:**
- Modify: `xms/tides/data/tidal_data.py`
- Test: location TBD (check the repo's existing test layout in Task B2 — most likely `tests/tidal_data_test.py` or `xms/tides/tests/`)

- [ ] **Step 1: Write failing unit test**

Add to whichever test file currently exercises `tidal_data` (discover in Task B2). If no test file exists, create `tests/test_tidal_data.py`:

```python
"""Tests for tidal_data constants."""
from xms.tides.data import tidal_data


def test_new_tpxo_indexes_appended():
    """New TPXO indexes are appended after existing ones (do not insert)."""
    # Existing
    assert tidal_data.ADCIRC_INDEX == 0
    assert tidal_data.LEPROVOST_INDEX == 1
    assert tidal_data.FES2014_INDEX == 2
    assert tidal_data.TPX08_INDEX == 3
    assert tidal_data.TPX09_INDEX == 4
    assert tidal_data.USER_DEFINED_INDEX == 5
    # New (appended)
    assert tidal_data.TPX09_ATLAS_INDEX == 6
    assert tidal_data.TPX10_INDEX == 7
    assert tidal_data.TPX10_ATLAS_INDEX == 8


def test_tdb_sources_appended():
    """TDB_SOURCES has three new entries appended at indexes 6, 7, 8."""
    sources = tidal_data.TDB_SOURCES
    assert sources[tidal_data.TPX09_ATLAS_INDEX] == 'TPXO9-atlas (v5)'
    assert sources[tidal_data.TPX10_INDEX] == 'TPXO10 (1/6 deg)'
    assert sources[tidal_data.TPX10_ATLAS_INDEX] == 'TPXO10-atlas (1/30 deg)'
    # Order preserved for backward-compat with saved tidal_comp.nc files
    assert sources[tidal_data.ADCIRC_INDEX] == 'ADCIRC2015'
    assert sources[tidal_data.TPX09_INDEX] == 'TPXO9'
```

Note on display strings: spec §5 used `'TPXO10 (1/6°)'` with the degree symbol. Within Python source files in this codebase the degree symbol is fine in string literals (the file is UTF-8). However, if you discover the existing TDB_SOURCES entries avoid non-ASCII (check what `'ADCIRC2015'` looks like), match that convention and use `'TPXO10 (1/6 deg)'` and `'TPXO10-atlas (1/30 deg)'` instead. Pick one and use it in both this test and the source code.

- [ ] **Step 2: Run test; expect failure**

```
cd D:\quick\git\xmstides
tox -e py310 -- tests/test_tidal_data.py -v
```

Expected: FAIL with `AttributeError: module ... has no attribute 'TPX09_ATLAS_INDEX'`.

- [ ] **Step 3: Append the constants and display strings**

In `xms/tides/data/tidal_data.py`, find the existing block of `*_INDEX` constants (near line 1-50 depending on file structure). Append after `USER_DEFINED_INDEX = 5`:

```python
TPX09_ATLAS_INDEX = 6
TPX10_INDEX = 7
TPX10_ATLAS_INDEX = 8
```

Find the existing `TDB_SOURCES` list. Append three entries at indexes 6, 7, 8 in the same order as the constants:

```python
TDB_SOURCES = [
    'ADCIRC2015',
    'LeProvost',
    'FES2014',
    'TPXO8',
    'TPXO9',
    'User defined',
    'TPXO9-atlas (v5)',
    'TPXO10 (1/6 deg)',
    'TPXO10-atlas (1/30 deg)',
]
```

(Or — equivalent — `.extend([...])` if the existing code uses that style. Match the existing style.)

- [ ] **Step 4: Run test; expect pass**

```
tox -e py310 -- tests/test_tidal_data.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```
Append TPX09_ATLAS_INDEX, TPX10_INDEX, TPX10_ATLAS_INDEX

Three new tidal-database options for the SMS Tidal dialog. Constants are
appended (not inserted) because the integer index is persisted into
tidal_comp.nc as info.attrs['source']; reordering would break existing
project files.
```

---

## Task B4: Extend `_get_harmonica_model_string()` in `tidal_dlg.py`

**Files:**
- Modify: `xms/tides/gui/tidal_dlg.py` (function `_get_harmonica_model_string`)
- Test: same test file as Task B3 (or a new one in the same folder)

- [ ] **Step 1: Write failing unit test**

Add to the test file:

```python
def test_get_harmonica_model_string_new_indexes():
    """The three new dialog indexes map to the correct harmonica model names."""
    from xms.tides.gui.tidal_dlg import _get_harmonica_model_string
    from xms.tides.data import tidal_data
    assert _get_harmonica_model_string(tidal_data.TPX09_ATLAS_INDEX) == 'tpxo9_atlas'
    assert _get_harmonica_model_string(tidal_data.TPX10_INDEX) == 'tpxo10'
    assert _get_harmonica_model_string(tidal_data.TPX10_ATLAS_INDEX) == 'tpxo10_atlas'
    # Existing mappings still work
    assert _get_harmonica_model_string(tidal_data.TPX08_INDEX) == 'tpxo8'
    assert _get_harmonica_model_string(tidal_data.TPX09_INDEX) == 'tpxo9'
```

- [ ] **Step 2: Run test; expect failure**

```
tox -e py310 -- tests/test_tidal_data.py::test_get_harmonica_model_string_new_indexes -v
```

Expected: FAIL — the function returns `None` or raises for the new indexes.

- [ ] **Step 3: Extend the function**

In `xms/tides/gui/tidal_dlg.py`, find `_get_harmonica_model_string` (around line 180 per spec). The function is presumably an if-elif chain or dict lookup mapping `source_index` → harmonica model string. Add three new cases preserving the existing style:

```python
# If/elif style:
elif source_index == tidal_data.TPX09_ATLAS_INDEX:
    return 'tpxo9_atlas'
elif source_index == tidal_data.TPX10_INDEX:
    return 'tpxo10'
elif source_index == tidal_data.TPX10_ATLAS_INDEX:
    return 'tpxo10_atlas'

# OR dict-lookup style — append:
tidal_data.TPX09_ATLAS_INDEX: 'tpxo9_atlas',
tidal_data.TPX10_INDEX: 'tpxo10',
tidal_data.TPX10_ATLAS_INDEX: 'tpxo10_atlas',
```

Match the existing pattern.

- [ ] **Step 4: Run test; expect pass**

```
tox -e py310 -- tests/test_tidal_data.py::test_get_harmonica_model_string_new_indexes -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```
Map new dialog indexes to harmonica model strings

TPX09_ATLAS_INDEX -> tpxo9_atlas; TPX10_INDEX -> tpxo10;
TPX10_ATLAS_INDEX -> tpxo10_atlas. Wires the new dialog choices through to
harmonica's model resolution.
```

---

## Task B5: Extend the license-warning check in `tidal_dlg.py`

All three new TPXO products require OSU registration. Per spec §5, they need the same red-text "license required" treatment as TPXO8 / TPXO9 / FES2014.

**Files:**
- Modify: `xms/tides/gui/tidal_dlg.py` (license-warning check, around line 103 per spec)
- Test: same test file

- [ ] **Step 1: Read the existing license-warning check to understand the pattern**

```
grep -n -C 5 "license\|TPX08_INDEX\|TPX09_INDEX" xms\tides\gui\tidal_dlg.py
```

Identify whether the check uses (a) a set of "licensed" indexes, (b) an if/elif chain, or (c) consults `harmonica` for each model's `url` (which would auto-handle the new ones since their `resource_attributes` returns `url=None`).

- [ ] **Step 2: Write failing unit test (test the user-visible behavior)**

If the existing pattern is a set or list of licensed indexes, write:

```python
def test_new_models_flagged_as_licensed():
    """The three new TPXO models display the license-required warning."""
    from xms.tides.gui.tidal_dlg import _is_licensed_source  # or whichever predicate
    from xms.tides.data import tidal_data
    assert _is_licensed_source(tidal_data.TPX09_ATLAS_INDEX)
    assert _is_licensed_source(tidal_data.TPX10_INDEX)
    assert _is_licensed_source(tidal_data.TPX10_ATLAS_INDEX)
    # Sanity: existing licensed sources still flagged
    assert _is_licensed_source(tidal_data.TPX08_INDEX)
    assert _is_licensed_source(tidal_data.TPX09_INDEX)
    # Non-licensed: ADCIRC and LeProvost are freely distributed
    assert not _is_licensed_source(tidal_data.ADCIRC_INDEX)
    assert not _is_licensed_source(tidal_data.LEPROVOST_INDEX)
```

If the predicate has a different name, adjust the import. If the check is inline (not a separate predicate), refactor it into a predicate function so it's testable.

- [ ] **Step 3: Run test; expect failure**

```
tox -e py310 -- tests/test_tidal_data.py -v
```

Expected: FAIL.

- [ ] **Step 4: Extend the license check**

Append `TPX09_ATLAS_INDEX`, `TPX10_INDEX`, `TPX10_ATLAS_INDEX` to whatever data structure or branching represents "licensed sources". E.g., if there's a set:

```python
LICENSED_SOURCES = {
    tidal_data.FES2014_INDEX,
    tidal_data.TPX08_INDEX,
    tidal_data.TPX09_INDEX,
    tidal_data.TPX09_ATLAS_INDEX,   # new
    tidal_data.TPX10_INDEX,         # new
    tidal_data.TPX10_ATLAS_INDEX,   # new
}
```

- [ ] **Step 5: Run test; expect pass**

```
tox -e py310 -- tests/test_tidal_data.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```
Flag new TPXO models as license-required in Tidal dialog

All three new OSU TPXO products require registration; show the same red-text
warning as TPXO8/9 and FES2014.
```

---

## Task B6: Extend `tidal_extractor.py` source-to-harmonica-model dispatch

This is the runtime side — when the saved index in `tidal_comp.nc` is loaded, it dispatches to the corresponding harmonica model.

**Files:**
- Modify: `xms/tides/data/tidal_extractor.py` (around line 45 per spec)
- Test: same test file

- [ ] **Step 1: Read the existing dispatch to understand the pattern**

```
grep -n -C 10 "source\|TPX08_INDEX\|TPX09_INDEX" xms\tides\data\tidal_extractor.py
```

Identify whether it's a function (e.g., `_source_to_model(idx)`) or inline dispatch within a larger function.

- [ ] **Step 2: Write failing unit test**

If a callable predicate exists, test it directly. Otherwise, test the higher-level extractor entry point with each new index:

```python
def test_extractor_dispatches_new_models():
    """The extractor maps the three new indexes to harmonica model names."""
    from xms.tides.data.tidal_extractor import _source_to_model  # or equivalent
    from xms.tides.data import tidal_data
    assert _source_to_model(tidal_data.TPX09_ATLAS_INDEX) == 'tpxo9_atlas'
    assert _source_to_model(tidal_data.TPX10_INDEX) == 'tpxo10'
    assert _source_to_model(tidal_data.TPX10_ATLAS_INDEX) == 'tpxo10_atlas'
```

- [ ] **Step 3: Run test; expect failure**

```
tox -e py310 -- tests/test_tidal_data.py::test_extractor_dispatches_new_models -v
```

Expected: FAIL.

- [ ] **Step 4: Extend the dispatch**

Mirror the same pattern used for existing TPXO8/9 cases. Three new cases:

```python
# If/elif:
elif source == tidal_data.TPX09_ATLAS_INDEX:
    return 'tpxo9_atlas'
elif source == tidal_data.TPX10_INDEX:
    return 'tpxo10'
elif source == tidal_data.TPX10_ATLAS_INDEX:
    return 'tpxo10_atlas'
```

- [ ] **Step 5: Run test; expect pass**

```
tox -e py310 -- tests/test_tidal_data.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```
Dispatch new dialog indexes to harmonica models in tidal_extractor

Reads info.attrs['source'] from saved tidal_comp.nc and resolves it to the
harmonica model string for runtime extraction.
```

---

## Task B7: Run full xmstides suite

- [ ] **Step 1: Run full tox**

```
cd D:\quick\git\xmstides
tox -e py310
```

Expected: All tests pass. If coverage thresholds are enforced (check `tox.ini` for `--fail-under`), confirm they're met.

- [ ] **Step 2: (No commit; verification step.)**

---

## Task B8: Bump xmstides to 3.4.0

**Files:**
- Modify: `setup.py` (and/or `xms/tides/__init__.py` if it has `__version__`)

- [ ] **Step 1: Verify both version locations are in sync (or note drift)**

```
grep -rn "3\.3\.0" setup.py xms\tides\__init__.py
```

Same pattern as harmonica — if there's drift, fix both.

- [ ] **Step 2: Update versions to 3.4.0**

In `setup.py`:

```python
version = '3.4.0'
```

In `xms/tides/__init__.py` (if it has `__version__`):

```python
__version__ = '3.4.0'
```

- [ ] **Step 3: Verify**

```
python -c "import xms.tides; print(xms.tides.__version__)"
```

Expected: `3.4.0`.

- [ ] **Step 4: Commit**

```
Bump xmstides to 3.4.0

Adds TPXO9-atlas-v5, TPXO10v2, TPXO10-atlas-v2 options in the Tidal dialog;
wires through to harmonica 2.2.0.
```

---

## Task B9: Phase B delivery handoff

- [ ] **Step 1: Push branch and open PR**

```
git push -u origin master_update_tpxo
```

PR title: "Add TPXO9-atlas-v5, TPXO10v2, TPXO10-atlas-v2 to Tidal dialog; bump to 3.4.0". Link to design spec and the harmonica 2.2.0 PR.

- [ ] **Step 2: After PR merge: tag the release**

```
git checkout master
git pull origin master
git tag -a v3.4.0 -m "xmstides 3.4.0 - add TPXO9-atlas-v5, TPXO10v2, TPXO10-atlas-v2 dialog options"
git push origin v3.4.0
```

- [ ] **Step 3: Publish to Aquaveo's package index**

(Out of scope for this plan — follow the standard Aquaveo Python release procedure.)

---

# Phase C — xmsdev_trunk integration (SVN)

Working tree: `D:\quick\xmsdev_trunk\` (SVN, not git).

## Task C1: Bump `python_requirements.txt`

**Files:**
- Modify: `Dev/python_requirements.txt`

- [ ] **Step 1: Inspect current pins**

```
grep -n "harmonica\|xmstides" Dev\python_requirements.txt
```

Confirm current entries are at `harmonica==2.1.0` and `xmstides==3.3.0` (or whatever the equivalent version-pinning syntax is in this file).

- [ ] **Step 2: Update pins to the new versions**

In `Dev/python_requirements.txt`, replace the two lines:

```
harmonica==2.2.0
xmstides==3.4.0
```

(Match the exact pinning syntax — if the existing lines use `>=` or no version, mirror that.)

- [ ] **Step 3: (No commit yet; the SVN commit is user-owned per workflow.)**

---

## Task C2: Refresh SMS's bundled Python

**Files:** Modifies `Dev/{SMS,GMS,WMS}/APP/bin64/hidden.python/Lib/site-packages/`.

- [ ] **Step 1: Run the update batch file**

```
cd D:\quick\xmsdev_trunk\Dev
update_dev_python.bat
```

Expected: pip installs harmonica 2.2.0 and xmstides 3.4.0 into each app's hidden Python. Output should mention both packages being upgraded.

- [ ] **Step 2: Verify the install**

```
Dev\SMS\APP\bin64\hidden.python\python.exe -c "import harmonica, xms.tides; print(harmonica.__version__, xms.tides.__version__)"
```

Expected: `2.2.0 3.4.0`.

- [ ] **Step 3: (No SVN commit yet — Step C3 first.)**

---

## Task C3: Manual smoke test in SMS

The Python-level tests don't exercise the actual Qt dialog. A short interactive smoke test confirms end-to-end wiring before delivering Phase C.

- [ ] **Step 1: Launch SMS**

Build (if not already built) and launch the SMS binary. Open or create a project where the Tidal dialog is reachable (typically: add an ADCIRC coverage, then access the Tidal Database options for a boundary arc).

- [ ] **Step 2: Verify dialog displays all 9 sources**

Confirm the dropdown lists, in order:
1. ADCIRC2015
2. LeProvost
3. FES2014
4. TPXO8
5. TPXO9
6. User defined
7. TPXO9-atlas (v5)
8. TPXO10 (1/6 deg)
9. TPXO10-atlas (1/30 deg)

- [ ] **Step 3: Select each new model and confirm license warning appears**

For each of items 7, 8, 9: select the model and confirm the red license-required warning text appears in the dialog (same as TPXO8 / TPXO9 / FES2014).

- [ ] **Step 4: Run a constituent extraction with TPXO10-atlas (the new default)**

Set the model to TPXO10-atlas. Set the data directory to a local copy of `\\f\sms\tidal_databases\tpxo10_atlas_v2\` (or point the harmonica config at the network share). Extract constituents for a known boundary point. Confirm amplitudes are plausible (M2 amplitudes in the US East Coast region should be roughly 0.3–1.5 m).

- [ ] **Step 5: Save and reload**

Save the project (`.sms` file). Close and reopen. Verify the new source index round-trips through `tidal_comp.nc` and the dialog re-opens showing TPXO10-atlas selected.

- [ ] **Step 6: Save the screenshot or note any issues**

(If the smoke test failed at any step, do not proceed to the SVN commit handoff. Diagnose and either patch xmstides / harmonica or escalate.)

---

## Task C4: Hand off to user for SVN commit

Per `feedback_svn_add_reminder.md`: do not run `svn commit` or build batch files (other than `update_dev_python.bat`, which is part of the dev workflow).

- [ ] **Step 1: Show the user the SVN status**

```
svn status Dev\python_requirements.txt
```

Expected: `M Dev\python_requirements.txt`.

- [ ] **Step 2: Tell the user to review and commit**

Suggested message for the user:

```
Bump harmonica to 2.2.0 and xmstides to 3.4.0

Adds TPXO9-atlas-v5, TPXO10v2, TPXO10-atlas-v2 as selectable tidal database
options in the SMS Tidal dialog. New default is TPXO10-atlas.
```

Workflow per `feedback_svn_add_reminder.md`: the user runs `svn commit` and the SMS build themselves.

---

# Self-review checklist (done by the planner)

**1. Spec coverage:** Every numbered §3 success criterion has a task:
- "Select TPXO10-atlas in dialog and extract" → Tasks A5 (resource class) + B3/B4 (dialog wiring) + C3 step 4 (manual smoke).
- "Existing source=3/source=4 files still load" → Tasks A1/A2 don't change existing indexes; B3 confirms appends-only; Phase A integration tests still exercise tpxo8 and tpxo9.
- "Per-constituent loader test against TPXO10 file" → Tasks A8 + A9 (both per-con and consolidated cases covered by A7/A8/A9 together).

**2. Placeholder scan:** No "TBD" / "fill in" / "appropriate error handling" / "similar to Task N" remain. The "test file location TBD" notes in Phase B are intentional — they're discoverable in Task B2 and the test code itself is fully written.

**3. Type consistency:** Names used consistently:
- Resource classes: `Tpxo9AtlasResources`, `Tpxo10Resources`, `Tpxo10AtlasResources` (PascalCase, matches `Tpxo8Resources`/`Tpxo9Resources` precedent)
- Model string identifiers: `tpxo9_atlas`, `tpxo10`, `tpxo10_atlas` (snake_case, matches `tpxo8`/`tpxo9` precedent)
- Index constants: `TPX09_ATLAS_INDEX`, `TPX10_INDEX`, `TPX10_ATLAS_INDEX` (SCREAMING_SNAKE, matches `TPX08_INDEX`/`TPX09_INDEX` precedent — note the `TPX09` spelling drops the `O` of `TPXO`, mirroring the existing convention)
- Resource attribute: `is_consolidated_file` (snake_case, descriptive)
- Resource attribute: `data_dir_name` (snake_case)

**4. Project conventions check:**
- **VCS workflow**: harmonica/xmstides are git → Claude does branch creation, commits, PR push (with user approving each push). xmsdev_trunk is SVN → user owns `svn add`, `svn commit`, and build steps (Phase C handoff respects this).
- **Test framework**: harmonica uses pytest + tox per `tox.ini`. Tests live in `tests/test_harmonica.py` as a class. New tests added as class methods. xmstides framework discovered in Task B2 — defer concrete test placement to that step.
- **Test-fixture format**: harmonica `.base` files are byte-exact regression fixtures (`filecmp.cmp`). First run creates `.out`; user must inspect and bless as `.base`. Tasks A7/A8/A9 explicitly walk through this.
- **Style/format**: No clang-format equivalent for Python in harmonica/xmstides repos; existing flake8 / pylint config will be honored by tox.
- **CP1252 gotcha**: Python source files in these repos are UTF-8 and contain no high-bit chars that we modify. The `°` in display strings was deliberately replaced with `deg` in Task B3 to avoid mixing encodings.
- **SVN→git migration**: Per `project_svn_to_git_migration.md`, xmsdev_trunk dev branch is the durable timeline; skip docs-only commits when backporting. Phase C touches one config file; not docs-only.

---

# Risk and rollback notes

- **Phase A: resource path-join change** (Task A1 Step 6) — this changes how all models resolve data directories. The default `data_dir_name = None` should preserve existing behavior for TPXO8/9/etc, but Task A1 Step 7 runs the full suite as a regression check.
- **Phase A: default model change** (Task A6) — callers that rely on the implicit default `'tpxo9'` will silently start using `'tpxo10_atlas'`. Verify in Task C3 that the dialog defaults to the new model in fresh projects. Existing projects keep their saved source index (unchanged behavior).
- **Phase B: index ordering** (Task B3) — the test explicitly asserts indexes 0..5 are unchanged. If anyone reorders them in the future, project files with `source ∈ {0..5}` would silently load the wrong model. Worth a code comment in `tidal_data.py` near the indexes warning against reorder.
- **Phase C: SVN commit** — user-owned per workflow memory. Plan does not run `svn commit`.

---

# Status

Ready to execute. Recommended sub-skill: `superpowers:subagent-driven-development` (fresh subagent per task with review between; matches the bottom-up dev-install workflow well) or `superpowers:executing-plans` (inline execution with checkpoints).
