"""
    .. module:: initialize
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Helper routines used to initialize the TestPlus runtime and
    test result resources.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import os

from automojo.thisapp.persona import establish_app_persona
from automojo.thisapp.wellknown import ThisApplicationSingleton
from automojo.thisapp.contextpaths import ContextPaths

from automojo.runtime.enumerations import JobType
from automojo.runtime.activation import activate_profile_job


from automojo.runtime.runtimevariables import RuntimeVariables, resolve_runtime_variables

from automojo.configuration.configurationvariables import resolve_configuration_variables

from automojo import testbase

TESTBASE_DIR = os.path.dirname(testbase.__file__)

class TestPlusVariables:
    """
        Collection of constants used to configure results handling.

        The attributes provide locations for templates and static resources that
        are consumed by TestPlus.
    """
    TESTPLUS_TEMPLATES_DIR = os.path.join(TESTBASE_DIR, "templates")
    TESTPLUS_RESOURCE_DEST_LEAF = os.path.join("static", "v2")
    TESTPLUS_RESOURCE_SRC_DIR = os.path.join(TESTPLUS_TEMPLATES_DIR, "v2", "static")
    TESTPLUS_SUMMARY_TEMPLATE = os.path.join(TESTPLUS_TEMPLATES_DIR, "v2", "testsummary.html")


def initialize_testplus_runtime():
    """
        Initializes the TestPlus runtime and loads configuration.

        This sets up the default home directory and registers the TestPlus
        default type factory so jobs executed via the ``testplus`` command run
        correctly.

        :returns: ``None``
    """

    name="automojo"
    home_dir = os.path.join(os.path.expanduser("~"), name)

    # Register the testplus default type factory so the default job type will be a distributed test job for
    # any tests run with the 'testplus' command.
    extension_modules = "automojo.testplus.testplusdefaulttypefactory"
    
    establish_app_persona(name=name, home_dir=home_dir, logger_name="TP", extension_modules=extension_modules, log_basename="testrun")

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
