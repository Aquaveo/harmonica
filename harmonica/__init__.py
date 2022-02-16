"""Initialize the module."""
# 1. Standard python modules
import os

# 2. Third party modules

# 3. Aquaveo modules

# 4. Local modules


config = {
    'pre_existing_data_dir': '',  # ignored if empty string
    # 'data_dir': os.path.join(os.path.dirname(__file__), 'data'),
    # If on Windows, use the system APPDATA directory to download resources to. The Python installation may
    # be in a protected folder. Default to the package directory if no APPDATA environment variable.
    'data_dir': os.path.join(os.getenv('APPDATA', os.path.dirname(os.path.dirname(__file__))), 'harmonica', 'data')
}

__version__ = '2.0.0rc2'
