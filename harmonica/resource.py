"""Resource managers for the tidal database models supported in harmonica."""

# 1. Standard Python modules
from abc import ABCMeta, abstractmethod
import os
import shutil
import urllib.request
from zipfile import ZipFile

# 2. Third party modules
import xarray as xr

# 3. Aquaveo modules

# 4. Local modules
from harmonica import config


MAX_NUM_CONS = 37  # Maximum number of constituents in all available models


class Resources(object):
    """Abstract base class for model resources."""

    # Default: data is one file per constituent. Override to True for single-file models.
    # Consumed by TpxoDB.get_components to dispatch between the per-con and consolidated code paths.
    is_consolidated_file = False
    # Default: data subdirectory under pre_existing_data_dir matches the model name.
    # Override (e.g. 'tpxo9_atlas_v5') when the on-disk dir is version-suffixed.
    data_dir_name = None

    def __init__(self):
        """Base constructor."""
        pass

    __metaclass__ = ABCMeta

    @abstractmethod
    def resource_attributes(self):
        """Get the resource attributes of a model (e.g. web url, compression type).

        Returns:
            dict: Dictionary of model resource attributes
        """
        return {}

    @abstractmethod
    def dataset_attributes(self):
        """Get the dataset attributes of a model (e.g. unit multiplier, grid dimensions).

        Returns:
            dict: Dictionary of model dataset attributes
        """
        return {}

    @abstractmethod
    def available_constituents(self):
        """Get all the available constituents of a model.

        Returns:
            list: List of all the available constituents
        """
        return []

    @abstractmethod
    def constituent_groups(self):
        """Get all the available constituents of a model grouped by compatible file types.

        Returns:
            list[list]: 2-D list of available constituents, where the first dimension groups compatible files
        """
        return []

    @abstractmethod
    def constituent_resource(self, con):
        """Get the resource name of a constituent.

        Returns:
            str: Name of the constituent's resource
        """
        return None


class Tpxo8Resources(Resources):
    """TPXO8 resources."""
    TPXO8_CONS = [
        {  # 1/30 degree
            'K1': 'hf.k1_tpxo8_atlas_30c_v1.nc',
            'K2': 'hf.k2_tpxo8_atlas_30c_v1.nc',
            'M2': 'hf.m2_tpxo8_atlas_30c_v1.nc',
            'M4': 'hf.m4_tpxo8_atlas_30c_v1.nc',
            'N2': 'hf.n2_tpxo8_atlas_30c_v1.nc',
            'O1': 'hf.o1_tpxo8_atlas_30c_v1.nc',
            'P1': 'hf.p1_tpxo8_atlas_30c_v1.nc',
            'Q1': 'hf.q1_tpxo8_atlas_30c_v1.nc',
            'S2': 'hf.s2_tpxo8_atlas_30c_v1.nc',
        },
        {  # 1/6 degree
            'MF': 'hf.mf_tpxo8_atlas_6.nc',
            'MM': 'hf.mm_tpxo8_atlas_6.nc',
            'MN4': 'hf.mn4_tpxo8_atlas_6.nc',
            'MS4': 'hf.ms4_tpxo8_atlas_6.nc',
        },
    ]

    def __init__(self):
        """Constructor."""
        super().__init__()

    def resource_attributes(self):
        """Returns a dict of the resource attributes that are disabled (TPXO8 is not freely available)."""
        return {
            'url': None,  # Resources must already exist. Licensing restrictions prevent hosting files.
            'archive': None,
        }

    def dataset_attributes(self):
        """Returns a dict of the TPXO8 dataset attributes (currently just 'units_muliplier')."""
        return {
            'units_multiplier': 0.001,  # mm to meter
        }

    def available_constituents(self):
        """Returns a list of the constituents supported by the TPXO8 tidal database."""
        # get keys from const groups as list of lists and flatten
        return [c for sl in [grp.keys() for grp in self.TPXO8_CONS] for c in sl]

    def constituent_groups(self):
        """Returns a list of the constituents supported by the TPXO8 tidal database (2-D)."""
        return [self.TPXO8_CONS[0], self.TPXO8_CONS[1]]

    def constituent_resource(self, con):
        """Get the filename given a constituent.

        Args:
            con (str): Name of the constituent to get resource filename of. See TPXO8_CONS for list of available
                constituents

        Returns:
            str: The basename of the resource file if the specified constituent is supported by the TPXO8 tidal
                database, else None
        """
        con = con.upper()
        for group in self.TPXO8_CONS:
            if con in group:
                return group[con]
        return None


