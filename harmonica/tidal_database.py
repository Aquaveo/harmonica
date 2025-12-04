"""Base class for the tidal database models."""

# 1. Standard Python modules
from abc import ABCMeta, abstractmethod
import math

# 2. Third party modules
import numpy
import pandas as pd

# 3. Aquaveo modules

# 4. Local modules
from .resource import ResourceManager


NCNST = 37

# Dictionary of NOAA constituent speed constants (deg/hr)
# Source: https://tidesandcurrents.noaa.gov
# The speed is the rate change in the phase of a constituent, and is equal to 360 degrees divided by the
# constituent period expressed in hours
# name: (speed, amplitude, frequency, ETRF)
NOAA_SPEEDS = {
    'OO1': (16.139101, 0.0, 0.00007824457305, 0.069),
    '2Q1': (12.854286, 0.0, 0.000062319338107, 0.069),
    '2MK3': (42.92714, 0.0, 0.000208116646659, 0.069),
    '2N2': (27.895355, 0.0, 0.000135240496464, 0.069),
    '2SM2': (31.015896, 0.0, 0.000150369306157, 0.069),
    'K1': (15.041069, 0.141565, 0.000072921158358, 0.736),
    'K2': (30.082138, 0.030704, 0.000145842317201, 0.693),
    'J1': (15.5854435, 0.0, 0.00007556036138, 0.069),
    'L2': (29.528479, 0.0, 0.000143158105531, 0.069),
    'LAM2': (29.455626, 0.0, 0.000142804901311, 0.069),
    'M1': (14.496694, 0.0, 0.000070281955336, 0.069),
    'M2': (28.984104, 0.242334, 0.000140518902509, 0.693),
    'M3': (43.47616, 0.0, 0.000210778353763, 0.069),
    'M4': (57.96821, 0.0, 0.000281037805017, 0.069),
    'M6': (86.95232, 0.0, 0.000421556708011, 0.069),
    'M8': (115.93642, 0.0, 0.000562075610519, 0.069),
    'MF': (1.0980331, 0.0, 0.000005323414692, 0.069),
    'MK3': (44.025173, 0.0, 0.000213440061351, 0.069),
    'MM': (0.5443747, 0.0, 0.000002639203022, 0.069),
    'MN4': (57.423832, 0.0, 0.000278398601995, 0.069),
    'MS4': (58.984104, 0.0, 0.000285963006842, 0.069),
    'MSF': (1.0158958, 0.0, 0.000004925201824, 0.069),
    'MU2': (27.968208, 0.0, 0.000135593700684, 0.069),
    'N2': (28.43973, 0.046398, 0.000137879699487, 0.693),
    'NU2': (28.512583, 0.0, 0.000138232903707, 0.069),
    'O1': (13.943035, 0.100514, 0.000067597744151, 0.695),
    'P1': (14.958931, 0.046834, 0.000072522945975, 0.706),
    'Q1': (13.398661, 0.019256, 0.000064958541129, 0.695),
    'R2': (30.041067, 0.0, 0.000145643201313, 0.069),
    'RHO': (13.471515, 0.0, 0.000065311745349, 0.069),
    'S1': (15.0, 0.0, 0.000072722052166, 0.069),
    'S2': (30.0, 0.112841, 0.000145444104333, 0.693),
    'S4': (60.0, 0.0, 0.000290888208666, 0.069),
    'S6': (90.0, 0.0, 0.000436332312999, 0.069),
    'SA': (0.0410686, 0.0, 0.000000199106191, 0.069),
    'SSA': (0.0821373, 0.0, 0.000000398212868, 0.069),
    'T2': (29.958933, 0.0, 0.000145245007353, 0.069),
}


def get_complex_components(amps, phases):
    """Get the real and imaginary components of amplitudes and phases.

    Args:
        amps (:obj:`list` of :obj:`float`): List of constituent amplitudes
        phases (:obj:`list` of :obj:`float`): List of constituent phases in radians

    Returns:
        :obj:`list` of :obj:`tuple` of :obj:`float`: The list of the complex components,
            e.g. [[real1, imag1], [real2, imag2]]

    """
    components = [[0.0, 0.0] for _ in range(len(amps))]
    for idx, (amp, phase) in enumerate(zip(amps, phases)):
        components[idx][0] = amp * math.cos(phase)
        components[idx][1] = amp * math.sin(phase)
    return components


