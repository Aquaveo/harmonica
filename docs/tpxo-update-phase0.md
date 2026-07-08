# TPXO Update — Phase 0 Findings

**Date**: 2026-05-14
**Author**: azundel@aquaveo.com (with Claude)
**Status**: Phase 0 closed — Phase 1 (implementation) can proceed
**Companion spec**: `xmsdev_trunk/docs/superpowers/specs/2026-05-12-harmonica-tpxo-update-design.md`

## Purpose

Verify the on-disk layout and netCDF schema of three new TPXO products before writing resource classes or modifying the loader:

- TPXO9-atlas-v5
- TPXO10v2 (1/6° global)
- TPXO10-atlas-v2 (1/30° global)

OSU's site notes that their netCDF "is different from TMD3 consolidated netcdf format," so the schema deltas needed verification rather than assumption.

## Sample data

Verified against the full OSU distributions on Aquaveo's `\\f\sms\tidal_databases\` network share, received 2026-05-14 after OSU approved non-commercial use:

- `\\f\sms\tidal_databases\tpxo9_atlas_v5\`
- `\\f\sms\tidal_databases\tpxo10_atlas_v2\`
- `\\f\sms\tidal_databases\tpxo10v2\`

## Findings summary

### Layout per product

| Product | Layout | Grid | # cons | Storage |
|---|---|---|---|---|
| **TPXO9-atlas-v5** | per-constituent (one file per con per quantity) | 10800 × 5401 (1/30°) | 15 | `int` millimeter |
| **TPXO10-atlas-v2** | per-constituent | 10800 × 5401 (1/30°) | 15 | `int` millimeter |
| **TPXO10v2** | **consolidated** (one file holds all cons stacked along `nc` dim) | 2160 × 1081 (1/6°) | 25 | `double` meter |

**Spec correction**: the design spec (§5, §3 table) assumed TPXO10v2 would be per-constituent. It is not — it follows the same consolidated single-file pattern as the legacy TPXO9v2 distribution.

### Filename conventions (verified, not guessed)

**TPXO9-atlas-v5**:
- Grid: `grid_tpxo9_atlas_30_v5.nc`
- Elevation per con: `h_<con>_tpxo9_atlas_30_v5.nc`
- Transport per con: `u_<con>_tpxo9_atlas_30_v5.nc` (holds both U and V components)

**TPXO10-atlas-v2**:
- Grid: `grid_tpxo10atlas_v2.nc` (note: no underscore before `atlas`)
- Elevation per con: `h_<con>_tpxo10_atlas_30_v2.nc`
- Transport per con: `u_<con>_tpxo10_atlas_30_v2.nc`

**TPXO10v2** (consolidated):
- Grid: `grid_tpxo10v2.nc`
- Elevation: `h_tpxo10.v2.nc` (all 25 cons in one file)
- Transport: `u_tpxo10.v2.nc`
- Manifest: `Model_tpxo10v2.nc` — **not netCDF**, a 3-line legacy OTIS Fortran text file pointing at the three real files. Ignore in the loader.

In each `<con>` slot the constituent name is lowercase: `m2`, `s2`, `n2`, `k1`, `o1`, etc.

### Constituent lists

**Both atlases (TPXO9-atlas-v5 and TPXO10-atlas-v2), 15 cons** — identical set, same as legacy TPXO9v2:

```
2N2, K1, K2, M2, M4, MF, MM, MN4, MS4, N2, O1, P1, Q1, S1, S2
```

**TPXO10v2, 25 cons** (read from the `con(nc=25, nct=4)` char array in `h_tpxo10.v2.nc`):

```
M2, S2, N2, K2, K1, O1, P1, Q1, MM, MF, MSF, M4, MN4, MS4, 2N2,
S1, 2Q1, J1, L2, M3, MU2, NU2, OO1, T2, M1
```

(Adds 10 cons over the legacy TPXO9 set: MSF, 2Q1, J1, L2, M3, MU2, NU2, OO1, T2, M1.)

### Variable schema — elevation files (what harmonica reads)

Harmonica's loader (`tpxo_database.py`) reads four variables: `lat_z`, `lon_z`, `hRe`, `hIm`.
**All three new products use these exact names.** ✓ No per-resource var-name attributes needed (which §5 had listed as a fallback).

Detailed schema differences:

| Aspect | Atlas products | TPXO10v2 (consolidated) |
|---|---|---|
| Coord shape | 1-D: `lon_z(nx)`, `lat_z(ny)` | 2-D: `lon_z(nx, ny)`, `lat_z(nx, ny)` |
| Re/Im shape | `hRe(nx, ny)`, `hIm(nx, ny)` | `hRe(nc, nx, ny)`, `hIm(nc, nx, ny)` |
| Re/Im dtype | `int` | `double` |
| Re/Im units | `millimeter` | `meter` |
| `con` shape | `con(nct=4)` — single name per file | `con(nc=25, nct=4)` — array of names |
| `units_multiplier` | `0.001` | `1.0` |

The 2-D coord shape on TPXO10v2 is already handled by the existing TPXO9-legacy code path:

```python
# tpxo_database.py:65-68
if 'nx' in dset.lat_z.dims:
    dset['lat_z'] = dset.lat_z.sel(nx=0, drop=True)
if 'ny' in dset.lon_z.dims:
    dset['lon_z'] = dset.lon_z.sel(ny=0, drop=True)
