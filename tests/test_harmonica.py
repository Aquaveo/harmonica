"""Tests the supported tidal database models."""
# 1. Standard python modules
import datetime
import filecmp
import os
import unittest

# 2. Third party modules

# 3. Aquaveo modules

# 4. Local modules
from harmonica import config
from harmonica.tidal_constituents import Constituents


WINDOWS_CI_TEST_DATA_DIR = r'\\f\sms\tidal_databases'


class HarmonicaTests(unittest.TestCase):
    """Test harmonica Python interface with all supported models."""
    # Need to be in (lat, lon), not (x, y)
    LOCS = [
        (39.74, -74.07),
        (42.32, -70.0),
        (45.44, -65.0),
        (43.63, -124.55),
        (46.18, -124.38),
    ]
    CONS = ['M2', 'S2', 'N2', 'K1']
    # These are all the constituents that are supported by tide_fac.f in the order it outputs them
    EQ_ARG_CONS = [
        'M2', 'S2', 'N2', 'K1', 'M4', 'O1', 'M6', 'MK3', 'S4', 'MN4', 'NU2', 'S6', 'MU2', '2N2', 'OO1', 'LAM2', 'S1',
        'M1', 'J1', 'MM', 'SSA', 'SA', 'MSF', 'MF', 'RHO', 'Q1', 'T2', 'R2', '2Q1', 'P1', '2SM2', 'M3', 'L2', '2MK3',
        'K2', 'M8', 'MS4'
    ]
    extractor = Constituents()

    @classmethod
    def setUpClass(cls):
        """Runs before all the test cases, set the config variable for a preexisting data dir."""
        # Change working directory to test location
        os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))
        # Use internal Aquaveo data directory to test protected models.
        config['pre_existing_data_dir'] = WINDOWS_CI_TEST_DATA_DIR

    def _run_case(self, model):
        """Run a tidal extraction case for a model.

        Args:
            model (str): Name of the model to test
        """
        model_data = self.extractor.get_components(self.LOCS, self.CONS, True, model)
        with open(f'{model}.out', 'w', newline='') as f:
            for pt in model_data.data:
                f.write(f'{pt.sort_index().to_string()}\n\n')
        self.assertTrue(filecmp.cmp(f'{model}.base', f'{model}.out'))

    def _run_eq_args_case(self, case_name, start, rundays):
        middle = start + datetime.timedelta(days=rundays / 2)
        nodal_factors = self.extractor.get_nodal_factor(self.EQ_ARG_CONS, start, middle)
        with open(f'{case_name}.out', 'w', newline='') as f:
            f.write(f'{nodal_factors.to_string()}\n\n')
        self.assertTrue(filecmp.cmp(f'{case_name}.base', f'{case_name}.out'))

    def test_2015040700_10day(self):
        """Test extracting astronomical nodal factor data (not dependent on the tidal model)."""
        start = datetime.datetime(2015, 4, 7, 0)
        self._run_eq_args_case('2015040700_10day', start, 10)

    def test_2015040700_5day(self):
        """Test extracting astronomical nodal factor data (not dependent on the tidal model)."""
        start = datetime.datetime(2015, 4, 7, 0)
        self._run_eq_args_case('2015040700_5day', start, 5)

    def test_1980072005_20day(self):
        """Test extracting astronomical nodal factor data (not dependent on the tidal model)."""
        start = datetime.datetime(1980, 7, 20, 5)
        self._run_eq_args_case('1980072005_20day', start, 20)

    def test_2100123020_2day(self):
        """Test extracting astronomical nodal factor data (not dependent on the tidal model)."""
        # The fortran code in tide_fac.f incorrectly assumes 2100 is a leap year. It is not because it is a century
        # year, so the Python should be different but presumably more correct in this case.
        start = datetime.datetime(2100, 12, 30, 20)
        self._run_eq_args_case('2100123020_2day', start, 2)

    def test_2101123020_2day(self):
        """Test extracting astronomical nodal factor data (not dependent on the tidal model)."""
        start = datetime.datetime(2101, 12, 30, 20)
        self._run_eq_args_case('2101123020_2day', start, 2)

    def test_adcirc(self):
        """Test tidal extraction for the ADCIRC 2015 model."""
        self._run_case('adcirc2015')

    def test_leprovost(self):
        """Test tidal extraction for the legacy LeProvost model."""
        self._run_case('leprovost')

    def test_fes2014(self):
        """Test tidal extraction for the FES2014 model."""
        self._run_case('fes2014')

    def test_tpxo8(self):
        """Test tidal extraction for the TPXO8 model."""
        self._run_case('tpxo8')

    def test_tpxo9(self):
        """Test tidal extraction for the TPXO9 model."""
        self._run_case('tpxo9')
