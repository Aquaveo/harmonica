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

    def test_nodal_factor(self):
        """Test extracting astronomical nodal factor data (not dependent on the tidal model)."""
        nodal_factors = self.extractor.get_nodal_factor(self.CONS, datetime.datetime(2018, 8, 30, 15))
        with open('nodal_factor.out', 'w', newline='') as f:
            f.write(f'{nodal_factors.to_string()}\n\n')
        self.assertTrue(filecmp.cmp('nodal_factor.base', 'nodal_factor.out'))

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
