"""The constituents CLI command."""

# 1. Standard Python modules
import argparse
import sys

# 2. Third party modules

# 3. Aquaveo modules

# 4. Local modules
from .common import add_common_args
from .main_constituents import config_parser as config_parser_constituents
from .main_deconstruct import config_parser as config_parser_deconstruct
from .main_reconstruct import config_parser as config_parser_reconstruct
from .main_resources import config_parser as config_parser_resources


def main():
    """Entry point for the top-level CLI command.

    Returns:
        int: 0 on success, 1 on error
    """
    p = argparse.ArgumentParser(
        description='harmonica is a tool for working with tidal harmonics.',
        add_help=False,
    )
    add_common_args(p)
    sps = p.add_subparsers(
        metavar='command',
        dest='cmd',
    )
    sps.required = True
    config_parser_constituents(sps, True)
    config_parser_deconstruct(sps, True)
    config_parser_reconstruct(sps, True)
    config_parser_resources(sps, True)

    args = p.parse_args(sys.argv[1:])
    try:
        sys.modules[f'harmonica.cli.main_{args.cmd}'].execute(args)
    except RuntimeError as e:
        print(str(e))
        sys.exit(1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