def convert_coords(coords, zero_to_360=False):
    """Convert latitude coordinates to [-180, 180] or [0, 360].

    Args:
        coords (:obj:`list` of :obj:`tuple` of :obj:`float`): latitude [-90, 90] and longitude [-180 180] or [0 360]
            of the requested point.
        zero_to_360 (:obj:`bool`, optional) If True, coordinates will be converted to the [0, 360] range. If False,
            coordinates will be converted to the [-180, 180] range.

    Returns:
        :obj:`list` of :obj:`tuple` of :obj:`float`: The list of converted coordinates. None if a coordinate out of
            range was encountered

    """
    # Make sure point locations are valid lat/lon
    for idx, pt in enumerate(coords):
        y_lat = pt[0]
        x_lon = pt[1]
        if x_lon < 0.0:
            x_lon += 360.0
        if not zero_to_360 and x_lon > 180.0:
            x_lon -= 360.0

        bad_lat = y_lat > 90.0 or y_lat < -90.0  # Invalid latitude
        bad_lon = not zero_to_360 and (x_lon > 180.0 or x_lon < -180.0)  # Invalid [-180, 180]
        bad_lon = bad_lon or (zero_to_360 and (x_lon > 360.0 or x_lon < 0.0))  # Invalid [0, 360]
        if bad_lat or bad_lon:
            # ERROR: Not in latitude/longitude
            return None
        else:
            coords[idx] = (y_lat, x_lon)
    return coords


class OrbitVariables(object):
    """Container for variables used in astronomical equations.

    Attributes:
        astro (:obj:`pytides.astro.astro`): Orbit variables obtained from pytides.
        grterm (:obj:`dict` of :obj:`float`): Dictionary of equilibrium arguments where the key is constituent name
        nodfac (:obj:`dict` of :obj:`float`): Dictionary of nodal factors where the key is constituent name

    """
    def __init__(self):
        """Construct the container."""
        self.astro = {}
        self.grterm = {con: 0.0 for con in NOAA_SPEEDS}
        self.nodfac = {con: 0.0 for con in NOAA_SPEEDS}


