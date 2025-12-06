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

from automojo.thisapp.wellknown import ThisApplicationSingleton

from automojo.runtime.runtimevariables import RuntimeVariablesDesc

from automojo.testbase.cli.cmdtree.services import group_testbase_services
from automojo.testbase.cli.cmdtree.utilities import group_testbase_utilities

from automojo.testplus.cli.cmdtree.testing import group_testplus_testing

from automojo.testplus.initialize import initialize_testplus_runtime

@click.group("testplus")
@click.option('-v', '--verbose', count=True)
def testplus_root_command(verbose):
    """
        Entry point for the ``testplus`` command line interface.

        :param int verbose: Verbosity level specified by ``-v`` or ``--verbose``.

        :returns: ``None``
    """

    initialize_testplus_runtime()
    
    interactive_console = False
    log_level_console = "WARNING"

    if verbose == 0:
        interactive_console = True
    else:
        interactive_console = False

        if verbose == 1:
            log_level_console = "INFO"
        elif verbose == 2:
            log_level_console = "DEBUG"
        elif verbose > 2:
            log_level_console = "NOTSET"

    this_app = ThisApplicationSingleton()

    this_app.override_variable_value(RuntimeVariablesDesc.AM_INTERACTIVE_CONSOLE, interactive_console)
    this_app.override_variable_value(RuntimeVariablesDesc.AM_LOG_LEVEL_CONSOLE, log_level_console)

    return


testplus_root_command.add_command(group_testbase_services)
testplus_root_command.add_command(group_testbase_utilities)

testplus_root_command.add_command(group_testplus_testing)


if __name__ == '__main__':
    testplus_root_command()
