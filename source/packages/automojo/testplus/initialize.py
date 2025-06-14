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

from automojo.foundation.collections.contextpaths import ContextPaths
from automojo.foundation.collections.wellknown import ContextSingleton

from automojo.foundation.xlogging.foundations import logging_initialize
    
from automojo.foundation.configuration.initialize import initialize_configuration, AM_CONFIGURATION_STATE

from automojo.foundation.runtime.runtimevariables import AM_RUNTIME_VARIABLES

from automojo import testbase

TESTBASE_DIR = os.path.dirname(testbase.__file__)

class TestPlusVariables:
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

    if not AM_CONFIGURATION_STATE.INITIALIZED:
        name="automojo"
        home_dir = os.path.join(os.path.expanduser("~"), name)

        # Register the testplus default type factory so the default job type will be a distributed test job for
        # any tests run with the 'testplus' command.
        extension_modules = "automojo.testplus.testplusdefaulttypefactory"
        initialize_configuration(name=name, home_dir=home_dir, logger_name="TP", extension_modules=extension_modules)

    return


def initialize_testplus_results():
    """
        Initializes the TestPlus results locations and logging.

        This populates runtime variables describing where static resources and
        templates are located and ensures logging is configured.

        :returns: ``None``
    """

    dest_static_dir = os.path.join(AM_RUNTIME_VARIABLES.AM_PRESENCE_DIRECTORY, "results", TestPlusVariables.TESTPLUS_RESOURCE_DEST_LEAF)

    if AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_RESOURCE_SRC_DIR is None:
        AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_RESOURCE_SRC_DIR = TestPlusVariables.TESTPLUS_RESOURCE_SRC_DIR
    if AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_RESOURCE_DEST_DIR is None:
        AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_RESOURCE_DEST_DIR = dest_static_dir
    if AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_SUMMARY_TEMPLATE is None:
        AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_SUMMARY_TEMPLATE = TestPlusVariables.TESTPLUS_SUMMARY_TEMPLATE

    ctx = ContextSingleton()
    ctx.insert(ContextPaths.DIR_RESULTS_RESOURCE_SRC, AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_RESOURCE_SRC_DIR)
    ctx.insert(ContextPaths.DIR_RESULTS_RESOURCE_DEST, AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_RESOURCE_DEST_DIR)
    ctx.insert(ContextPaths.FILE_RESULTS_TEMPLATE, AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_SUMMARY_TEMPLATE)

    logging_initialize()

    return