class TidalDB(object):
    """The base class for extracting tidal data from a database.

    Attributes:
        orbit (:obj:`OrbitVariables`): The orbit variables.
        data (:obj:`list` of :obj:`pandas.DataFrame`): List of the constituent component DataFrames with one
            per point location requested from get_components(). Intended return value of get_components().
        resources (:obj:`harmonica.resource.ResourceManager`): Manages fetching of tidal data

    """
    """(:obj:`list` of :obj:`float`): The starting days of the months (non-leap year)."""
    day_t = [0.0, 31.0, 59.0, 90.0, 120.0, 151.0, 181.0, 212.0, 243.0, 273.0, 304.0, 334.0]

    def __init__(self, model):
        """Base class constructor for the tidal extractors.

        Args:
            model (str): The name of the model. See resource.py for supported models.
        """
        self.orbit = OrbitVariables()
        # constituent information dataframe:
        #   amplitude (meters)
        #   phase (degrees)
        #   speed (degrees/hour, UTC/GMT)
        self.data = []
        self.model = model
        self.resources = ResourceManager(self.model)

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_components(self, locs, cons, positive_ph):
        """Abstract method to get amplitude, phase, and speed of specified constituents at specified point locations.

        Args:
            locs (:obj:`list` of :obj:`tuple` of :obj:`float`): latitude [-90, 90] and longitude [-180 180] or [0 360]
                of the requested points.
            cons (:obj:`list` of :obj:`str`, optional): List of the constituent names to get amplitude and phase for. If
                not supplied, all valid constituents will be extracted.
            positive_ph (bool, optional): Indicate if the returned phase should be all positive [0 360] (True) or
                [-180 180] (False, the default).

        Returns:
           :obj:`list` of :obj:`pandas.DataFrame`: Implementations should return a list of dataframes of constituent
                information including amplitude (meters), phase (degrees) and speed (degrees/hour, UTC/GMT). The list is
                parallel with locs, where each element in the return list is the constituent data for the corresponding
                element in locs. Empty list on error. Note that function uses fluent interface pattern.
        """
        pass

    def have_constituent(self, name):
        """Determine if a constituent is valid for this tidal extractor.

        Args:
            name (str): The name of the constituent.

        Returns:
            bool: True if the constituent is valid, False otherwise
        """
        return name.upper() in self.resources.available_constituents()

    def get_nodal_factor(self, names, timestamp, timestamp_middle):
        """Get the nodal factor for specified constituents at a specified time.

        Args:
            names (:obj:`list` of :obj:`str`): Names of the constituents to get nodal factors for
            timestamp (datetime.datetime): Start date and time to extract constituent arguments at
            timestamp_middle (datetime.datetime): Date and time to consider as the middle of the series.

        Returns:
            :obj:`pandas.DataFrame`: Constituent data frames. Each row contains frequency, earth tidal reduction factor,
                amplitude, nodal factor, and equilibrium argument for one of the specified constituents. Rows labeled by
                constituent name.
        """
        con_data = pd.DataFrame(columns=['amplitude', 'frequency', 'speed', 'earth_tide_reduction_factor',
                                         'equilibrium_argument', 'nodal_factor'])
        self.get_eq_args(timestamp, timestamp_middle)
        for name in names:
            name = name.upper()
            if name not in NOAA_SPEEDS:
                con_data.loc[name] = [numpy.nan, numpy.nan, numpy.nan, numpy.nan, numpy.nan, numpy.nan]
            else:
                equilibrium_arg = 0.0
                nodal_factor = self.orbit.nodfac[name]
                if nodal_factor != 0.0:
                    equilibrium_arg = self.orbit.grterm[name]
                con_data.loc[name] = [
                    NOAA_SPEEDS[name][1], NOAA_SPEEDS[name][2], NOAA_SPEEDS[name][0], NOAA_SPEEDS[name][3],
                    equilibrium_arg, nodal_factor
                ]
        return con_data

    def get_eq_args(self, timestamp, timestamp_middle):
        """Get equilibrium arguments at a starting time.

        Args:
            timestamp (datetime.datetime): Date and time to extract constituent arguments at
            timestamp_middle (datetime.datetime): Date and time to consider as the middle of the series
        """
        self.nfacs(timestamp_middle)
        self.gterms(timestamp, timestamp_middle)

    @staticmethod
    def angle(a_number):
        """Converts the angle to be within 0-360.

        Args:
            a_number (float): The angle to convert.

        Returns:
            The angle converted to be within 0-360.
        """
        return a_number % 360.0

    def set_orbit(self, timestamp):
        """Determination of primary and secondary orbital functions.

        Args:
           timestamp (datetime.datetime): Date and time to extract constituent arguments at.
        """
        # We used to rely on pytides for astronomical computations, but it was giving was different results from
        # the tide_fac Fortran utility.
        # from pytides.astro import astro
        # self.orbit.astro = astro(timestamp)

        # Ported code from tide_fac.f
        dayj = timestamp.timetuple().tm_yday  # ordinal day number
        # pi180 = 3.14159265 / 180.0
        x = int((timestamp.year - 1901.) / 4.0)
        dyr = timestamp.year - 1900.0
        dday = dayj + x - 1.0
        # DN IS THE MOON'S NODE (CAPITAL N, TABLE 1, SCHUREMAN)
        dn = 259.1560564 - 19.328185764 * dyr - 0.0529539336 * dday - 0.0022064139 * timestamp.hour
        dn = self.angle(dn)
        n = math.radians(dn)
        # DP IS THE LUNAR PERIGEE (SMALL P, TABLE 1)
        dp = 334.3837214 + 40.66246584 * dyr + 0.111404016 * dday + 0.004641834 * timestamp.hour
        dp = self.angle(dp)
        i = math.acos(0.9136949 - 0.0356926 * math.cos(n))
        di = self.angle(math.degrees(i))
        nu = math.asin(0.0897056 * math.sin(n) / math.sin(i))
        dnu = math.degrees(nu)
        xi = n - 2.0 * math.atan(0.64412 * math.tan(n / 2.0)) - nu
        dxi = math.degrees(xi)
        dpc = self.angle(dp - dxi)
        # DH IS THE MEAN LONGITUDE OF THE SUN (SMALL H, TABLE 1)
        dh = 280.1895014 - 0.238724988 * dyr + 0.9856473288 * dday + 0.0410686387 * timestamp.hour
        dh = self.angle(dh)
        # DP1 IS THE SOLAR PERIGEE (SMALL P1, TABLE 1)
        dp1 = 281.2208569 + 0.01717836 * dyr + 0.000047064 * dday + 0.000001961 * timestamp.hour
        dp1 = self.angle(dp1)
        # DS IS THE MEAN LONGITUDE OF THE MOON (SMALL S, TABLE 1)
        ds = 277.0256206 + 129.38482032 * dyr + 13.176396768 * dday + 0.549016532 * timestamp.hour
        ds = self.angle(ds)
        nup = math.atan(math.sin(nu) / (math.cos(nu) + 0.334766 / math.sin(2.0 * i)))
        dnup = math.degrees(nup)
        nup2 = math.atan(math.sin(2.0 * nu) / (math.cos(2.0 * nu) + 0.0726184 / math.sin(i) ** 2)) / 2.0
        dnup2 = math.degrees(nup2)

        self.orbit.astro = {
            'ds': ds,
            'dp': dp,
            'dh': dh,
            'dp1': dp1,
            'dn': dn,
            'di': di,
            'dnu': dnu,
            'dxi': dxi,
            'dnup': dnup,
            'dnup2': dnup2,
            'dpc': dpc,
        }

    def nfacs(self, timestamp):
        """Calculates node factors for constituent tidal signal.

        Args:
            timestamp (datetime.datetime): Date and time to extract constituent arguments at

        Returns:
            The same values as found in table 14 of Schureman.
        """
        # Ported code from tide_fac.f
        self.set_orbit(timestamp)
        # n = math.radians(self.orbit.astro['dn'])
        i = math.radians(self.orbit.astro['di'])
        nu = math.radians(self.orbit.astro['dnu'])
        # xi = math.radians(self.orbit.astro['dxi'])
        # p = math.radians(self.orbit.astro['dp'])
        # pc = math.radians(self.orbit.astro['dpc'])
        sini = math.sin(i)
        sini2 = math.sin(i / 2.0)
        sin2i = math.sin(2.0 * i)
        cosi2 = math.cos(i / 2.0)
        # tani2 = math.tan(i / 2.0)
        # EQUATION 197, SCHUREMAN
        # qainv = math.sqrt(2.310 + 1.435 * math.cos(2.0 * pc))
        # EQUATION 213, SCHUREMAN
        # rainv = math.sqrt(1.0 - 12.0 * tani2 ** 2 * math.cos(2.0 * pc) + 36.0 * tani2 ** 4)
        # VARIABLE NAMES REFER TO EQUATION NUMBERS IN SCHUREMAN
        eq73 = (2.0 / 3.0 - sini ** 2) / 0.5021
        eq74 = sini ** 2 / 0.1578
        eq75 = sini * cosi2 ** 2 / 0.37988
        eq76 = math.sin(2 * i) / 0.7214
        eq77 = sini * sini2 ** 2 / 0.0164
        eq78 = cosi2 ** 4 / 0.91544
        eq149 = cosi2 ** 6 / 0.8758
        # eq207 = eq75 * qainv
        # eq215 = eq78 * rainv
        eq227 = math.sqrt(0.8965 * sin2i ** 2 + 0.6001 * sin2i * math.cos(nu) + 0.1006)
        eq235 = 0.001 + math.sqrt(19.0444 * sini ** 4 + 2.7702 * sini ** 2 * math.cos(2.0 * nu) + 0.0981)
        # NODE FACTORS FOR 37 CONSTITUENTS:
        self.orbit.nodfac['M2'] = eq78
        self.orbit.nodfac['S2'] = 1.0
        self.orbit.nodfac['N2'] = eq78
        self.orbit.nodfac['K1'] = eq227
        self.orbit.nodfac['M4'] = self.orbit.nodfac['M2'] ** 2
        self.orbit.nodfac['O1'] = eq75
        self.orbit.nodfac['M6'] = self.orbit.nodfac['M2'] ** 3
        self.orbit.nodfac['MK3'] = self.orbit.nodfac['M2'] * self.orbit.nodfac['K1']
        self.orbit.nodfac['S4'] = 1.0
        self.orbit.nodfac['MN4'] = self.orbit.nodfac['M2'] ** 2
        self.orbit.nodfac['NU2'] = eq78
        self.orbit.nodfac['S6'] = 1.0
        self.orbit.nodfac['MU2'] = eq78
        self.orbit.nodfac['2N2'] = eq78
        self.orbit.nodfac['OO1'] = eq77
        self.orbit.nodfac['LAM2'] = eq78
        self.orbit.nodfac['S1'] = 1.0
        # EQUATION 207 NOT PRODUCING CORRECT ANSWER FOR M1
        # SET NODE FACTOR FOR M1 = 0 UNTIL CAN FURTHER RESEARCH
        self.orbit.nodfac['M1'] = 0.0  # = eq207
        self.orbit.nodfac['J1'] = eq76
        self.orbit.nodfac['MM'] = eq73
        self.orbit.nodfac['SSA'] = 1.0
        self.orbit.nodfac['SA'] = 1.0
        self.orbit.nodfac['MSF'] = eq78
        self.orbit.nodfac['MF'] = eq74
        self.orbit.nodfac['RHO'] = eq75
        self.orbit.nodfac['Q1'] = eq75
        self.orbit.nodfac['T2'] = 1.0
        self.orbit.nodfac['R2'] = 1.0
        self.orbit.nodfac['2Q1'] = eq75
        self.orbit.nodfac['P1'] = 1.0
        self.orbit.nodfac['2SM2'] = eq78
        self.orbit.nodfac['M3'] = eq149
        # EQUATION 215 NOT PRODUCING CORRECT ANSWER FOR L2
        # SET NODE FACTOR FOR L2 = 0 UNTIL CAN FURTHER RESEARCH
        self.orbit.nodfac['L2'] = 0.0  # = eq215
        self.orbit.nodfac['2MK3'] = self.orbit.nodfac['M2'] ** 2 * self.orbit.nodfac['K1']
        self.orbit.nodfac['K2'] = eq235
        self.orbit.nodfac['M8'] = self.orbit.nodfac['M2'] ** 4
        self.orbit.nodfac['MS4'] = eq78

    def gterms(self, timestamp, timestamp_middle):
        """Determines the Greenwich equilibrium terms.

        Args:
            timestamp (datetime.datetime): Start date and time to extract constituent arguments at
            timestamp_middle (datetime.datetime): Date and time to consider as the middle of the series
        Returns:
            The same values as found in table 15 of Schureman.
        """
        # Ported code from tide_fac.f
        # OBTAINING ORBITAL VALUES AT BEGINNING OF SERIES FOR V0
        self.set_orbit(timestamp)
        s = self.orbit.astro['ds']
        p = self.orbit.astro['dp']
        h = self.orbit.astro['dh']
        p1 = self.orbit.astro['dp1']
        t = self.angle(180.0 + timestamp.hour * (360.0 / 24.0))

        # OBTAINING ORBITAL VALUES AT MIDDLE OF SERIES FOR U
        self.set_orbit(timestamp_middle)
        nu = self.orbit.astro['dnu']
        xi = self.orbit.astro['dxi']
        nup = self.orbit.astro['dnup']
        nup2 = self.orbit.astro['dnup2']

        # SUMMING TERMS TO OBTAIN EQUILIBRIUM ARGUMENTS
        self.orbit.grterm['M2'] = 2.0 * (t - s + h) + 2.0 * (xi - nu)
        self.orbit.grterm['S2'] = 2.0 * t
        self.orbit.grterm['N2'] = 2.0 * (t + h) - 3.0 * s + p + 2.0 * (xi - nu)
        self.orbit.grterm['K1'] = t + h - 90.0 - nup
        self.orbit.grterm['M4'] = 4.0 * (t - s + h) + 4.0 * (xi - nu)
        self.orbit.grterm['O1'] = t - 2.0 * s + h + 90.0 + 2.0 * xi - nu
        self.orbit.grterm['M6'] = 6.0 * (t - s + h) + 6.0 * (xi - nu)
        self.orbit.grterm['MK3'] = 3.0 * (t + h) - 2.0 * s - 90.0 + 2.0 * (xi - nu) - nup
        self.orbit.grterm['S4'] = 4.0 * t
        self.orbit.grterm['MN4'] = 4.0 * (t + h) - 5.0 * s + p + 4.0 * (xi - nu)
        self.orbit.grterm['NU2'] = 2.0 * t - 3.0 * s + 4.0 * h - p + 2.0 * (xi - nu)
        self.orbit.grterm['S6'] = 6.0 * t
        self.orbit.grterm['MU2'] = 2.0 * (t + 2.0 * (h - s)) + 2.0 * (xi - nu)
        self.orbit.grterm['2N2'] = 2.0 * (t - 2.0 * s + h + p) + 2.0 * (xi - nu)
        self.orbit.grterm['OO1'] = t + 2.0 * s + h - 90.0 - 2.0 * xi - nu
        self.orbit.grterm['LAM2'] = 2.0 * t - s + p + 180.0 + 2.0 * (xi - nu)
        self.orbit.grterm['S1'] = t
        i = math.radians(self.orbit.astro['di'])
        pc = math.radians(self.orbit.astro['dpc'])
        top = (5.0 * math.cos(i) - 1.0) * math.sin(pc)
        bottom = (7.0 * math.cos(i) + 1.0) * math.cos(pc)
        q = self.angle(math.degrees(math.atan2(top, bottom)))
        self.orbit.grterm['M1'] = t - s + h - 90.0 + xi - nu + q
        self.orbit.grterm['J1'] = t + s + h - p - 90.0 - nu
        self.orbit.grterm['MM'] = s - p
        self.orbit.grterm['SSA'] = 2.0 * h
        self.orbit.grterm['SA'] = h
        self.orbit.grterm['MSF'] = 2.0 * (s - h)
        self.orbit.grterm['MF'] = 2.0 * s - 2.0 * xi
        self.orbit.grterm['RHO'] = t + 3.0 * (h - s) - p + 90.0 + 2.0 * xi - nu
        self.orbit.grterm['Q1'] = t - 3.0 * s + h + p + 90.0 + 2.0 * xi - nu
        self.orbit.grterm['T2'] = 2.0 * t - h + p1
        self.orbit.grterm['R2'] = 2.0 * t + h - p1 + 180.0
        self.orbit.grterm['2Q1'] = t - 4.0 * s + h + 2.0 * p + 90.0 + 2.0 * xi - nu
        self.orbit.grterm['P1'] = t - h + 90.0
        self.orbit.grterm['2SM2'] = 2.0 * (t + s - h) + 2.0 * (nu - xi)
        self.orbit.grterm['M3'] = 3.0 * (t - s + h) + 3.0 * (xi - nu)
        r = math.sin(2.0 * pc) / ((1.0 / 6.0) * (1.0 / math.tan(0.5 * i)) ** 2 - math.cos(2.0 * pc))
        r = math.degrees(math.atan(r))
        self.orbit.grterm['L2'] = 2.0 * (t + h) - s - p + 180.0 + 2.0 * (xi - nu) - r
        self.orbit.grterm['2MK3'] = 3.0 * (t + h) - 4.0 * s + 90.0 + 4.0 * (xi - nu) + nup
        self.orbit.grterm['K2'] = 2.0 * (t + h) - 2.0 * nup2
        self.orbit.grterm['M8'] = 8.0 * (t - s + h) + 8.0 * (xi - nu)
        self.orbit.grterm['MS4'] = 2.0 * (2.0 * t - s + h) + 2.0 * (xi - nu)
        for con, value in self.orbit.grterm.items():
            self.orbit.grterm[con] = self.angle(value)
