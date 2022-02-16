"""The resources CLI command."""
# 1. Standard python modules
import argparse
import sys

# 2. Third party modules

# 3. Aquaveo modules

# 4. Local modules
from ..resource import ResourceManager


DESCR = 'Manage model resources for subsequent analysis calls.'
EXAMPLE = """
Example:

    harmonica resources download tpxo8
"""
actions = {
    'download': 'download_model',
    'remove': 'remove_model',
}


def config_parser(p, sub=False):
    """Configure the command line arguments passed the resources CLI command.

    Args:
        p (ArgumentParser): The argument parser
        sub (Optional[bool]): True if this is a resources subparser
    """
    # Subparser info
    if sub:
        p = p.add_parser(
            'resources',
            description=DESCR,
            help=DESCR,
            epilog=EXAMPLE,
            add_help=False,
        )

    p.add_argument(
        'action',
        choices=actions.keys(),
        help='Action to perform on model resources',
    )

    p.add_argument(
        'model',
        choices=ResourceManager.RESOURCES.keys(),
        help='Constituent model specification',
    )


def parse_args(args):
    """Parse the command line arguments passed the resources CLI command.

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
    """Execute the resources CLI command.

    Args:
        args (...): Variable length positional arguments
    """
    eval('ResourceManager(model=args.model).{}()'.format(actions[args.action]))
    print('\nComplete.\n')


def main(args=None):
    """Entry point for the resources CLI command.

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