```

This squeeze converts 2-D coord arrays to 1-D for the bilinear interp slice. TPXO10v2 will exercise this path; the atlas products will skip it (their coords are already 1-D).

### Variable schema — transport/current files (out of scope but documented)

Harmonica's `get_components()` is elevation-only. Currents would be a separate feature. For future reference:

| Aspect | Atlas products (`u_*.nc`) | TPXO10v2 (`u_tpxo10.v2.nc`) |
|---|---|---|
| Transport (W→E) | `uRe`, `uIm` — `int`, cm²/s | `URe`, `UIm` — `float`, m²/s (note uppercase) |
| Transport (S→N) | `vRe`, `vIm` — `int`, cm²/s | `VRe`, `VIm` — `float`, m²/s |
| Velocity (alt form) | — | `ua`, `va` — `float`, cm/s + `up`, `vp` phase |
| Amplitude (alt form) | — | `Ua`, `Va` — `float`, m²/s + `up`, `vp` phase |
| Coord nodes | separate `lon_u`/`lat_u`, `lon_v`/`lat_v` per Arakawa C-grid | same |

Both consolidated and per-con transport files use the OTIS Arakawa C-grid convention (U-nodes at lon-faces, V-nodes at lat-faces, Z-nodes at cell centers).

## Loader change required

The single-line hard-coded check at `tpxo_database.py:61`:

```python
single_file = self.model == 'tpxo9'
```

becomes:

```python
single_file = getattr(self.resources, 'is_consolidated_file', False)
```

Each resource class sets the flag explicitly:

| Resource class | `is_consolidated_file` |
|---|---|
| `Tpxo8Resources` | `False` (default) |
| `Tpxo9Resources` (legacy) | `True` |
| `Tpxo9AtlasResources` (new) | `False` |
| `Tpxo10Resources` (new) | `True` |
| `Tpxo10AtlasResources` (new) | `False` |

No other loader changes needed. The existing dim squeeze (lines 65-68), the per-con vs multi-con `nc_names` branch (lines 70-73), and the conditional `query` slice (lines 103-106) already cover both topologies.

## Resource entries required

In `resource.py`, three new classes following the existing `Tpxo8Resources` shape:

### `Tpxo9AtlasResources`

- 15 cons (same set as legacy TPXO9)
- `units_multiplier = 0.001`
- `resource_attributes`: `url=None`, `archive=None` (licensed, registration required)
- `is_consolidated_file = False`
- `constituent_resource('M2')` → `'h_m2_tpxo9_atlas_30_v5.nc'` (and analogous lowercase mapping for the other 14)
- `constituent_groups()` → `[<all 15>]` (single group; the atlas data is uniform 1/30°)

### `Tpxo10Resources`

- 25 cons
- `units_multiplier = 1.0`
- `resource_attributes`: `url=None`, `archive=None`
- `is_consolidated_file = True`
- `DEFAULT_RESOURCE_FILE = 'h_tpxo10.v2.nc'`
- `constituent_resource(con)` returns `DEFAULT_RESOURCE_FILE` if `con` is in the 25-element set, else `None` (same pattern as legacy `Tpxo9Resources`)

### `Tpxo10AtlasResources`

- 15 cons (same set as TPXO9-atlas-v5)
- `units_multiplier = 0.001`
- `resource_attributes`: `url=None`, `archive=None`
- `is_consolidated_file = False`
- `constituent_resource('M2')` → `'h_m2_tpxo10_atlas_30_v2.nc'` (and analogous mapping for the other 14)
- `constituent_groups()` → `[<all 15>]`

### Registry updates

```python
RESOURCES = {
    'tpxo8': Tpxo8Resources(),
    'tpxo9': Tpxo9Resources(),
    'tpxo9_atlas': Tpxo9AtlasResources(),    # new
    'tpxo10': Tpxo10Resources(),             # new
    'tpxo10_atlas': Tpxo10AtlasResources(),  # new
    'leprovost': LeProvostResources(),
    'fes2014': FES2014Resources(),
    'adcirc2015': Adcirc2015Resources(),
}
TPXO_MODELS = {'tpxo8', 'tpxo9', 'tpxo9_atlas', 'tpxo10', 'tpxo10_atlas'}
DEFAULT_RESOURCE = 'tpxo10_atlas'  # was 'tpxo9'
```

## Spec deltas — what to update in the design spec

The companion design spec was written before Phase 0 data was available. The following items in §5 need correction (captured in this note's findings and in the spec's "Phase 0 closure" section):

1. **TPXO10v2 is consolidated, not per-constituent.** Spec table §4 had it correct ("per-constituent" was actually wrong in the working spec table — should be "consolidated"), and spec §5 table named `Tpxo10Resources` as per-con. Reality: consolidated, single file, 25 cons.
2. **Filename `h_tpxo10_v2.nc` (spec guess) is wrong.** Actual: `h_tpxo10.v2.nc` (dot, not underscore, before `v2`).
3. **Filename pattern for atlas products** is `_30_v5.nc` / `_30_v2.nc` — the `_30_` segment encoding 1/30° resolution wasn't in the spec's guess.
4. **Constituent counts**: spec said "17 advertised TPXO10 constituents." Actual TPXO10v2 has 25; both atlases have 15.
5. **Variable names match** harmonica's existing `lat_z`/`lon_z`/`hRe`/`hIm` — no per-resource var-name attributes needed (the spec's contingency in §5 is moot).
6. **Unit multipliers**: atlases need `0.001` (int mm), TPXO10v2 needs `1.0` (double m). Not surprising relative to TPXO8 (mm) / TPXO9 (m), but worth pinning.

## Out of scope from this Phase 0

- Currents/transport extraction (documented above for future reference).
- Test-data hosting strategy. The full datasets are too large to commit (10800 × 5401 grids); CI fixtures will need clipped subsets. Decision deferred to the implementation plan.
- The `Model_<product>.nc` legacy OTIS Fortran manifest files. Ignored by harmonica.

## Next step

Phase 0 closed. Phase 1 (implementation) can proceed using the writing-plans skill against this note + the companion design spec.
