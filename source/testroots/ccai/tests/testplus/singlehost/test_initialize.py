"""
    .. module:: test_initialize
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the testplus runtime and results initialisation
               helpers.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import contextlib
import os

from typing import Optional
from unittest.mock import patch

from ccai.integrationruntime.initialize import IntegrationResultResources

from ccai.thisapp.contextpaths import ContextPaths
from ccai.thisapp.enumerations import JobType

from ccai.testplus import initialize
from ccai.testplus.initialize import (
    TestPlusVariables,
    initialize_testplus_results,
    initialize_testplus_runtime,
)

from ccai.tests.testplus.singlehost.fakes import CallRecorder, FakeThisApplication


class FakeRuntimeVariables:
    """
        Stands in for ``RuntimeVariables``: plain class attributes the product
        code reads and assigns.
    """

    AM_PRESENCE_DIR = os.path.join(os.sep, "presence")
    AM_RESULTS_STATIC_RESOURCE_SRC_DIR: Optional[str] = None
    AM_RESULTS_STATIC_RESOURCE_DEST_DIR: Optional[str] = None
    AM_RESULTS_STATIC_SUMMARY_TEMPLATE: Optional[str] = None


def _make_fake_runtime_variables(src_dir: Optional[str] = None, dest_dir: Optional[str] = None,
                                 template: Optional[str] = None) -> type:
    attributes = {
        "AM_PRESENCE_DIR": os.path.join(os.sep, "presence"),
        "AM_RESULTS_STATIC_RESOURCE_SRC_DIR": src_dir,
        "AM_RESULTS_STATIC_RESOURCE_DEST_DIR": dest_dir,
        "AM_RESULTS_STATIC_SUMMARY_TEMPLATE": template,
    }
    rtnval = type("FakeRuntimeVariablesForTest", (FakeRuntimeVariables,), attributes)
    return rtnval


@contextlib.contextmanager
def _patched_results_initialisation(runtime_variables: type, app: FakeThisApplication, activate: CallRecorder):
    with contextlib.ExitStack() as stack:
        stack.enter_context(patch.object(initialize, "RuntimeVariables", runtime_variables))
        stack.enter_context(patch.object(initialize, "ThisApplicationSingleton", lambda: app))
        stack.enter_context(patch.object(initialize, "activate_profile_job", activate))
        yield
    return


def test_testplus_variables_alias_the_integration_result_resources() -> None:
    """
        testplus renders results from the same templates and static resources as
        the integration runtime, so its constants must alias them exactly.
    """
    assert TestPlusVariables.TESTPLUS_TEMPLATES_DIR == IntegrationResultResources.TEMPLATES_DIR
    assert TestPlusVariables.TESTPLUS_RESOURCE_DEST_LEAF == IntegrationResultResources.RESOURCE_DEST_LEAF
    assert TestPlusVariables.TESTPLUS_RESOURCE_SRC_DIR == IntegrationResultResources.RESOURCE_SRC_DIR
    assert TestPlusVariables.TESTPLUS_SUMMARY_TEMPLATE == IntegrationResultResources.SUMMARY_TEMPLATE
    return


def test_initialize_runtime_establishes_the_ccai_persona_with_the_testplus_factory() -> None:
    """
        The runtime is initialised as the ``ccai`` application homed under
        ``~/ccai`` with the testplus default type factory registered as its
        extension, so distributed jobs become the default job type.
    """
    establish = CallRecorder()
    resolve_runtime = CallRecorder()
    resolve_configuration = CallRecorder()

    with contextlib.ExitStack() as stack:
        stack.enter_context(patch.object(initialize, "establish_app_persona", establish))
        stack.enter_context(patch.object(initialize, "resolve_runtime_variables", resolve_runtime))
        stack.enter_context(patch.object(initialize, "resolve_configuration_variables", resolve_configuration))
        initialize_testplus_runtime()

    assert establish.call_count == 1
    _args, kwargs = establish.calls[0]
    assert kwargs["name"] == "ccai"
    assert kwargs["presence_dir"] == os.path.join(os.path.expanduser("~"), "ccai")
    assert kwargs["logger_name"] == "TP"
    assert kwargs["log_basename"] == "testrun"
    assert kwargs["extensions"] == "ccai.testplus.testplusdefaulttypefactory"
    assert resolve_runtime.call_count == 1
    assert resolve_configuration.call_count == 1
    return


def test_initialize_results_fills_unset_static_resource_variables() -> None:
    """
        Static resource locations that were not configured default to the
        testplus resources, with the destination under the presence directory.
    """
    runtime_variables = _make_fake_runtime_variables()
    app = FakeThisApplication()
    activate = CallRecorder()

    with _patched_results_initialisation(runtime_variables, app, activate):
        initialize_testplus_results()

    expected_dest = os.path.join(runtime_variables.AM_PRESENCE_DIR, "results", TestPlusVariables.TESTPLUS_RESOURCE_DEST_LEAF)
    assert runtime_variables.AM_RESULTS_STATIC_RESOURCE_SRC_DIR == TestPlusVariables.TESTPLUS_RESOURCE_SRC_DIR
    assert runtime_variables.AM_RESULTS_STATIC_RESOURCE_DEST_DIR == expected_dest
    assert runtime_variables.AM_RESULTS_STATIC_SUMMARY_TEMPLATE == TestPlusVariables.TESTPLUS_SUMMARY_TEMPLATE
    return


def test_initialize_results_keeps_preconfigured_static_resource_variables() -> None:
    """
        Static resource locations that were already configured are left alone.
    """
    runtime_variables = _make_fake_runtime_variables(src_dir="/custom/src", dest_dir="/custom/dest", template="/custom/summary.html")
    app = FakeThisApplication()
    activate = CallRecorder()

    with _patched_results_initialisation(runtime_variables, app, activate):
        initialize_testplus_results()

    assert runtime_variables.AM_RESULTS_STATIC_RESOURCE_SRC_DIR == "/custom/src"
    assert runtime_variables.AM_RESULTS_STATIC_RESOURCE_DEST_DIR == "/custom/dest"
    assert runtime_variables.AM_RESULTS_STATIC_SUMMARY_TEMPLATE == "/custom/summary.html"
    return


def test_initialize_results_publishes_resource_paths_to_the_application_context() -> None:
    """
        The resolved resource locations are inserted into the application
        context at the well-known result paths.
    """
    runtime_variables = _make_fake_runtime_variables(src_dir="/custom/src", dest_dir="/custom/dest", template="/custom/summary.html")
    app = FakeThisApplication()
    activate = CallRecorder()

    with _patched_results_initialisation(runtime_variables, app, activate):
        initialize_testplus_results()

    expected = [
        (ContextPaths.DIR_RESULTS_RESOURCE_SRC, "/custom/src"),
        (ContextPaths.DIR_RESULTS_RESOURCE_DEST, "/custom/dest"),
        (ContextPaths.FILE_RESULTS_TEMPLATE, "/custom/summary.html"),
    ]
    assert app.context.inserted == expected
    return


def test_initialize_results_activates_a_test_run_job() -> None:
    """
        Results initialisation activates the process as a test-run job, which
        is what wires logging and the results directory.
    """
    runtime_variables = _make_fake_runtime_variables()
    app = FakeThisApplication()
    activate = CallRecorder()

    with _patched_results_initialisation(runtime_variables, app, activate):
        initialize_testplus_results()

    assert activate.calls == [((), {"job_type": JobType.TestRun})]
    return
