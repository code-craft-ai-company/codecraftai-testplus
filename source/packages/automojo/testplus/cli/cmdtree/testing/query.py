"""
    .. module:: query
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: CLI command used to query tests available in a TestPlus
    environment.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import List

import logging
from automojo.xmodules.xlogging.enhancedloggers import getEnhancedLogger
import os
import sys

import click

from automojo.testplus.cli.cmdtree.testing.constants import (
    HELP_ROOT,
    HELP_EXCLUDES,
    HELP_INCLUDES,
    HELP_EXCLUDE_MARKER_EXP,
    HELP_INCLUDE_MARKER_EXP
)

@click.command("query", help="Command used to query information about tests.")
@click.option("--root", default=None, type=str, help=HELP_ROOT)
@click.option("--excludes", "-x", multiple=True, help=HELP_EXCLUDES)
@click.option("--includes", "-i", multiple=True, help=HELP_INCLUDES)
@click.option("--include-marker-exp", required=False, multiple=True, help=HELP_INCLUDE_MARKER_EXP)
@click.option("--exclude-marker-exp", required=False, multiple=True, help=HELP_EXCLUDE_MARKER_EXP)
def command_testplus_testing_query(root, includes, excludes,
    include_marker_exp, exclude_marker_exp):
    """
        Queries tests available within a TestPlus environment.

        :param root: Root directory used when scanning for tests.
        :param includes: Inclusion expressions for tests.
        :param excludes: Exclusion expressions for tests.

        :returns: ``None``
    """

    # pylint: disable=unused-import,import-outside-toplevel

    # We do the imports of the automation framework code inside the action functions because
    # we don't want to startup loggin and the processing of inputs and environment variables
    # until we have entered an action method.  Thats way we know how to setup the environment.

    # IMPORTANT: We need to load the context first because it will trigger the loading
    # of the default user configuration

    from automojo.thisapp.contextpaths import ContextPaths
    from automojo.thisapp.wellknown import ThisApplicationSingleton

    from automojo.xmodules.xpython import prepend_python_path

    from automojo.runtime.activation import activate_runtime, ActivationProfile
    from automojo.runtime.runtimevariables import RuntimeVariables

    # STEP 2 - Resolve the configuration variables (performed by the root command)

    # STEP 3 - Apply the configuration related options

    this_app = ThisApplicationSingleton()

    # STEP 4 - Resolve the Configuration Maps
    from automojo.configuration.configurationmaps import resolve_configuration_maps
    resolve_configuration_maps(use_credentials=False, use_landscape=False,
                               use_runtime=False, use_topology=False)

    # STEP 5 - Apply any Option Overrides

    from automojo.runtime.optionoverrides import AM_RUNTIME_OPTION_OVERRIDES

    from automojo.testbase.markers import MetaFilter, parse_marker_expression

    # Setup the Test Root
    if root is None:
        if RuntimeVariables.AM_TESTROOT is not None:
            root = RuntimeVariables.AM_TESTROOT
        else:
            root = "."

    test_root = os.path.abspath(os.path.expandvars(os.path.expanduser(root)))
    if not os.path.isdir(test_root):
        errmsg = "The specified root folder does not exist. root=%s" % root
        if test_root != root:
            errmsg += " expanded=%s" % test_root
        raise click.BadParameter(errmsg)

    AM_RUNTIME_OPTION_OVERRIDES.override_testroot(root)

    # Make sure we extend PATH to include the test roots parent folder so imports will
    # work properly.
    test_root_parent = os.path.dirname(test_root)
    prepend_python_path(test_root_parent)

    metafilters: List[MetaFilter] = []
    for imexp in include_marker_exp:
        imexp = imexp.strip("\"")
        imexp = imexp.strip("'")
        mfilter = parse_marker_expression("+" + imexp)
        metafilters.append(mfilter)

    for exmexp in exclude_marker_exp:
        exmexp = exmexp.strip("\"")
        exmexp = exmexp.strip("'")
        mfilter = parse_marker_expression("-" + exmexp)
        metafilters.append(mfilter)

    
    # STEP 6 - Initialize the Results Output

    # Initialize testplus results and logging
    from automojo.testplus.initialize import initialize_testplus_results

    initialize_testplus_results()


    # STEP 7 - Kick off the query

    logger = getEnhancedLogger()

    from automojo.thisapp.wellknown import ConfiguredSuperFactorySingleton
    from automojo.testbase.factoryprotocols import TestBaseFactoryProtocol

    sfactory = ConfiguredSuperFactorySingleton()
    TestJobType = sfactory.get_override_types_by_order(TestBaseFactoryProtocol.get_testbase_default_job_type)

    # At this point in the code, we either lookup an existing test job or we create a test job
    # from the includes, excludes or test_module
    result_code = 0
    with TestJobType(logger, test_root, includes=includes, excludes=excludes, metafilters=metafilters) as tjob:
        query_results = tjob.query()

        test_names = [tn for tn in query_results.keys()]
        test_names.sort()
        print()
        print("Tests:")
        for tname in test_names:
            tref = query_results[tname]
            print("    " + tname)

            param_names = [pn for pn in tref.subscriptions.keys()]
            param_names.sort()
            for pname in param_names:
                pinfo = tref.subscriptions[pname]
                print ("        {}: {}".format(pname, pinfo.describe_source()))

        print()

        if len(tjob.import_errors) > 0:
            print("IMPORT ERRORS:", file=sys.stderr)
            for ifilename in tjob.import_errors:
                imperr_msg = ifilename
                print("    " + imperr_msg, file=sys.stderr)
            print("", file=sys.stderr)

    return
