"""
    .. module:: run
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: CLI command used to execute collections of tests via the
    TestPlus framework.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import List

import os
import sys

import click

from ccai.interfaces.itestjob import ITestJob
from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
from ccai.xmodules.xlogging.enhancedloggers import getEnhancedLogger

from ccai.testplus.cli.cmdtree.testing.constants import (
    HELP_ROOT,
    HELP_EXCLUDES,
    HELP_INCLUDES,
    HELP_OUTPUT,
    HELP_START,
    HELP_BRANCH,
    HELP_BUILD,
    HELP_FLAVOR,
    HELP_JOB_ID,
    HELP_JOB_INITIATOR,
    HELP_JOB_LABEL,
    HELP_JOB_NAME,
    HELP_JOB_OWNER,
    HELP_RUNID,
    HELP_CONSOLE_LOG_LEVEL,
    HELP_FILE_LOG_LEVEL,
    HELP_DEBUGGER,
    HELP_BREAKPOINT,
    HELP_PRERUN_DIAGNOSTIC,
    HELP_POSTRUN_DIAGNOSTIC,
    HELP_INCLUDE_MARKER_EXP,
    HELP_EXCLUDE_MARKER_EXP
)

from ccai.testplus.cli.cmdtree.testing.constants import (
    HELP_CONFIG_NAME,
    HELP_CREDENTIAL,
    HELP_CREDENTIAL_NAMES,
    HELP_CREDENTIAL_SOURCES,
    HELP_DEFAULT_CONFIGS,
    HELP_LANDSCAPE,
    HELP_LANDSCAPE_NAMES,
    HELP_LANDSCAPE_SOURCES,
    HELP_RUNTIME,
    HELP_RUNTIME_NAMES,
    HELP_RUNTIME_SOURCES,
    HELP_TOPOLOGY,
    HELP_TOPOLOGY_NAMES,
    HELP_TOPOLOGY_SOURCES,
    HELP_PRERUN_DIAGNOSTIC,
    HELP_POSTRUN_DIAGNOSTIC,
    CONFIGURATION_CHOICES
)

@click.command("run", help="Command used to run collections of tests.")
@click.option("--root", default=None,  type=str, required=False, help=HELP_ROOT)
@click.option("--excludes", "-x", multiple=True, required=False, help=HELP_EXCLUDES)
@click.option("--includes", "-i", multiple=True, help=HELP_INCLUDES)
@click.option("--output", "-o", default=None, required=False, help=HELP_OUTPUT)
@click.option("--start", default=None, required=False, help=HELP_START)
@click.option("--runid", default=None, required=False, help=HELP_RUNID)
@click.option("--branch", default=None, required=False, help=HELP_BRANCH)
@click.option("--build", default=None, required=False, help=HELP_BUILD)
@click.option("--flavor", default=None, required=False, help=HELP_FLAVOR)
@click.option("--job-id", default=None, required=False, help=HELP_JOB_ID)
@click.option("--job-initiator", default=None, required=False, help=HELP_JOB_INITIATOR)
@click.option("--job-label", default=None, required=False, help=HELP_JOB_LABEL)
@click.option("--job-name", default=None, required=False, help=HELP_JOB_NAME)
@click.option("--job-owner", default=None, required=False, help=HELP_JOB_OWNER)
@click.option("--default-configs", "default_configs", multiple=True, default=None, required=False, type=click.Choice(CONFIGURATION_CHOICES), help=HELP_DEFAULT_CONFIGS)
@click.option("--config-name", "config_name", multiple=False, default=None, required=False, help=HELP_CONFIG_NAME)
@click.option("--credential", "credential_files", multiple=True, default=None, required=False, help=HELP_CREDENTIAL)
@click.option("--credential-name", "credential_names", multiple=True, default=None, required=False, help=HELP_CREDENTIAL_NAMES)
@click.option("--credential-source", "credential_sources", multiple=True, default=None, required=False, help=HELP_CREDENTIAL_SOURCES)
@click.option("--landscape", "landscape_files", multiple=True, default=None, required=False, help=HELP_LANDSCAPE)
@click.option("--landscape-name", "landscape_names", multiple=True, default=None, required=False, help=HELP_LANDSCAPE_NAMES)
@click.option("--landscape-source", "landscape_sources", multiple=True, default=None, required=False, help=HELP_LANDSCAPE_SOURCES)
@click.option("--runtime", "runtime_files", multiple=True, default=None, required=False, help=HELP_RUNTIME)
@click.option("--runtime-name", "runtime_names", multiple=True, default=None, required=False, help=HELP_RUNTIME_NAMES)
@click.option("--runtime-source", "runtime_sources", multiple=True, default=None, required=False, help=HELP_RUNTIME_SOURCES)
@click.option("--topology", "topology_files", multiple=True, default=None, required=False, help=HELP_TOPOLOGY)
@click.option("--topology-name", "topology_names", multiple=True, default=None, required=False, help=HELP_TOPOLOGY_NAMES)
@click.option("--topology-source", "topology_sources", multiple=True, default=None, required=False, help=HELP_TOPOLOGY_SOURCES)
@click.option("--console-level", default=None, required=False, type=click.Choice(LOG_LEVEL_NAMES, case_sensitive=False), help=HELP_CONSOLE_LOG_LEVEL)
@click.option("--logfile-level", default=None, required=False, type=click.Choice(LOG_LEVEL_NAMES, case_sensitive=False), help=HELP_FILE_LOG_LEVEL)
@click.option("--debugger", default=None, required=False, type=click.Choice(['pdb', 'debugpy']), help=HELP_DEBUGGER)
@click.option("--breakpoint", "breakpoints", default=None, required=False, multiple=True, type=click.Choice(['test-discovery', 'testrun-start']), help=HELP_BREAKPOINT)
@click.option("--prerun-diagnostic", is_flag=True, default=False, required=False, help=HELP_PRERUN_DIAGNOSTIC)
@click.option("--postrun-diagnostic", is_flag=True, default=False, required=False, help=HELP_POSTRUN_DIAGNOSTIC)
@click.option("--include-marker-exp", required=False, multiple=True, help=HELP_INCLUDE_MARKER_EXP)
@click.option("--exclude-marker-exp", required=False, multiple=True, help=HELP_EXCLUDE_MARKER_EXP)
def command_testplus_testing_run(root, includes, excludes, output, start, runid, branch, build, flavor, job_id, job_initiator,
                        job_label, job_name, job_owner, default_configs, config_name, credential_files, credential_names, credential_sources,
                        landscape_files, landscape_names, landscape_sources, runtime_files, runtime_names, runtime_sources,
                        topology_files, topology_names, topology_sources, console_level, logfile_level,
                        debugger, breakpoints, prerun_diagnostic, postrun_diagnostic, include_marker_exp,
                        exclude_marker_exp):
    """
        Executes a collection of tests using the TestPlus framework.

        :param root: Root directory used when scanning for tests.
        :param includes: Test inclusion expressions.
        :param excludes: Test exclusion expressions.

        :returns: ``None``
    """

    # The click options below are declared multiple=True, so these arrive as
    # immutable tuples; copy them into lists before appending the config name.
    landscape_names = list(landscape_names)
    topology_names = list(topology_names)

    if config_name is not None:
        if config_name not in landscape_names:
            landscape_names.append(config_name)
        if config_name not in topology_names:
            topology_names.append(config_name)

    # pylint: disable=unused-import,import-outside-toplevel

    # We do the imports of the automation framework code inside the action functions because
    # we don't want to startup loggin and the processing of inputs and environment variables
    # until we have entered an action method.  Thats way we know how to setup the environment.

    # IMPORTANT: We need to load the context first because it will trigger the loading
    # of the default user configuration

    from ccai.thisapp.contextpaths import ContextPaths
    from ccai.thisapp.wellknown import ThisApplicationSingleton

    from ccai.xmodules.xpython import prepend_python_path

    from ccai.thisapp.runtimevariables import RuntimeVariables, RuntimeVariablesDesc

    from ccai.runtime.optionoverrides import AM_RUNTIME_OPTION_OVERRIDES
    from ccai.configuration.optionoverrides import ConfigOptionOverrides

    # STEP 1 - Initialize the Runtime (Performed by the root command)
    
    # STEP 2 - Resolve the configuration variables (Performed by the root command)

    # STEP 3 - Apply any 'Configuration' related option overrides

    this_app = ThisApplicationSingleton()

    # We need to default these to 'None' so they do not effect the runtime behavior unless
    # this command explicitly sets them later.
    use_credentials = None
    use_landscape = None
    use_runtime = None
    use_topology = None

    if "all" in default_configs:
        use_credentials = True
        use_landscape = True
        use_runtime = True
        use_topology = True
    else:
        if "credentials" in default_configs:
            use_credentials = True
        if "landscape" in default_configs:
            use_landscape = True
        if "runtime" in default_configs:
            use_runtime = True
        if "topology" in default_configs:
            use_topology = True

    from ccai.testbase.markers import MetaFilter, parse_marker_expression

    if len(credential_files) > 0:
        use_credentials = True
        ConfigOptionOverrides.override_config_credentials_files(credential_files)

    if len(credential_names) > 0:
        use_credentials = True
        ConfigOptionOverrides.override_config_credentials_names(credential_names)

    if len(credential_sources) > 0:
        use_credentials = True
        ConfigOptionOverrides.override_config_credentials_sources(credential_sources)


    if len(landscape_files) > 0:
        use_landscape = True
        ConfigOptionOverrides.override_config_landscape_files(landscape_files)

    if len(landscape_names) > 0:
        use_landscape = True
        ConfigOptionOverrides.override_config_landscape_names(landscape_names)

    if len(landscape_sources) > 0:
        use_landscape = True
        ConfigOptionOverrides.override_config_landscape_sources(landscape_sources)


    if len(runtime_files) > 0:
        use_runtime = True
        ConfigOptionOverrides.override_config_runtime_files(runtime_files)

    if len(runtime_names) > 0:
        use_runtime = True
        ConfigOptionOverrides.override_config_runtime_names(runtime_names)

    if len(runtime_sources) > 0:
        use_runtime = True
        ConfigOptionOverrides.override_config_runtime_sources(runtime_sources)


    if len(topology_files) > 0:
        use_topology = True
        ConfigOptionOverrides.override_config_topology_files(topology_files)

    if len(topology_names) > 0:
        use_topology = True
        ConfigOptionOverrides.override_config_topology_names(topology_names)

    if len(topology_sources) > 0:
        use_topology = True
        ConfigOptionOverrides.override_config_topology_sources(topology_sources)


    # STEP 4 - Resolve the Configuration Maps
    from ccai.configuration.configurationmaps import resolve_configuration_maps
    resolve_configuration_maps(use_credentials=use_credentials, use_landscape=use_landscape,
                               use_runtime=use_runtime, use_topology=use_topology)


    # STEP 5 - The application of the remaining options must happen after we have resolved configuration
    # maps because some of those settings will get overridden by the options.  So the runtime
    # needs to be loaded and set first before we apply runtime options 

    if prerun_diagnostic:
        this_app.override_variable_value(RuntimeVariablesDesc.AM_DIAGNOSTICS_PRERUN, {})

    if postrun_diagnostic:
        this_app.override_variable_value(RuntimeVariablesDesc.AM_DIAGNOSTICS_POSTRUN, {})

    if branch is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_build_branch(branch)

    if build is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_build_name(build)

    if flavor is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_build_flavor(flavor)


    if job_id is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_job_id(job_id)

    if job_initiator is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_job_initiator(job_initiator)

    if job_label is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_job_label(job_label)

    if job_name is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_job_name(job_name)

    if job_owner is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_job_owner(job_owner)

    if console_level is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_loglevel_console(console_level)

    if logfile_level is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_loglevel_file(logfile_level)

    if output is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_output_directory(output)

    if start is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_starttime(start)

    if runid is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_run_id(runid)

    # The '--breakpoint' option is declared multiple=True, so click delivers an
    # empty tuple rather than None when it is not given.  Only a non-empty
    # selection is a request to break, so only then override the breakpoints
    # and fall back to a default debugger.
    if breakpoints is not None and len(breakpoints) > 0:
        AM_RUNTIME_OPTION_OVERRIDES.override_debug_breakpoints(breakpoints)

        # If a breakpoint was passed but the debugger was not, fall back to
        # 'debugpy' as the default debugger.
        if debugger is None:
            AM_RUNTIME_OPTION_OVERRIDES.override_debug_debugger('debugpy')

    if debugger is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_debug_debugger(debugger)

    # TODO: Handle 'root' parameter better
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
    from ccai.testplus.initialize import initialize_testplus_results

    initialize_testplus_results()

    logger = getEnhancedLogger()


    # STEP 7 - Create and kick off the job

    from ccai.thisapp.wellknown import ConfiguredSuperFactorySingleton
    from ccai.testbase.factoryprotocols import TestBaseFactoryProtocol

    # At this point in the code, we either lookup an existing test job or we create a test job
    # from the includes, excludes or test_module
    sfactory = ConfiguredSuperFactorySingleton()
    TestJobType = sfactory.get_override_types_by_order(TestBaseFactoryProtocol.get_testbase_default_job_type)

    tjob: ITestJob

    result_code = 0
    with TestJobType(logger, test_root, includes=includes, excludes=excludes, metafilters=metafilters) as tjob:
        result_code = tjob.execute()

    sys.exit(result_code)

    return
