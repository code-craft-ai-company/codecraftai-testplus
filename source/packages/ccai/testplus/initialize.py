"""
    .. module:: initialize
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Helper routines used to initialize the TestPlus runtime and
    test result resources.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import os

from ccai.thisapp.persona import establish_app_persona
from ccai.thisapp.wellknown import ThisApplicationSingleton
from ccai.thisapp.contextpaths import ContextPaths

from ccai.thisapp.enumerations import JobType
from ccai.thisapp.activation import activate_profile_job


from ccai.thisapp.runtimevariables import RuntimeVariables, resolve_runtime_variables

from ccai.configuration.configurationvariables import resolve_configuration_variables

from ccai.integrationruntime.initialize import IntegrationResultResources


class TestPlusVariables:
    """
        Collection of constants used to configure results handling.

        The attributes provide locations for templates and static resources that
        are consumed by TestPlus. The HTML summary template and static render
        resources relocated from ``codecraftai-testbase`` to
        ``codecraftai-integration-runtime`` in the Phase 3 results split, so
        these now alias :class:`IntegrationResultResources` -- testplus and the
        integration runtime must always render from the same resources.
    """
    TESTPLUS_TEMPLATES_DIR = IntegrationResultResources.TEMPLATES_DIR
    TESTPLUS_RESOURCE_DEST_LEAF = IntegrationResultResources.RESOURCE_DEST_LEAF
    TESTPLUS_RESOURCE_SRC_DIR = IntegrationResultResources.RESOURCE_SRC_DIR
    TESTPLUS_SUMMARY_TEMPLATE = IntegrationResultResources.SUMMARY_TEMPLATE


def initialize_testplus_runtime():
    """
        Initializes the TestPlus runtime and loads configuration.

        This sets up the default home directory and registers the TestPlus
        default type factory so jobs executed via the ``testplus`` command run
        correctly.

        :returns: ``None``
    """

    name="ccai"
    home_dir = os.path.join(os.path.expanduser("~"), name)

    # Register the testplus default type factory so the default job type will be a distributed test job for
    # any tests run with the 'testplus' command.
    extension_modules = "ccai.testplus.testplusdefaulttypefactory"
    
    establish_app_persona(name=name, presence_dir=home_dir, logger_name="TP", extensions=extension_modules, log_basename="testrun")

    resolve_runtime_variables()

    resolve_configuration_variables()

    return


def initialize_testplus_results():
    """
        Initializes the TestPlus results locations and logging.

        This populates runtime variables describing where static resources and
        templates are located and ensures logging is configured.

        :returns: ``None``
    """

    dest_static_dir = os.path.join(RuntimeVariables.AM_PRESENCE_DIR, "results", TestPlusVariables.TESTPLUS_RESOURCE_DEST_LEAF)

    if RuntimeVariables.AM_RESULTS_STATIC_RESOURCE_SRC_DIR is None:
        RuntimeVariables.AM_RESULTS_STATIC_RESOURCE_SRC_DIR = TestPlusVariables.TESTPLUS_RESOURCE_SRC_DIR
    if RuntimeVariables.AM_RESULTS_STATIC_RESOURCE_DEST_DIR is None:
        RuntimeVariables.AM_RESULTS_STATIC_RESOURCE_DEST_DIR = dest_static_dir
    if RuntimeVariables.AM_RESULTS_STATIC_SUMMARY_TEMPLATE is None:
        RuntimeVariables.AM_RESULTS_STATIC_SUMMARY_TEMPLATE = TestPlusVariables.TESTPLUS_SUMMARY_TEMPLATE

    this_app = ThisApplicationSingleton()
    ctx = this_app.context
    ctx.insert(ContextPaths.DIR_RESULTS_RESOURCE_SRC, RuntimeVariables.AM_RESULTS_STATIC_RESOURCE_SRC_DIR)
    ctx.insert(ContextPaths.DIR_RESULTS_RESOURCE_DEST, RuntimeVariables.AM_RESULTS_STATIC_RESOURCE_DEST_DIR)
    ctx.insert(ContextPaths.FILE_RESULTS_TEMPLATE, RuntimeVariables.AM_RESULTS_STATIC_SUMMARY_TEMPLATE)

    activate_profile_job(job_type=JobType.TestRun)

    return
