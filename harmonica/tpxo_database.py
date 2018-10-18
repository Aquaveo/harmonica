from .resource import ResourceManager
from .tidal_database import NOAA_SPEEDS, TidalDB

from bisect import bisect
import numpy as np
import pandas as pd


class TpxoDB(TidalDB):
    """Harmonica tidal constituents."""

    def __init__(self, model=ResourceManager.DEFAULT_RESOURCE):
        """Constructor for the TPXO tidal extractor.

        Args:
            model (:obj:`str`, optional): The name of the TPXO model. One of: 'tpxo9', 'tpxo8', 'tpxo7'.
                ResourceManager.DEFAULT_RESOURCE if not specified.
        """
        # constituent information dataframe:
        #   amplitude (meters)
        #   phase (degrees)
        #   speed (degrees/hour, UTC/GMT)
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
        self.data = [pd.DataFrame(columns=['amplitude', 'phase', 'speed']) for _ in range(len(locs))]

        # if no constituents were requested, return all available
        if cons is None or not len(cons):
            cons = self.resources.available_constituents()
        # open the netcdf database(s)
        for d in self.resources.get_datasets(cons):
            # remove unnecessary data array dimensions if present (e.g. tpxo7.2)
            if 'nx' in d.lat_z.dims:
                d['lat_z'] = d.lat_z.sel(nx=0, drop=True)
            if 'ny' in d.lon_z.dims:
                d['lon_z'] = d.lon_z.sel(ny=0, drop=True)
            # get the dataset constituent name array from data cube
            nc_names = [x.tostring().decode('utf-8').strip().upper() for x in d.con.values]
            for c in set(cons) & set(nc_names):
                for i, loc in enumerate(locs):
                    lat, lon = loc
                    # check the phase of the longitude
                    if lon < 0:
                        lon = lon + 360.

                    # get constituent and bounding indices within the data cube
                    idx = {'con': nc_names.index(c)}
                    idx['top'] = bisect(d.lat_z[idx['con']], lat)
                    idx['right'] = bisect(d.lon_z[idx['con']], lon)
                    idx['bottom'] = idx['top'] - 1
                    idx['left'] = idx['right'] - 1
                    # get distance from the bottom left to the requested point
                    dx = (lon - d.lon_z.values[idx['con'], idx['left']]) / \
                         (d.lon_z.values[idx['con'], idx['right']] - d.lon_z.values[idx['con'], idx['left']])
                    dy = (lat - d.lat_z.values[idx['con'], idx['bottom']]) / \
                         (d.lat_z.values[idx['con'], idx['top']] - d.lat_z.values[idx['con'], idx['bottom']])
                    # calculate weights for bilinear spline
                    weights = np.array([
                        (1. - dx) * (1. - dy),  # w00 :: bottom left
                        (1. - dx) * dy,         # w01 :: bottom right
                        dx * (1. - dy),         # w10 :: top left
                        dx * dy                 # w11 :: top right
                    ]).reshape((2, 2))
                    weights = weights / weights.sum()
                    # devise the slice to subset surrounding values
                    query = np.s_[idx['con'], idx['left']:idx['right']+1, idx['bottom']:idx['top']+1]
                    # calculate the weighted tide from real and imaginary components
                    h = np.complex((d.hRe.values[query] * weights).sum(), -(d.hIm.values[query] * weights).sum())
                    # get the phase and amplitude
                    ph = np.angle(h, deg=True)
                    # place info into data table
                    self.data[i].loc[c] = [
                        # amplitude
                        np.absolute(h) * self.resources.get_units_multiplier(),
                        # phase
                        ph + (360. if positive_ph and ph < 0 else 0),
                        # speed
                        NOAA_SPEEDS[c]
                    ]

        return self
