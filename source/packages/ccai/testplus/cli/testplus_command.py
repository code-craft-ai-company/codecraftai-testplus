#!/usr/bin/env python3
"""
    .. module:: testplus_command
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The script entrypoint for the 'testplus' command.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import click

from ccai.thisapp.wellknown import ThisApplicationSingleton

from ccai.thisapp.runtimevariables import RuntimeVariablesDesc

from ccai.testplus.cli.cmdtree.testing import group_testplus_testing

from ccai.testplus.initialize import initialize_testplus_runtime

@click.group("testplus", help="Run and inspect distributed, multi-host tests.")
@click.option('-v', '--verbose', count=True, help="Set the verbosity level.")
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


# NOTE: testbase's 'services' and 'utilities' groups are deliberately NOT
# mounted here.  This root command is still a click group, while testbase's
# command tree has been migrated to arcli, and click cannot dispatch to an
# arcli command: click's Group.invoke calls cmd.make_context() and its help
# formatter reads cmd.hidden, neither of which an arcli GroupingCommand has.
#
# Mounting them raised AttributeError on EVERY use -- 'testplus services',
# 'testplus utilities', any subcommand of either, and 'testplus --help'
# itself, because formatting the root help walks every registered command.
# So they contributed no working functionality while breaking root help.
#
# Those commands remain available through the 'testbase' entry point, which
# is installed alongside this one (testplus depends on testbase).  Mount them
# here again only once this root command is itself migrated to arcli.
testplus_root_command.add_command(group_testplus_testing)


if __name__ == '__main__':
    testplus_root_command()
