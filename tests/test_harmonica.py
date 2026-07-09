"""Tests the supported tidal database models."""

# 1. Standard Python modules
import datetime
import filecmp
import os
from unittest.mock import patch

# 2. Third party modules
import numpy as np
import pandas as pd
import pytest

# 3. Aquaveo modules

# 4. Local modules
from harmonica import config
from harmonica.tidal_constituents import Constituents


WINDOWS_CI_TEST_DATA_DIR = r'\\f\sms\tidal_databases'

# Models whose get_components() reads a gridded or mesh database. The refactor-safety net below exercises each so a
# later vectorization / batched-DataFrame rewrite (Findings 2 & 3) can be validated numerically instead of byte-exact.
EXTRACTION_MODELS = ['adcirc2015', 'leprovost', 'fes2014', 'tpxo8', 'tpxo9', 'tpxo9_atlas', 'tpxo10', 'tpxo10_atlas']
# One representative model per distinct extraction code path (consolidated TPXO, per-constituent TPXO, LeProvost 2-D
# grid, ADCIRC mesh), used for the more expensive per-point property tests.
REPRESENTATIVE_MODELS = ['tpxo9', 'tpxo10_atlas', 'leprovost', 'adcirc2015']
# Models with explicit out-of-domain handling that returns NaN rather than raising.
NAN_MODELS = ['leprovost', 'adcirc2015']


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
    # A dry-land point outside every model's ocean domain, used to pin the missing-data (NaN) behavior.
    OUT_OF_DOMAIN_LOC = (23.0, 12.0)  # Sahara desert
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

    def test_tpxo9_atlas(self):
        """Test tidal extraction for the TPXO9-atlas-v5 model."""
        self._run_case('tpxo9_atlas')

    def test_tpxo10(self):
        """Test tidal extraction for the TPXO10v2 model."""
        self._run_case('tpxo10')

    def test_tpxo10_atlas(self):
        """Test tidal extraction for the TPXO10-atlas-v2 model (default)."""
        self._run_case('tpxo10_atlas')

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

    def test_default_resource_is_tpxo10_atlas(self):
        """Harmonica's default tidal model is now TPXO10-atlas (was TPXO9)."""
        from harmonica.resource import ResourceManager
        from harmonica.tpxo_database import DEFAULT_TPXO_RESOURCE
        assert ResourceManager.DEFAULT_RESOURCE == 'tpxo10_atlas'
        assert DEFAULT_TPXO_RESOURCE == 'tpxo10_atlas'

    # ------------------------------------------------------------------------------------------------------------
    # Refactor-safety net for the get_components() optimizations (Findings 2 & 3).
    # These characterize the current (assumed-correct) extraction behavior so a later vectorization / batched-
    # DataFrame rewrite can be validated numerically instead of byte-for-byte -- last-bit reordering from
    # vectorization breaks the filecmp .base fixtures even when the result is still correct.
    # ------------------------------------------------------------------------------------------------------------

    @staticmethod
    def _extract(locs: list[tuple[float, float]], cons: list[str] | None, positive_ph: bool,
                 model: str) -> list[pd.DataFrame]:
        """Run one extraction and return the parallel list of per-point constituent frames.

        Args:
            locs: Point locations as (latitude, longitude) tuples.
            cons: Constituent names to extract, or None for every available constituent.
            positive_ph: Report phases in [0, 360] (True) or [-180, 180] (False).
            model: Name of the tidal model to extract from.

        Returns:
            One DataFrame per location, parallel with locs.
        """
        return Constituents().get_components(list(locs), cons, positive_ph, model).data

    @staticmethod
    def _assert_extraction_schema(df: pd.DataFrame) -> None:
        """Assert a constituent frame keeps the expected columns, float dtypes, and a unique index.

        Guards Finding 3 (batched DataFrame construction); a np.allclose value check cannot see a dtype or
        column-order regression.

        Args:
            df: A single point's constituent DataFrame from get_components().
        """
        assert list(df.columns) == ['amplitude', 'phase', 'speed']
        assert len(df.index) > 0, 'expected at least one constituent row'
        assert len(df.index) == len(set(df.index)), 'constituent index must be unique'
        for column in df.columns:
            assert df[column].dtype == np.float64, f'{column} must stay float64, got {df[column].dtype}'

    @staticmethod
    def _assert_frames_close(actual: pd.DataFrame, expected: pd.DataFrame, context: str) -> None:
        """Assert two constituent frames agree, comparing the tide as a complex vector.

        The tide is compared as ``amplitude * e^(i * phase)`` via the magnitude of the difference, toleranced
        relative to amplitude, rather than amplitude and phase separately. A phase difference on a
        near-zero-amplitude constituent -- whose polar phase is ill-conditioned and varies by a few ULP across
        platforms (transcendental functions) -- yields a proportionally tiny vector difference, while a real
        interpolation error, which moves the vector by O(amplitude), still fails. This also sidesteps the 0/360
        phase wrap; amplitude agreement is implied by the vector magnitude. Rows are aligned by constituent name
        first, so the check is independent of the order get_components() emits rows in.

        Args:
            actual: Frame produced by the code under test.
            expected: Frame to compare against (golden snapshot or a second extraction).
            context: Human-readable label included in assertion messages.
        """
        expected = expected.reindex(actual.index)
        amp_a, ph_a, sp_a = (actual['amplitude'].to_numpy(), actual['phase'].to_numpy(),
                             actual['speed'].to_numpy())
        amp_e, ph_e, sp_e = (expected['amplitude'].to_numpy(), expected['phase'].to_numpy(),
                             expected['speed'].to_numpy())
        assert np.array_equal(np.isnan(amp_a), np.isnan(amp_e)), f'{context}: NaN pattern'
        valid = ~np.isnan(amp_a)
        tide_a = amp_a[valid] * np.exp(1j * np.radians(ph_a[valid]))
        tide_e = amp_e[valid] * np.exp(1j * np.radians(ph_e[valid]))
        tolerance = 1e-4 * np.abs(tide_e) + 1e-8
        assert np.all(np.abs(tide_a - tide_e) <= tolerance), f'{context}: tide vector'
        assert np.allclose(sp_a, sp_e, rtol=1e-9, atol=1e-12, equal_nan=True), f'{context}: speed'

    def test_frames_close_tolerates_low_amplitude_phase_noise(self) -> None:
        """The comparator accepts platform-dependent phase jitter on a near-zero-amplitude constituent.

        Reproduces the cross-environment difference that failed CI: EPS2 (amplitude ~0.004 m) whose phase
        differed by ~2e-4 degrees between the golden-generating machine and CI must not be flagged.
        """
        actual = pd.DataFrame({'amplitude': [0.003920], 'phase': [0.842094], 'speed': [np.nan]}, index=['EPS2'])
        expected = pd.DataFrame({'amplitude': [0.003920], 'phase': [0.842324], 'speed': [np.nan]}, index=['EPS2'])
        self._assert_frames_close(actual, expected, 'low-amplitude noise')

    def test_frames_close_rejects_real_phase_error(self) -> None:
        """The comparator still fails on a genuine phase error at a normal amplitude."""
        actual = pd.DataFrame({'amplitude': [0.5], 'phase': [105.0], 'speed': [28.984104]}, index=['M2'])
        expected = pd.DataFrame({'amplitude': [0.5], 'phase': [100.0], 'speed': [28.984104]}, index=['M2'])
        with pytest.raises(AssertionError):
            self._assert_frames_close(actual, expected, 'real phase error')

    @pytest.mark.parametrize('model', EXTRACTION_MODELS)
    def test_extraction_snapshot(self, model: str) -> None:
        """Every model's all-constituent extraction matches its committed numeric golden.

        Primary numeric regression net for Findings 2 & 3: tolerance-based (survives last-bit reordering) and
        covers every constituent, not just the four in the byte-exact fixtures.

        Args:
            model: Name of the tidal model under test (parametrized).
        """
        data = self._extract(self.LOCS, None, True, model)
        assert len(data) == len(self.LOCS)
        golden = pd.read_csv(f'{model}.tol.base')
        for i, pt in enumerate(data):
            self._assert_extraction_schema(pt)
            expected = golden[golden['point'] == i].set_index('con')[['amplitude', 'phase', 'speed']]
            self._assert_frames_close(pt, expected, f'{model} snapshot point {i}')

    @pytest.mark.parametrize('model', REPRESENTATIVE_MODELS)
    def test_batch_matches_single_point(self, model: str) -> None:
        """Extracting a point inside a batch equals extracting it on its own.

        This is the core contract a vectorized get_components() must preserve (Finding 2): the batched result
        for point i must equal the standalone result for point i.

        Args:
            model: Representative model for one extraction code path (parametrized).
        """
        batch = self._extract(self.LOCS, self.CONS, True, model)
        assert len(batch) == len(self.LOCS)
        for i, loc in enumerate(self.LOCS):
            single = self._extract([loc], self.CONS, True, model)
            assert len(single) == 1
            self._assert_frames_close(batch[i], single[0], f'{model} batch-vs-single point {i}')

    @pytest.mark.parametrize('model', REPRESENTATIVE_MODELS)
    def test_output_order_preserved(self, model: str) -> None:
        """Output frames stay parallel with the input locations when the input order is reversed.

        Guards against a vectorized rewrite scrambling point order via a reshape or argsort.

        Args:
            model: Representative model for one extraction code path (parametrized).
        """
        forward = self._extract(self.LOCS, self.CONS, True, model)
        reverse = self._extract(list(reversed(self.LOCS)), self.CONS, True, model)
        count = len(self.LOCS)
        assert len(reverse) == count
        for i in range(count):
            self._assert_frames_close(reverse[count - 1 - i], forward[i], f'{model} reversed point {i}')

    @pytest.mark.parametrize('model', REPRESENTATIVE_MODELS)
    def test_positive_ph_branches(self, model: str) -> None:
        """positive_ph shifts only negative phases by 360 and never changes amplitude or speed.

        Exercises both sides of the ``ph + (360 if positive_ph and ph < 0 else 0)`` branch, which a vectorized
        rewrite would express as a np.where and could get wrong.

        Args:
            model: Representative model for one extraction code path (parametrized).
        """
        # Note: only the TPXO extractor honors positive_ph=False (its np.angle output is [-180, 180]). LeProvost
        # and ADCIRC always emit phase in [0, 360] regardless of the flag, so for those the mapping below is an
        # identity. The assertion is written to hold for both behaviors -- it pins whichever is current.
        positive = self._extract(self.LOCS, self.CONS, True, model)
        signed = self._extract(self.LOCS, self.CONS, False, model)
        for pt_pos, pt_signed in zip(positive, signed):
            pt_signed = pt_signed.reindex(pt_pos.index)
            assert np.allclose(pt_pos['amplitude'].to_numpy(), pt_signed['amplitude'].to_numpy(),
                               rtol=1e-6, atol=1e-9, equal_nan=True), f'{model}: amplitude changed with positive_ph'
            signed_ph = pt_signed['phase'].to_numpy()
            expected_pos = np.where(signed_ph < 0.0, signed_ph + 360.0, signed_ph)
            assert np.allclose(pt_pos['phase'].to_numpy(), expected_pos, atol=1e-9, equal_nan=True), \
                f'{model}: positive_ph did not shift negative phases by 360'

    @pytest.mark.parametrize('model', REPRESENTATIVE_MODELS)
    def test_single_point_extraction(self, model: str) -> None:
        """A length-1 location list returns a single well-formed frame equal to the batch row.

        Length-1 inputs are where vectorized code tends to break on shape (1,) versus scalar.

        Args:
            model: Representative model for one extraction code path (parametrized).
        """
        single = self._extract([self.LOCS[0]], self.CONS, True, model)
        assert len(single) == 1
        self._assert_extraction_schema(single[0])
        batch = self._extract(self.LOCS, self.CONS, True, model)
        self._assert_frames_close(single[0], batch[0], f'{model} single point')

    @pytest.mark.parametrize('model', NAN_MODELS)
    def test_out_of_domain_isolated_nan(self, model: str) -> None:
        """An out-of-domain point yields all-NaN without contaminating a valid point in the same batch.

        Pins the per-point NaN placement that batched DataFrame construction (Finding 3) must keep isolated.

        Args:
            model: A model with explicit out-of-domain (NaN) handling (parametrized).
        """
        data = self._extract([self.LOCS[0], self.OUT_OF_DOMAIN_LOC], None, True, model)
        assert len(data) == 2
        assert np.isfinite(data[0]['amplitude'].to_numpy()).any(), f'{model}: valid point unexpectedly all-NaN'
        assert np.isnan(data[1]['amplitude'].to_numpy()).all(), f'{model}: out-of-domain point should be all-NaN'

    def test_empty_locs_returns_empty(self) -> None:
        """An empty location list returns an empty result list rather than raising."""
        assert self._extract([], self.CONS, True, 'tpxo9') == []
