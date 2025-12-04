"""The reconstruct CLI command."""

# 1. Standard Python modules
import argparse
from datetime import date, datetime
import sys

# 2. Third party modules
import numpy as np
import pandas as pd
from pytides.tide import Tide as pyTide

# 3. Aquaveo modules

# 4. Local modules
from .common import add_common_args, add_const_out_args, add_loc_model_args
from ..harmonica import Tide


DESCR = 'Reconstruct the tides at specified location and times.'
EXAMPLE = """
Example:

    harmonica reconstruct 38.375789 -74.943915
"""


def validate_date(value):
    """Validate a date string.

    Args:
        value (str): The date string, should be in '%Y-%m-%d' format (e.g. '2022-02-20')

    Returns:
        bool: True if the value is positive, False if it is zero or negative
    """
    try:
        # return date.fromisoformat(value) # python 3.7
        return pd.datetime.strptime(value, '%Y-%m-%d')
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(value)
        raise argparse.ArgumentTypeError(msg)


def check_positive(value):
    """Check if a value is positive.

    Args:
        value (Union[int, float]): The value to check

    Returns:
        bool: True if the value is positive, False if it is zero or negative
    """
    flt = float(value)
    if flt <= 0:
        msg = "Not a valid time length: {0}".format(value)
        raise argparse.ArgumentTypeError(msg)
    return flt


def config_parser(p, sub=False):
    """Configure the command line arguments passed the reconstruct CLI command.

    Args:
        p (ArgumentParser): The argument parser
        sub (Optional[bool]): True if this is a resources subparser
    """
    # Subparser info
    if sub:
        p = p.add_parser(
            'reconstruct',
            description=DESCR,
            help=DESCR,
            epilog=EXAMPLE,
            add_help=False,
        )

    add_common_args(p)
    p.add_argument(
        '-S', '--start_date',
        type=validate_date,
        default=date.today(),
        help='Start Date [YYYY-MM-DD], default: today'
    )
    p.add_argument(
        '-L', '--length',
        type=check_positive,
        default=7.,
        help='Length of series in days [positive non-zero], default: 7'
    )
    add_loc_model_args(p)
    add_const_out_args(p)


def parse_args(args):
    """Parse the command line arguments passed the reconstruct CLI command.

    Args:
        args (...): Variable length positional arguments

    Returns:
        ArgumentParser: The command line argument parser
    """
    p = argparse.ArgumentParser(
        description=DESCR,
        epilog=EXAMPLE,
        add_help=False,
    )
    config_parser(p)
    return p.parse_args(args)


def execute(args):
    """Execute the reconstruct CLI command.

    Args:
        args (...): Variable length positional arguments
    """
    times = pyTide._times(datetime.fromordinal(args.start_date.toordinal()), np.arange(args.length * 24., dtype=float))
    tide = Tide(model=args.model).reconstruct_tide(loc=[args.lat, args.lon], times=times, cons=args.cons,
                                                   positive_ph=args.positive_phase)
    out = tide.data.to_csv(args.output, sep='\t', header=True, index=False)
    if args.output is None:
        print(out)
    print('\nComplete.\n')


def main(args=None):
    """Entry point for the reconstruct CLI command.

    Args:
        args (...): Variable length positional arguments
    """
    if not args:
        args = sys.argv[1:]
    try:
        execute(parse_args(args))
    except RuntimeError as e:
        print(str(e))
        sys.exit(1)
    return
