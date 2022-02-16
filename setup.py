"""Build or install the harmonica package."""
# 1. Standard python modules
import os

# 2. Third party modules
from setuptools import setup

# 3. Aquaveo modules

# 4. Local modules


# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


install_requires = [
    'dask',
    'netCDF4',
    'numpy',
    'pandas',
    'pytides>=1.0.0',  # ERDC fork packaged by Aquaveo
    'toolz',
    'xarray',
    'xmsgrid>=6.0.0',
]

extras_require = {
    'build': [
        'setuptools',
    ],
    'tests': [],
}

extras_require['all'] = sorted(set(sum(extras_require.values(), [])))

entry_points = [
    'harmonica = harmonica.cli.main:main',
    'harmonica-constituents = harmonica.cli.main_constituents:main',
    'harmonica-deconstruct = harmonica.cli.main_deconstruct:main',
    'harmonica-reconstruct = harmonica.cli.main_reconstruct:main',
    'harmonica-resources = harmonica.cli.main_resources:main',
]


try:  # Use version_generator if available, but don't require it.
    from version_generator import get_version_string
    version = get_version_string(strict=False)
except Exception:
    version = '99.99.99'


setup(
    name='harmonica',
    version=version,
    description='Worldwide amplitude, phase, and speed for standard tidal constituents and tidal time series '
                'reconstruction and deconstruction.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Kevin Winters',
    author_email='Kevin.D.Winters@erdc.dren.mil',
    maintainer='Aquaveo LLC',
    url='https://github.com/aquaveo/harmonica',
    packages=['harmonica', 'harmonica.cli'],
    dependency_links=[
        'https://public.aquapi.aquaveo.com/aquaveo/stable'
        'https://public.aquapi.aquaveo.com/aquaveo/stable/pytides',
        'https://public.aquapi.aquaveo.com/aquaveo/stable/xmsgrid',
    ],
    entry_points={
        'console_scripts': entry_points
    },
    install_requires=install_requires,
    extras_require=extras_require,
    tests_require=extras_require['tests'],
    test_suite='tests',
    keywords='harmonica',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Natural Language :: English',
        'Topic :: Scientific/Engineering'
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.10',
    ],
    python_requires='>=3.10'
)