class Tpxo9Resources(Resources):
    """TPXO9 resources."""
    TPXO9_CONS = {'2N2', 'K1', 'K2', 'M2', 'M4', 'MF', 'MM', 'MN4', 'MS4', 'N2', 'O1', 'P1', 'Q1', 'S1', 'S2'}
    DEFAULT_RESOURCE_FILE = 'tpxo9_netcdf/h_tpxo9.v1.nc'
    is_consolidated_file = True

    def __init__(self):
        """Constructor."""
        super().__init__()

    def resource_attributes(self):
        """Returns a dict of the resource attributes that are disabled (TPXO9 is not freely available)."""
        return {
            'url': None,  # Resources must already exist. Licensing restrictions prevent hosting files.
            'archive': 'gz',
        }

    def dataset_attributes(self):
        """Returns a dict of the TPXO9 dataset attributes (currently just 'units_muliplier')."""
        return {
            'units_multiplier': 1.0,  # meter
        }

    def available_constituents(self):
        """Returns a list of the constituents supported by the TPXO9 tidal database."""
        return self.TPXO9_CONS

    def constituent_groups(self):
        """Returns a list of the constituents supported by the TPXO9 tidal database (2-D)."""
        return [self.available_constituents()]

    def constituent_resource(self, con):
        """Get the filename given a constituent.

        Args:
            con (str): Name of the constituent to get resource filename of. See TPXO9_CONS for list of available
                constituents

        Returns:
            str: The basename of the resource file if the specified constituent is supported by the TPXO9 tidal
                database, else None
        """
        if con.upper() in self.TPXO9_CONS:
            return self.DEFAULT_RESOURCE_FILE
        else:
            return None


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
        return list(self.TPXO9_ATLAS_CONS.keys())

    def constituent_groups(self):
        """Single uniform-resolution group."""
        return [self.available_constituents()]

    def constituent_resource(self, con):
        """Map constituent name to per-con filename, or None if unsupported."""
        return self.TPXO9_ATLAS_CONS.get(con.upper())


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


class LeProvostResources(Resources):
    """LeProvost resources."""
    LEPROVOST_CONS = {'K1', 'K2', 'M2', 'N2', 'O1', 'P1', 'Q1', 'S2', 'NU2', 'MU2', '2N2', 'T2', 'L2'}
    DEFAULT_RESOURCE_FILE = 'leprovost_tidal_db.nc'

    def __init__(self):
        """Constructor."""
        super().__init__()

    def resource_attributes(self):
        """Returns a dict of the resource attributes needed to fetch the freely available LeProvost tidal database."""
        return {
            'url': 'http://sms.aquaveo.com/leprovost_tidal_db.zip',
            'archive': 'zip',  # zip compression
        }

    def dataset_attributes(self):
        """Returns a dict of the LeProvost dataset attributes."""
        return {
            'units_multiplier': 1.0,  # meter
            'num_lats': 361,
            'num_lons': 720,
            'min_lon': -180.0,
        }

    def available_constituents(self):
        """Returns a list of the constituents supported by the LeProvost tidal database."""
        return self.LEPROVOST_CONS

    def constituent_groups(self):
        """Returns a list of the constituents supported by the LeProvost tidal database (2-D)."""
        return [self.available_constituents()]

    def constituent_resource(self, con):
        """Get the filename given a constituent.

        Args:
            con (str): Name of the constituent to get resource filename of. See LEPROVOST_CONS for list of available
                constituents

        Returns:
            str: The basename of the resource file if the specified constituent is supported by the LeProvost tidal
                database, else None
        """
        if con.upper() in self.LEPROVOST_CONS:
            return self.DEFAULT_RESOURCE_FILE
        else:
            return None


