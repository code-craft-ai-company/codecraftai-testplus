"""
    .. module:: test_entrypoints
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for :func:`distributed_test_entrypoint`: option
               parsing, job-type selection and the re-homing of a ``__main__``
               test module, driven with a stubbed job type.

    The entry point reads ``sys.modules["__main__"]``, writes the re-homed
    module back into ``sys.modules`` and calls ``sys.exit``.  Rather than put
    stand-ins into the real ``sys.modules``, the tests patch the ``sys`` name
    bound in the entrypoints module with a small recording object, so every
    module registration the product code performs is observable without
    touching the interpreter's own module table.  ``argparse`` reads the real
    ``sys.argv``, which is patched with ``patch.object`` for the call.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import contextlib
import inspect
import io
import os
import shutil
import sys
import tempfile
import types

from typing import Any, Dict, List, Optional, Type
from unittest.mock import patch

import ccai.testbase

from ccai.configuration import configurationmaps
from ccai.thisapp import activation
from ccai.thisapp.enumerations import JobType

from ccai.testplus import entrypoints
from ccai.testplus import initialize
from ccai.testplus.distributedtestjob import DefaultDistributedTestJob
from ccai.testplus.entrypoints import distributed_test_entrypoint

from ccai.tests.testplus.singlehost.fakes import (
    CallRecorder,
    FakeThisApplication,
    StubTestJob,
    make_stub_job_type,
)


MAIN_MODULE_SOURCE = '''
class HelperType:
    pass


def test_from_main():
    return


def helper_function():
    return
'''


class RecordingSys:
    """
        The subset of ``sys`` the entry point uses: a private module table,
        and an ``exit`` that raises ``SystemExit`` like the real one.
    """

    def __init__(self, main_module: types.ModuleType):
        self.modules: Dict[str, Any] = {
            "__main__": main_module,
            "ccai.testbase": ccai.testbase,
        }
        self.exit_codes: List[int] = []
        return

    def exit(self, code: int) -> None:
        self.exit_codes.append(code)
        raise SystemExit(code)


class RecordingRegistry:
    """
        Stands in for the injection registry; records origin renames.
    """

    renamed: List[str] = []

    def rename_resource_origins_from_main(self, new_origin: str) -> None:
        type(self).renamed.append(new_origin)
        return


class EntrypointHarness:
    """
        Holds the module under test plus every recorder the patched
        collaborators write to.
    """

    def __init__(self, test_root: str, results_dir: str):
        self.test_root = test_root
        self.results_dir = results_dir
        self.module_fullname = "troot.pkg.test_entry"

        self.main_module = types.ModuleType("__main__")
        self.main_module.__file__ = os.path.join(test_root, "pkg", "test_entry.py")
        exec(MAIN_MODULE_SOURCE, self.main_module.__dict__)

        self.fake_sys = RecordingSys(self.main_module)
        self.app = FakeThisApplication()
        self.initialize_runtime = CallRecorder()
        self.initialize_results = CallRecorder()
        self.activate_profile_job = CallRecorder()
        self.resolve_configuration_maps = CallRecorder()
        self.import_by_name = CallRecorder()
        return

    @contextlib.contextmanager
    def patched(self, argv: List[str]):
        """
            Patches the entry point's collaborators for one call.

            :param argv: The command line the entry point should parse.
        """
        RecordingRegistry.renamed = []
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(initialize, "initialize_testplus_runtime", self.initialize_runtime))
            stack.enter_context(patch.object(initialize, "initialize_testplus_results", self.initialize_results))
            stack.enter_context(patch.object(activation, "activate_profile_job", self.activate_profile_job))
            stack.enter_context(patch.object(configurationmaps, "resolve_configuration_maps", self.resolve_configuration_maps))
            stack.enter_context(patch.object(entrypoints, "ThisApplicationSingleton", lambda: self.app))
            stack.enter_context(patch.object(entrypoints, "get_path_for_testresults", lambda: self.results_dir))
            stack.enter_context(patch.object(entrypoints, "find_testmodule_root", lambda module: self.test_root))
            stack.enter_context(patch.object(entrypoints, "find_testmodule_fullname",
                                             lambda module, testroot=None: self.module_fullname))
            stack.enter_context(patch.object(entrypoints, "import_by_name", self.import_by_name))
            stack.enter_context(patch.object(entrypoints, "InjectionRegistry", RecordingRegistry))
            stack.enter_context(patch.object(entrypoints, "sys", self.fake_sys))
            stack.enter_context(patch.object(sys, "argv", ["test_entry.py"] + list(argv)))
            yield self
        return


def _run_entrypoint(argv: List[str], job_type: Optional[Type[StubTestJob]] = None) -> Any:
    """
        Runs the entry point inside a temporary test root and returns a tuple
        of ``(harness, exit_code)``; ``exit_code`` is what ``sys.exit`` received.
    """
    if job_type is None:
        job_type = make_stub_job_type()

    base_dir = tempfile.mkdtemp(prefix="testplus-entry-")
    try:
        test_root = os.path.join(base_dir, "troot")
        os.makedirs(os.path.join(test_root, "pkg"))
        results_dir = os.path.join(base_dir, "results")

        harness = EntrypointHarness(test_root, results_dir)
        exit_code = None
        with harness.patched(argv):
            try:
                distributed_test_entrypoint(job_type=job_type)
            except SystemExit as sysexit:
                exit_code = sysexit.code
        results_dir_created = os.path.isdir(results_dir)
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

    harness.results_dir_created = results_dir_created
    rtnval = (harness, exit_code)
    return rtnval


def test_entrypoint_defaults_to_the_default_distributed_job() -> None:
    """
        When no job type is supplied the entry point uses
        :class:`DefaultDistributedTestJob`.
    """
    signature = inspect.signature(distributed_test_entrypoint)
    default = signature.parameters["job_type"].default

    assert default is DefaultDistributedTestJob
    return


def test_entrypoint_defaults_includes_to_everything() -> None:
    """
        With no ``--include`` the job is asked to run every test (``*``) and
        given no excludes.
    """
    job_type = make_stub_job_type()

    harness, exit_code = _run_entrypoint([], job_type=job_type)

    assert exit_code == 0
    assert len(job_type.instances) == 1
    job = job_type.instances[0]
    assert job.includes == ["*"]
    assert job.excludes == []
    return


def test_entrypoint_passes_parsed_includes_and_excludes_to_the_job() -> None:
    """
        Repeated ``-i`` / ``-x`` options are accumulated and handed to the job
        in the order given.
    """
    job_type = make_stub_job_type()

    harness, _exit_code = _run_entrypoint(["-i", "#test_a", "--include", "#test_b", "-x", "#test_c"], job_type=job_type)

    job = job_type.instances[0]
    assert job.includes == ["#test_a", "#test_b"]
    assert job.excludes == ["#test_c"]
    return


def test_entrypoint_constructs_the_job_with_root_and_main_module() -> None:
    """
        The job receives the discovered test root and the re-homed test module,
        and is executed inside its context.
    """
    job_type = make_stub_job_type()

    harness, _exit_code = _run_entrypoint([], job_type=job_type)

    job = job_type.instances[0]
    assert job.testroot == harness.test_root
    assert job.test_module is harness.main_module
    assert job.entered and job.executed and job.exited
    return


def test_entrypoint_exits_with_the_job_result_code() -> None:
    """
        The process exit code is whatever ``execute`` returned.
    """
    job_type = make_stub_job_type(exit_code=5)

    harness, exit_code = _run_entrypoint([], job_type=job_type)

    assert exit_code == 5
    assert harness.fake_sys.exit_codes == [5]
    return


def test_entrypoint_resolves_configuration_maps_from_the_job_type_flags() -> None:
    """
        The job type's ``requires_*`` flags select which configuration maps are
        resolved before the run.
    """
    job_type = make_stub_job_type(requires_landscape=True, requires_topology=True)

    harness, _exit_code = _run_entrypoint([], job_type=job_type)

    assert harness.resolve_configuration_maps.call_count == 1
    _args, kwargs = harness.resolve_configuration_maps.calls[0]
    assert kwargs == {"use_credentials": False, "use_landscape": True, "use_runtime": False, "use_topology": True}
    return


def test_entrypoint_initialises_runtime_then_activates_then_results() -> None:
    """
        Runtime initialisation, job activation as a test run and results
        initialisation all happen exactly once before the job runs.
    """
    harness, _exit_code = _run_entrypoint([])

    assert harness.initialize_runtime.call_count == 1
    assert harness.initialize_results.call_count == 1
    assert harness.activate_profile_job.calls == [((JobType.TestRun,), {})]
    return


def test_entrypoint_publishes_job_type_and_output_directory_to_the_environment() -> None:
    """
        The application environment is told the job is a test run and where its
        results go, and the results directory is created.
    """
    harness, _exit_code = _run_entrypoint([])

    environment = harness.app.context.lookup("/environment")
    assert environment["jobtype"] == "testrun"
    assert environment["output_directory"] == harness.results_dir
    assert harness.results_dir_created
    return


def test_entrypoint_rehomes_the_main_module_under_its_full_name() -> None:
    """
        A module run as ``__main__`` is registered under its dotted name, its
        classes and functions are re-labelled to that name, the parent package
        is imported first and resource origins are renamed.
    """
    harness, _exit_code = _run_entrypoint([])

    fullname = harness.module_fullname
    main_module = harness.main_module
    assert harness.fake_sys.modules[fullname] is main_module
    assert main_module.__name__ == fullname
    assert main_module.HelperType.__module__ == fullname
    assert main_module.test_from_main.__module__ == fullname
    assert main_module.helper_function.__module__ == fullname
    assert harness.import_by_name.calls == [(("troot.pkg",), {})]
    assert RecordingRegistry.renamed == [fullname]
    return


def test_entrypoint_rejects_an_unknown_console_level_before_running_the_job() -> None:
    """
        An invalid ``--console-level`` is an argument error (exit status 2) and
        no job is constructed.
    """
    job_type = make_stub_job_type()

    # argparse prints its usage message to stderr; keep it out of the gate log.
    with contextlib.redirect_stderr(io.StringIO()):
        harness, exit_code = _run_entrypoint(["--console-level", "LOUD"], job_type=job_type)

    assert exit_code == 2
    assert job_type.instances == []
    return
