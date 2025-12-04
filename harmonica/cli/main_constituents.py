"""The constituents CLI command."""

# 1. Standard Python modules
import argparse
import sys

# 2. Third party modules

# 3. Aquaveo modules

# 4. Local modules
from .common import add_common_args, add_const_out_args, add_loc_model_args
from ..tidal_constituents import Constituents


DESCR = 'Get specified tidal constituents at specified locations.'
EXAMPLE = """
Example:

    harmonica constituents 38.375789 -74.943915 -C M2 K1 -M tpxo8
"""


def config_parser(p, sub=False):
    """Configure the command line arguments passed the constituents CLI command.

    Args:
        p (ArgumentParser): The argument parser
        sub (Optional[bool]): True if this is a resources subparser
    """
    # Subparser info
    if sub:
        p = p.add_parser(
            'constituents',
            description=DESCR,
            help=DESCR,
            epilog=EXAMPLE,
            add_help=False,
        )

    add_common_args(p)
    add_loc_model_args(p)
    add_const_out_args(p)


def parse_args(args):
    """Parse the command line arguments passed the constituents CLI command.

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
    """Execute the constituents CLI command.

    Args:
        args (...): Variable length positional arguments
    """
    cons = Constituents(model=args.model).get_components(
        [(args.lat, args.lon)], cons=args.cons, positive_ph=args.positive_phase
    )
    out = cons.data[0].to_csv(args.output, sep='\t', header=True, index=True, index_label='constituent')
    if args.output is None:
        print(out)
    print("\nComplete.\n")


def main(args=None):
    """Entry point for the constituents CLI command.

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