class FES2014Resources(Resources):
    """FES2014 resources."""
    FES2014_CONS = {
        '2N2': '2n2.nc',
        'EPS2': 'eps2.nc',
        'J1': 'j1.nc',
        'K1': 'k1.nc',
        'K2': 'k2.nc',
        'L2': 'l2.nc',
        'LA2': 'la2.nc',
        'M2': 'm2.nc',
        'M3': 'm3.nc',
        'M4': 'm4.nc',
        'M6': 'm6.nc',
        'M8': 'm8.nc',
        'MF': 'mf.nc',
        'MKS2': 'mks2.nc',
        'MM': 'mm.nc',
        'MN4': 'mn4.nc',
        'MS4': 'ms4.nc',
        'MSF': 'msf.nc',
        'MSQM': 'msqm.nc',
        'MTM': 'mtm.nc',
        'MU2': 'mu2.nc',
        'N2': 'n2.nc',
        'N4': 'n4.nc',
        'NU2': 'nu2.nc',
        'O1': 'o1.nc',
        'P1': 'p1.nc',
        'Q1': 'q1.nc',
        'R2': 'r2.nc',
        'S1': 's1.nc',
        'S2': 's2.nc',
        'S4': 's4.nc',
        'SA': 'sa.nc',
        'SSA': 'ssa.nc',
        'T2': 't2.nc',
    }

    def __init__(self):
        """Constructor."""
        super().__init__()

    def resource_attributes(self):
        """Returns a dict of the resource attributes that are disabled (FES2014 is not freely available)."""
        return {
            'url': None,  # Resources must already exist. Licensing restrictions prevent hosting files.
            'archive': None,
        }

    def dataset_attributes(self):
        """Returns a dict of the FES2014 dataset attributes."""
        return {
            'units_multiplier': 1.0,  # meter
            'num_lats': 2881,
            'num_lons': 5760,
            'min_lon': 0.0,
        }

    def available_constituents(self):
        """Returns a list of the constituents supported by the FES2014 tidal database."""
        return self.FES2014_CONS.keys()

    def constituent_groups(self):
        """Returns a list of the constituents supported by the FES2014 tidal database (2-D)."""
        return [self.available_constituents()]

    def constituent_resource(self, con):
        """Get the filename given a constituent.

        Args:
            con (str): Name of the constituent to get resource filename of. See FES2014_CONS for list of available
                constituents

        Returns:
            str: The basename of the resource file if the specified constituent is supported by the FES2014 tidal
                database, else None
        """
        con = con.upper()
        if con in self.FES2014_CONS:
            return self.FES2014_CONS[con]
        else:
            return None


class Adcirc2015Resources(Resources):
    """ADCIRC (v2015) resources."""
    ADCIRC_CONS = {
        'M2', 'S2', 'N2', 'K1', 'M4', 'O1', 'M6', 'Q1', 'K2', 'L2', '2N2', 'R2', 'T2', 'LAMBDA2', 'MU2',
        'NU2', 'J1', 'M1', 'OO1', 'P1', '2Q1', 'RHO1', 'M8', 'S4', 'S6', 'M3', 'S1', 'MK3', '2MK3', 'MN4',
        'MS4', '2SM2', 'MF', 'MSF', 'MM', 'SA', 'SSA'
    }
    DEFAULT_RESOURCE_FILE = 'all_adcirc.nc'

    def __init__(self):
        """Constructor."""
        super().__init__()

    def resource_attributes(self):
        """Returns a dict of the resource attributes needed to fetch the freely available ADCIRC tidal database."""
        return {
            'url': 'http://sms.aquaveo.com/',
            'archive': None,  # Uncompressed NetCDF file
        }

    def dataset_attributes(self):
        """Returns a dict of the dataset attributes (currently only 'units_multiplier')."""
        return {'units_multiplier': 1.0}  # meter

    def available_constituents(self):
        """Returns a list of the constituents supported by the ADCIRC tidal database."""
        return self.ADCIRC_CONS

    def constituent_groups(self):
        """Returns a list of the constituents supported by the ADCIRC tidal database (2-D)."""
        return [self.available_constituents()]

    def constituent_resource(self, con):
        """Get the filename given a constituent.

        Args:
            con (str): Name of the constituent to get resource filename of. See ADCIRC_CONS for list of available
                constituents

        Returns:
            str: The basename of the resource file if the specified constituent is supported by the ADCIRC tidal
                database, else None
        """
        if con.upper() in self.ADCIRC_CONS:
            return self.DEFAULT_RESOURCE_FILE
        else:
            return None


