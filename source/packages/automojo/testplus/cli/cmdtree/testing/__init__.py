"""
    .. module:: testing
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: CLI group providing commands for interacting with tests and test
    results.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []
__version__ = "1.0.0"

from automojo.arcli.decorators import group

from automojo.testplus.cli.cmdtree.testing.jobs import group_testplus_testing_jobs
from automojo.testplus.cli.cmdtree.testing.query import command_testplus_testing_query
from automojo.testplus.cli.cmdtree.testing.run import command_testplus_testing_run

@group("testing")
def group_testplus_testing():
    """
        Contains command for working with tests and test results.

        Root command group for TestPlus testing related operations.

        :returns: ``None``
    """

    return

group_testplus_testing.add_command(group_testplus_testing_jobs)
group_testplus_testing.add_command(command_testplus_testing_query)
group_testplus_testing.add_command(command_testplus_testing_run)
