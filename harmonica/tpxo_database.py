"""Class to manage the TPXO tidal database models."""

# 1. Standard Python modules

# 2. Third party modules
import numpy as np
import pandas as pd

# 3. Aquaveo modules

# 4. Local modules
from .resource import ResourceManager
from .tidal_database import NOAA_SPEEDS, TidalDB


DEFAULT_TPXO_RESOURCE = 'tpxo10_atlas'  # was 'tpxo9'


class TpxoDB(TidalDB):
    """Harmonica tidal constituents."""

    def __init__(self, model=DEFAULT_TPXO_RESOURCE):
        """Constructor for the TPXO tidal extractor.

        Args:
            model (:obj:`str`, optional): The name of the TPXO model. See resource.py for supported models.

        """
        model = model.lower()  # Be case-insensitive
        if model not in ResourceManager.TPXO_MODELS:  # Check for valid TPXO model
            raise ValueError("\'{}\' is not a supported TPXO model. Must be one of: {}.".format(
                model, ", ".join(ResourceManager.TPXO_MODELS).strip()
            ))
        super().__init__(model)

    def get_components(self, locs, cons=None, positive_ph=False):
        """Get the amplitude, phase, and speed of specified constituents at specified point locations.

        Args:
            locs (:obj:`list` of :obj:`tuple` of :obj:`float`): latitude [-90, 90] and longitude [-180 180] or [0 360]
                of the requested points.
            cons (:obj:`list` of :obj:`str`, optional): List of the constituent names to get amplitude and phase for. If
                not supplied, all valid constituents will be extracted.
            positive_ph (bool, optional): Indicate if the returned phase should be all positive [0 360] (True) or
                [-180 180] (False, the default).

        Returns:
           :obj:`list` of :obj:`pandas.DataFrame`: A list of dataframes of constituent information including
                amplitude (meters), phase (degrees) and speed (degrees/hour, UTC/GMT). The list is parallel with locs,
                where each element in the return list is the constituent data for the corresponding element in locs.
                Empty list on error. Note that function uses fluent interface pattern.

        """
        n_locs = len(locs)
        # Accumulate each point's constituent rows, then build one DataFrame per point at the end. This avoids the
        # per-cell DataFrame.loc writes the old inner loop paid for every constituent of every point.
        rows = [{} for _ in range(n_locs)]

        # if no constituents were requested, return all available
        if cons is None or not len(cons):
            cons = list(self.resources.available_constituents())
        requested = set(cons)
        units_multiplier = self.resources.get_units_multiplier()

        # Requested coordinates as arrays; longitudes normalized to [0, 360) exactly as the scalar path did.
        lats = np.array([loc[0] for loc in locs], dtype=float)
        lons = np.array([loc[1] for loc in locs], dtype=float)
        lons = np.where(lons < 0.0, lons + 360.0, lons)

        # open the netcdf database(s)
        single_file = self.resources.model_atts.is_consolidated_file
        for d in self.resources.get_datasets(cons):
            for dset in d:
                # remove unnecessary data array dimensions if present (e.g. tpxo9)
                if 'nx' in dset.lat_z.dims:
                    dset['lat_z'] = dset.lat_z.sel(nx=0, drop=True)
                if 'ny' in dset.lon_z.dims:
                    dset['lon_z'] = dset.lon_z.sel(ny=0, drop=True)
                # get the dataset constituent name array from data cube
                if single_file:
                    nc_names = [x.tobytes().decode('utf-8').strip().upper() for x in dset.con.values]
                else:
                    nc_names = [dset.con.item().decode('utf-8').strip().upper()]

                # Bounding indices for every point at once. bisect(a, x) == np.searchsorted(a, x, side='right'),
                # so these indices (and the edge/longitude-wrap behavior) match the old per-point scalar path.
                lon_z = dset.lon_z.values
                lat_z = dset.lat_z.values
                right = np.searchsorted(lon_z, lons, side='right')
                left = right - 1
                top = np.searchsorted(lat_z, lats, side='right')
                bottom = top - 1
                # Bilinear spline weights per point, shaped (n_locs, 2, 2) to line up with each 2x2 data window
                # (row = lon left/right, col = lat bottom/top), then normalized -- identical layout to the old code.
                dx = (lons - lon_z[left]) / (lon_z[right] - lon_z[left])
                dy = (lats - lat_z[bottom]) / (lat_z[top] - lat_z[bottom])
                weights = np.stack([
                    (1. - dx) * (1. - dy),  # bottom left
                    (1. - dx) * dy,         # bottom right
                    dx * (1. - dy),         # top left
                    dx * dy,                # top right
                ], axis=-1).reshape(n_locs, 2, 2)
                weights = weights / weights.sum(axis=(1, 2), keepdims=True)

                for c in requested & set(nc_names):
                    con_idx = nc_names.index(c) if single_file else 0
                    # Read only each point's 2x2 window from the lazily-opened arrays (never the whole grid),
                    # stacking the windows so the interpolation runs across all points at once.
                    re_block = np.empty((n_locs, 2, 2))
                    im_block = np.empty((n_locs, 2, 2))
                    for i in range(n_locs):
                        if single_file:
                            query = np.s_[con_idx, left[i]:right[i] + 1, bottom[i]:top[i] + 1]
                        else:
                            query = np.s_[left[i]:right[i] + 1, bottom[i]:top[i] + 1]
                        re_block[i] = dset.hRe[query].values
                        im_block[i] = dset.hIm[query].values
                    # weighted tide from the real and imaginary components, vectorized over points
                    real = (re_block * weights).sum(axis=(1, 2))
                    imag = -(im_block * weights).sum(axis=(1, 2))
                    h = real + 1j * imag
                    phase = np.angle(h, deg=True)
                    if positive_ph:
                        phase = np.where(phase < 0.0, phase + 360.0, phase)
                    amplitude = np.absolute(h) * units_multiplier
                    speed = NOAA_SPEEDS[c][0]
                    for i in range(n_locs):
                        rows[i][c] = (float(amplitude[i]), float(phase[i]), speed)

        self.data = [
            pd.DataFrame.from_dict(row, orient='index', columns=['amplitude', 'phase', 'speed'])
            for row in rows
        ]
        return self
