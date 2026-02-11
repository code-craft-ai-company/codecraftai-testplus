"""
    .. module:: jobs
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: CLI commands for listing, showing and running TestPlus jobs.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import argparse
import logging
import os
import sys

from automojo.arcli.decorators import group, command, option
from automojo.arcli.model.parameters.booleanparameter import BooleanParameter

from automojo.xmodules.xlogging.levels import LOG_LEVEL_NAMES
from automojo.xmodules.xlogging.enhancedloggers import getEnhancedLogger

from automojo.testplus.cli.options import (
    with_logging_options,
    with_common_build_options,
    HELP_ROOT, HELP_JOB, HELP_FILTER, HELP_OUTPUT, HELP_START, HELP_DEBUG
)

@group("jobs")
def group_testplus_testing_jobs():
    """
        CLI command group for interacting with TestPlus jobs.

        :returns: ``None``
    """

    return

@option("--debug", default=False, ptype=BooleanParameter, help=HELP_DEBUG)
@option("--filter", "-f", required=False, help=HELP_FILTER)
@option("--root", default=".", help=HELP_ROOT)
@command("list")
def command_testing_jobs_list(root, filter, debug):
    """
        Lists available TestPlus jobs.

        :returns: ``None``
    """

    return

@option("--debug", default=False, ptype=BooleanParameter, help=HELP_DEBUG)
@option("--job", "-j", required=True, help=HELP_JOB)
@option("--root", default=".", help=HELP_ROOT)
@command("show")
def command_testplus_testing_jobs_show(root, job, debug):
    """
        Displays information about a specific TestPlus job.

        :returns: ``None``
    """

    return

@with_logging_options
@with_common_build_options
@option("--start", default=None, required=False, help=HELP_START)
@option("--output", "-o", required=False, help=HELP_OUTPUT)
@option("--job", "-j", required=True, help=HELP_JOB)
@option("--root", default=".", help=HELP_ROOT)
@command("run")
def command_testplus_testing_jobs_run(root, job, output, start, branch, build, flavor, console_level, logfile_level):
    """
        Executes a specified TestPlus job.

        :param root: Root directory used when scanning for tests.
        :param job: Fully qualified job identifier.
        :param output: Directory for test results.

        :returns: ``None``
    """

    # pylint: disable=unused-import,import-outside-toplevel

    # We do the imports of the automation framework code inside the action functions because
    # we don't want to startup loggin and the processing of inputs and environment variables
    # until we have entered an action method.  Thats way we know how to setup the environment.

    # IMPORTANT: We need to load the context first because it will trigger the loading
    # of the default user configuration

    from automojo.xmodules.ximport import import_by_name
    from automojo.xmodules.xpython import prepend_python_path

    # STEP 1 - Initialize the Runtime (Performed by the root command)

    # STEP 2 - Resolve the configuration variables (Performed by the root command)

    # STEP 3 - Apply any 'Configuration' related option overrides

    

    # STEP 4 - Resolve the Configuration Maps
    #from automojo.configuration.configurationmaps import resolve_configuration_maps
    #resolve_configuration_maps(use_credentials=use_credentials, use_landscape=use_landscape,
    #                           use_runtime=use_runtime, use_topology=use_topology)
    
    # STEP 5 - The application of the remaining options must happen after we have resolved configuration
    # maps because some of those settings will get overridden by the options.  So the runtime
    # needs to be loaded and set first before we apply runtime options    

    # STEP 6 - Initialize the Results Output

    # STEP 7 - Create and kick off the job
    from automojo.runtime.activation import activate_profile_job, JobType
    activate_profile_job(JobType.TestRun)


    test_root = os.path.abspath(os.path.expandvars(os.path.expanduser(root)))
    if not os.path.isdir(test_root):
        errmsg = "The specified root folder does not exist. root=%s" % root
        if test_root != root:
            errmsg += " expanded=%s" % test_root
        raise argparse.ArgumentError("--root", errmsg)

    # Make sure we extend PATH to include the test root
    prepend_python_path(test_root)

    # Activation of the runtime happens when we initialize test results
    from automojo.testplus.initialize import initialize_testplus_results
    initialize_testplus_results()

    logger = getEnhancedLogger()

    tpmod = sys.modules["mojo.testplus"]
    tpmod.logger = logger

    from automojo.thisapp.wellknown import ConfiguredSuperFactorySingleton
    from automojo.testbase.factoryprotocols import TestBaseFactoryProtocol

    # At this point in the code, we either lookup an existing test job or we create a test job
    # from the includes, excludes or test_module
    sfactory = ConfiguredSuperFactorySingleton()
    TestJobType = sfactory.get_override_types_by_order(TestBaseFactoryProtocol.get_testbase_default_job_type)

    if job is not None:
        job_parts = job.split("@")
        if len(job_parts) != 2:
            errmsg = "A --job parameter must be of the form 'package.module@JobClass'"
            raise ValueError(errmsg)

        job_package, job_class = job_parts

        try:
            job_mod = import_by_name(job_package)
        except ImportError as imperr:
            errmsg = "Failure while importing job package %r"  % job_package
            raise argparse.ArgumentError("--job", errmsg) from imperr

        if not hasattr(job_mod, job_class):
            errmsg = "The job package %r does not have a job type %r." % (job_package, job_class)
            raise argparse.ArgumentError("--job", errmsg)

        TestJobType = getattr(job_mod, job_class)

    result_code = 0
    with TestJobType(logger, test_root) as tjob:
        result_code = tjob.execute()

    sys.exit(result_code)

    return

group_testplus_testing_jobs.add_command(command_testplus_testing_jobs_show)
group_testplus_testing_jobs.add_command(command_testplus_testing_jobs_run)
