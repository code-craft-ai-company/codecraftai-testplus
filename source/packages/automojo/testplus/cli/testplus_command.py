#!/usr/bin/env python3
"""
.. module:: testplus_command
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The script entrypoint for the 'testplus' command.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import click

from automojo.testbase.cli.cmdtree.services import group_testbase_services
from automojo.testbase.cli.cmdtree.utilities import group_testbase_utilities

from automojo.testplus.cli.cmdtree.testing import group_testplus_testing


@click.group("testplus")
@click.option('-v', '--verbose', count=True)
def testplus_root_command(verbose):
    """
        Entry point for the ``testplus`` command line interface.

        :param int verbose: Verbosity level specified by ``-v`` or ``--verbose``.

        :returns: ``None``
    """

    from automojo.foundation.runtime.runtimevariables import AM_RUNTIME_VARIABLES

    if verbose == 0:
        AM_RUNTIME_VARIABLES.AM_INTERACTIVE_CONSOLE = True
    else:
        AM_RUNTIME_VARIABLES.AM_INTERACTIVE_CONSOLE = False

        if verbose == 1:
            AM_RUNTIME_VARIABLES.AM_LOG_LEVEL_CONSOLE = "INFO"
        elif verbose == 2:
            AM_RUNTIME_VARIABLES.AM_LOG_LEVEL_CONSOLE = "DEBUG"
        elif verbose > 2:
            AM_RUNTIME_VARIABLES.AM_LOG_LEVEL_CONSOLE = "NOTSET"

    from automojo.testplus.initialize import initialize_testplus_runtime
    initialize_testplus_runtime()

    return


testplus_root_command.add_command(group_testbase_services)
testplus_root_command.add_command(group_testbase_utilities)

testplus_root_command.add_command(group_testplus_testing)


if __name__ == '__main__':
    testplus_root_command()
