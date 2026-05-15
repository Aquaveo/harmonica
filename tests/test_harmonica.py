"""Tests the supported tidal database models."""

# 1. Standard Python modules
import datetime
import filecmp
import os
from unittest.mock import patch

# 2. Third party modules
import numpy as np
import pandas as pd

# 3. Aquaveo modules

# 4. Local modules
from harmonica import config
from harmonica.tidal_constituents import Constituents


WINDOWS_CI_TEST_DATA_DIR = r'\\f\sms\tidal_databases'


class TestHarmonica:
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
    def setup_class(cls):
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
        assert filecmp.cmp(f'{model}.base', f'{model}.out')

    def _run_case_tol(self, model):
        """Run the test case but use some tolerance when comparing to the baseline.

        Args:
            model (str): Name of the model to test
        """
        model_data = self.extractor.get_components(self.LOCS, self.CONS, True, model)
        assert 5 == len(model_data.data)
        for i, pt in enumerate(model_data.data):
            df = pd.read_csv(f'{model}.{i}.base', index_col=0)
            assert np.allclose(df.values, pt.values, equal_nan=True)

    def _run_eq_args_case(self, case_name, start, rundays):
        middle = start + datetime.timedelta(days=rundays / 2)
        nodal_factors = self.extractor.get_nodal_factor(self.EQ_ARG_CONS, start, middle)
        with open(f'{case_name}.out', 'w', newline='') as f:
            f.write(f'{nodal_factors.to_string()}\n\n')
        assert filecmp.cmp(f'{case_name}.base', f'{case_name}.out')

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
        self._run_case_tol('fes2014')

    def test_tpxo8(self):
        """Test tidal extraction for the TPXO8 model."""
        self._run_case('tpxo8')

    def test_tpxo9(self):
        """Test tidal extraction for the TPXO9 model."""
        self._run_case('tpxo9')

    def test_resource_is_consolidated_file_flags(self):
        """Each TPXO resource declares whether its data is consolidated into one file."""
        from harmonica.resource import Tpxo8Resources, Tpxo9Resources
        assert Tpxo8Resources().is_consolidated_file is False
        assert Tpxo9Resources().is_consolidated_file is True

    def test_resource_data_dir_name_defaults_to_none(self):
        """data_dir_name defaults to None so existing models keep using self.model as dir."""
        from harmonica.resource import Tpxo8Resources, Tpxo9Resources
        assert getattr(Tpxo8Resources(), 'data_dir_name', None) is None
        assert getattr(Tpxo9Resources(), 'data_dir_name', None) is None

    def test_data_dir_exists_honors_data_dir_name(self):
        """data_dir_exists looks under data_dir_name when set, falls back to model name otherwise."""
        from harmonica.resource import ResourceManager, Tpxo8Resources
        # Stub a resource class with a custom data_dir_name and patch it into RESOURCES
        class FakeResource(Tpxo8Resources):
            data_dir_name = 'fake_versioned_dir'
        fake_model = '_fake_test_model_'
        with patch.dict(ResourceManager.RESOURCES, {fake_model: FakeResource()}):
            # Patch isdir so only the 'fake_versioned_dir' path returns True
            def isdir_predicate(path):
                return path.endswith(os.sep + 'fake_versioned_dir')
            with patch('harmonica.resource.os.path.isdir', side_effect=isdir_predicate):
                assert ResourceManager.data_dir_exists(fake_model) is True
            # And when the dir isn't there, returns False
            with patch('harmonica.resource.os.path.isdir', return_value=False):
                assert ResourceManager.data_dir_exists(fake_model) is False
        # Backward compat: existing model without data_dir_name still uses the raw model name
        with patch('harmonica.resource.os.path.isdir', return_value=False):
            assert ResourceManager.data_dir_exists('tpxo8') is False

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