class ResourceManager(object):
    """Harmonica resource manager to retrieve and access tide models."""

    RESOURCES = {
        'tpxo8': Tpxo8Resources(),
        'tpxo9': Tpxo9Resources(),
        'tpxo9_atlas': Tpxo9AtlasResources(),
        'tpxo10': Tpxo10Resources(),
        'leprovost': LeProvostResources(),
        'fes2014': FES2014Resources(),
        'adcirc2015': Adcirc2015Resources(),
    }
    TPXO_MODELS = {'tpxo8', 'tpxo9', 'tpxo9_atlas', 'tpxo10'}
    LEPROVOST_MODELS = {'fes2014', 'leprovost'}
    ADCIRC_MODELS = {'adcirc2015'}
    DEFAULT_RESOURCE = 'tpxo9'

    def __init__(self, model=DEFAULT_RESOURCE):
        """Constructor.

        Args:
            model (str): Name of the model to use initially.  See the constants defined in ResourceManager for valid
                values.
        """
        if model not in self.RESOURCES:
            raise ValueError('Model not recognized.')
        self.model = model
        self.model_atts = self.RESOURCES[self.model]
        self.datasets = []

    def __del__(self):
        """Deleter - closes Dataset file handles."""
        for d in self.datasets:
            for dset in d:
                dset.close()

    @staticmethod
    def data_dir_exists(model):
        """Check if a model's data directory exists in either the default location or the configurable one.

        Args:
            model (str): Name of the model. See the constants defined in ResourceManager for valid values.

        Returns:
            bool: True if the model's data folder exists in either location.
        """
        resource = ResourceManager.RESOURCES.get(model)
        data_dir = (resource.data_dir_name if resource is not None else None) or model
        if os.path.isdir(os.path.join(config['data_dir'], data_dir)):
            return True  # Exists in the default %APPDATA% folder
        if os.path.isdir(os.path.join(config['pre_existing_data_dir'], data_dir)):
            return True  # Exists in the user configurable folder
        return False

    @staticmethod
    def available_models():
        """Get a dict of flags indicating whether a tidal model has been installed.

        This just performs a quick check for the existence of model data folders. If you need a more robust
        check, write something else. Needed something fast for dialogs.

        Returns:
            dict: {'model': True if available else False}
        """
        return {model: ResourceManager.data_dir_exists(model) for model in ResourceManager.RESOURCES}

    def available_constituents(self):
        """Returns a list of the available constituents for the current model."""
        return self.model_atts.available_constituents()

    def get_units_multiplier(self):
        """Returns the units multiplier for the current model."""
        return self.model_atts.dataset_attributes()['units_multiplier']

    def download(self, resource, destination_dir):
        """Download a specified model resource."""
        if not os.path.isdir(destination_dir):
            os.makedirs(destination_dir)

        rsrc_atts = self.model_atts.resource_attributes()
        url = rsrc_atts['url']
        # Check if we can download resources for this model.
        if url is None:
            raise ValueError("Automatic fetching of resources is not available for the {} model.".format(self.model))

        if rsrc_atts['archive'] is None:
            url = "".join((url, resource))

        print('Downloading resource: {}'.format(url))

        path = os.path.join(destination_dir, resource)
        with urllib.request.urlopen(url) as response:
            if rsrc_atts['archive'] is not None:
                if rsrc_atts['archive'] == 'gz':
                    import tarfile
                    try:
                        tar = tarfile.open(mode='r:{}'.format(rsrc_atts['archive']), fileobj=response)
                    except IOError as e:
                        print(str(e))
                    else:
                        rsrcs = set(
                            self.model_atts.constituent_resource(con) for con in
                            self.model_atts.available_constituents()
                        )
                        tar.extractall(path=destination_dir, members=[m for m in tar.getmembers() if m.name in rsrcs])
                        tar.close()
                elif rsrc_atts['archive'] == 'zip':  # Unzip .zip files
                    zip_file = os.path.join(destination_dir, os.path.basename(resource) + '.zip')
                    with open(zip_file, 'wb') as out_file:
                        shutil.copyfileobj(response, out_file)
                    # Unzip the files
                    print("Unzipping files to: {}".format(destination_dir))
                    with ZipFile(zip_file, 'r') as unzipper:
                        # Extract all the files in the archive
                        unzipper.extractall(path=destination_dir)
                    print("Deleting zip file: {}".format(zip_file))
                    os.remove(zip_file)  # delete the zip file
            else:
                with open(path, 'wb') as f:
                    f.write(response.read())

        return path

    def download_model(self, resource_dir=None):
        """Download all of the model's resources for later use."""
        resources = set(
            self.model_atts.constituent_resource(con) for con in
            self.model_atts.available_constituents()
        )
        if not resource_dir:
            data_dir = self.model_atts.data_dir_name or self.model
            resource_dir = os.path.join(config['data_dir'], data_dir)
        for r in resources:
            path = os.path.join(resource_dir, r)
            if not os.path.exists(path):
                self.download(r, resource_dir)
        return resource_dir

    def remove_model(self):
        """Remove all of the model's resources."""
        data_dir = self.model_atts.data_dir_name or self.model
        resource_dir = os.path.join(config['data_dir'], data_dir)
        if os.path.exists(resource_dir):
            import shutil

            shutil.rmtree(resource_dir, ignore_errors=True)

    def get_datasets(self, constituents, filenames=None):
        """Returns a list of xarray datasets.

        Args:
            constituents (list[str]): List of the constiuent names to retrieve datasets for
            filenames (Optional[list[list[str]]]): Paths to the NetCDF files, parallel with return value if provided.
                Only needed by the FES2014 model currently.

        Returns:
            list[list[Dataset]]: The xarray Datasets for the requested constituents
        """
        available = self.available_constituents()
        if any(const not in available for const in constituents):
            raise ValueError('Constituent not recognized.')
        # handle compatible files together
        self.datasets = []
        for const_group in self.model_atts.constituent_groups():
            rsrcs = set(self.model_atts.constituent_resource(const) for const in set(constituents) & set(const_group))

            paths = set()
            if config['pre_existing_data_dir']:
                missing = set()
                data_dir = self.model_atts.data_dir_name or self.model
                for r in rsrcs:
                    path = os.path.join(config['pre_existing_data_dir'], data_dir, r)
                    paths.add(path) if os.path.exists(path) else missing.add(r)
                rsrcs = missing
                if not rsrcs and paths:
                    paths_list = list(paths)  # If the caller wants filenames, give them as parallel list with return.
                    self.datasets.append([xr.open_dataset(path) for path in paths_list])
                    if filenames is not None:
                        filenames.append(paths_list)
                    continue

            data_dir = self.model_atts.data_dir_name or self.model
            resource_dir = os.path.join(config['data_dir'], data_dir)
            for r in rsrcs:
                path = os.path.join(resource_dir, r)
                if not os.path.exists(path):
                    self.download(r, resource_dir)
                paths.add(path)

            if paths:
                paths_list = list(paths)
                self.datasets.append([xr.open_dataset(path) for path in paths_list])
                if filenames is not None:  # If the caller wants the filenames, give them as parallel list with return.
                    filenames.append(paths_list)

        return self.datasets
