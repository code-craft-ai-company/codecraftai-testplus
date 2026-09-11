"""
    .. module:: test_cli_run
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for ``testplus testing run``: argument validation,
               option-to-override plumbing and job construction, driven with
               ``click.testing.CliRunner`` and a stubbed job type.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import contextlib
import os
import sys
import tempfile

from typing import List, Optional, Type
from unittest.mock import create_autospec, patch

from click.testing import CliRunner

from ccai.configuration import configurationmaps
from ccai.configuration import optionoverrides as configuration_optionoverrides
from ccai.runtime import optionoverrides as runtime_optionoverrides

from ccai.testbase.factoryprotocols import TestBaseFactoryProtocol
from ccai.testbase.properties import run_property
from ccai.testbase.properties import strategies as st

from ccai.thisapp import wellknown
from ccai.thisapp.runtimevariables import RuntimeVariablesDesc

from ccai.testplus import initialize
from ccai.testplus.cli.cmdtree.testing.run import command_testplus_testing_run

from ccai.tests.testplus.singlehost.fakes import (
    CallRecorder,
    FakeSuperFactory,
    FakeThisApplication,
    StubTestJob,
    make_stub_job_type,
)


class RunInvocation:
    """
        Everything one invocation of the ``run`` command touched.
    """

    def __init__(self, job_type: Type[StubTestJob]):
        self.job_type = job_type
        self.app = FakeThisApplication()
        self.super_factory = FakeSuperFactory(job_type)
        self.resolve_configuration_maps = CallRecorder()
        self.initialize_results = CallRecorder()
        self.runtime_overrides = create_autospec(runtime_optionoverrides.AM_RUNTIME_OPTION_OVERRIDES)
        self.config_overrides = create_autospec(configuration_optionoverrides.ConfigOptionOverrides)
        self.result = None
        self.python_path_after: List[str] = []
        return

    @property
    def job(self) -> StubTestJob:
        assert len(self.job_type.instances) == 1, "expected exactly one job to be constructed"
        rtnval = self.job_type.instances[0]
        return rtnval


def _invoke_run(args: List[str], job_type: Optional[Type[StubTestJob]] = None) -> RunInvocation:
    """
        Invokes ``run`` with every process-level collaborator patched so the
        command's own logic runs but nothing touches the live runtime.
    """
    if job_type is None:
        job_type = make_stub_job_type()
    invocation = RunInvocation(job_type)
    runner = CliRunner()
    saved_path = list(sys.path)

    try:
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(configurationmaps, "resolve_configuration_maps", invocation.resolve_configuration_maps))
            stack.enter_context(patch.object(initialize, "initialize_testplus_results", invocation.initialize_results))
            stack.enter_context(patch.object(wellknown, "ThisApplicationSingleton", lambda: invocation.app))
            stack.enter_context(patch.object(wellknown, "ConfiguredSuperFactorySingleton", lambda: invocation.super_factory))
            stack.enter_context(patch.object(runtime_optionoverrides, "AM_RUNTIME_OPTION_OVERRIDES", invocation.runtime_overrides))
            stack.enter_context(patch.object(configuration_optionoverrides, "ConfigOptionOverrides", invocation.config_overrides))
            invocation.result = runner.invoke(command_testplus_testing_run, args)
        invocation.python_path_after = list(sys.path)
    finally:
        sys.path[:] = saved_path

    return invocation


@contextlib.contextmanager
def _temporary_root():
    root = tempfile.mkdtemp(prefix="testplus-run-")
    try:
        yield root
    finally:
        os.rmdir(root)
    return


def test_run_rejects_a_root_that_does_not_exist() -> None:
    """
        A missing root directory is a parameter error and no job is built.
    """
    job_type = make_stub_job_type()
    missing_root = os.path.join(tempfile.gettempdir(), "testplus-no-such-root")

    invocation = _invoke_run(["--root", missing_root], job_type=job_type)

    assert invocation.result.exit_code == 2
    assert "does not exist" in invocation.result.output
    assert job_type.instances == []
    return


def test_run_builds_the_default_job_with_the_parsed_selection() -> None:
    """
        The job type resolved from the super factory is built with the
        absolute test root and the include and exclude expressions as given.
    """
    job_type = make_stub_job_type()

    with _temporary_root() as root:
        invocation = _invoke_run(["--root", root, "-i", "pkg.a", "--includes", "pkg.b", "-x", "pkg.c"], job_type=job_type)
        expected_root = os.path.abspath(root)

    assert invocation.result.exit_code == 0, invocation.result.output
    assert invocation.super_factory.requests == [TestBaseFactoryProtocol.get_testbase_default_job_type]
    job = invocation.job
    assert job.testroot == expected_root
    assert tuple(job.includes) == ("pkg.a", "pkg.b")
    assert tuple(job.excludes) == ("pkg.c",)
    assert job.entered and job.executed and job.exited
    return


def test_run_exit_status_is_the_job_result_code() -> None:
    """
        The command exits with whatever the job's ``execute`` returned.
    """
    job_type = make_stub_job_type(exit_code=7)

    with _temporary_root() as root:
        invocation = _invoke_run(["--root", root], job_type=job_type)

    assert invocation.result.exit_code == 7
    return


def test_run_initialises_results_and_records_the_test_root() -> None:
    """
        Results are initialised before the job runs and the test root is
        published as a runtime override.
    """
    with _temporary_root() as root:
        invocation = _invoke_run(["--root", root])

    assert invocation.initialize_results.call_count == 1
    invocation.runtime_overrides.override_testroot.assert_called_once_with(root)
    return


def test_run_prepends_the_test_root_parent_to_the_python_path() -> None:
    """
        The parent of the test root goes to the front of ``sys.path`` so the
        root package imports by name.
    """
    with _temporary_root() as root:
        invocation = _invoke_run(["--root", root])
        expected_parent = os.path.dirname(os.path.abspath(root))

    assert invocation.python_path_after[0] == expected_parent
    return


def test_run_without_configuration_options_leaves_every_map_unspecified() -> None:
    """
        With no configuration options every ``use_*`` argument is ``None`` so
        the runtime defaults decide.
    """
    with _temporary_root() as root:
        invocation = _invoke_run(["--root", root])

    assert invocation.resolve_configuration_maps.calls == [
        ((), {"use_credentials": None, "use_landscape": None, "use_runtime": None, "use_topology": None})
    ]
    return


def test_run_default_configs_all_enables_every_map() -> None:
    """
        ``--default-configs all`` turns on every configuration map.
    """
    with _temporary_root() as root:
        invocation = _invoke_run(["--root", root, "--default-configs", "all"])

    _args, kwargs = invocation.resolve_configuration_maps.calls[0]
    assert kwargs == {"use_credentials": True, "use_landscape": True, "use_runtime": True, "use_topology": True}
    return


def test_run_default_configs_enable_only_the_named_maps() -> None:
    """
        Naming individual configurations enables only those maps.
    """
    with _temporary_root() as root:
        invocation = _invoke_run(["--root", root, "--default-configs", "landscape", "--default-configs", "runtime"])

    _args, kwargs = invocation.resolve_configuration_maps.calls[0]
    assert kwargs == {"use_credentials": None, "use_landscape": True, "use_runtime": True, "use_topology": None}
    return


def test_run_config_name_extends_landscape_and_topology_names() -> None:
    """
        ``--config-name`` is appended to both the landscape and topology name
        lists, after any names given explicitly, and enables both maps.
    """
    with _temporary_root() as root:
        invocation = _invoke_run(["--root", root, "--config-name", "lab", "--landscape-name", "explicit"])

    invocation.config_overrides.override_config_landscape_names.assert_called_once_with(["explicit", "lab"])
    invocation.config_overrides.override_config_topology_names.assert_called_once_with(["lab"])
    _args, kwargs = invocation.resolve_configuration_maps.calls[0]
    assert kwargs["use_landscape"] is True
    assert kwargs["use_topology"] is True
    return


def test_run_config_name_appears_exactly_once_in_each_name_list() -> None:
    """
        For any explicit landscape and topology names, the configuration name
        ends up in each list exactly once and the explicit names keep their
        order.
    """
    name_strategy = st.text(alphabet="abcxyz", min_size=1, max_size=4)
    names_strategy = st.lists(name_strategy, min_size=0, max_size=3)

    def check(config_name: str, landscape_names: List[str], topology_names: List[str]) -> None:
        args = ["--config-name", config_name]
        for landscape_name in landscape_names:
            args.extend(["--landscape-name", landscape_name])
        for topology_name in topology_names:
            args.extend(["--topology-name", topology_name])

        with _temporary_root() as root:
            invocation = _invoke_run(["--root", root] + args)

        assert invocation.result.exit_code == 0, invocation.result.output

        landscape_call = invocation.config_overrides.override_config_landscape_names.call_args
        topology_call = invocation.config_overrides.override_config_topology_names.call_args
        applied_landscape = landscape_call.args[0]
        applied_topology = topology_call.args[0]

        assert applied_landscape.count(config_name) == 1
        assert applied_topology.count(config_name) == 1
        assert [name for name in applied_landscape if name != config_name] == [name for name in landscape_names if name != config_name]
        assert [name for name in applied_topology if name != config_name] == [name for name in topology_names if name != config_name]
        return

    run_property(check, max_examples=20, config_name=name_strategy, landscape_names=names_strategy,
                 topology_names=names_strategy)
    return


def test_run_credential_files_enable_the_credentials_map() -> None:
    """
        Supplying credential files enables the credentials map and forwards
        the files to the configuration overrides.
    """
    with _temporary_root() as root:
        invocation = _invoke_run(["--root", root, "--credential", "/creds/a.yaml", "--credential", "/creds/b.yaml"])

    invocation.config_overrides.override_config_credentials_files.assert_called_once_with(("/creds/a.yaml", "/creds/b.yaml"))
    _args, kwargs = invocation.resolve_configuration_maps.calls[0]
    assert kwargs["use_credentials"] is True
    return


def test_run_applies_build_and_job_metadata_overrides() -> None:
    """
        Build, job, log-level, output, start and run-id options each reach
        their runtime override.
    """
    with _temporary_root() as root:
        invocation = _invoke_run([
            "--root", root,
            "--branch", "main", "--build", "42", "--flavor", "debug",
            "--job-id", "job-1", "--job-initiator", "ci", "--job-label", "nightly",
            "--job-name", "smoke", "--job-owner", "owner",
            "--console-level", "INFO", "--logfile-level", "DEBUG",
            "--output", "/tmp/out", "--start", "2026-01-01T00:00:00.000000", "--runid", "run-1",
        ])

    overrides = invocation.runtime_overrides
    overrides.override_build_branch.assert_called_once_with("main")
    overrides.override_build_name.assert_called_once_with("42")
    overrides.override_build_flavor.assert_called_once_with("debug")
    overrides.override_job_id.assert_called_once_with("job-1")
    overrides.override_job_initiator.assert_called_once_with("ci")
    overrides.override_job_label.assert_called_once_with("nightly")
    overrides.override_job_name.assert_called_once_with("smoke")
    overrides.override_job_owner.assert_called_once_with("owner")
    overrides.override_loglevel_console.assert_called_once_with("INFO")
    overrides.override_loglevel_file.assert_called_once_with("DEBUG")
    overrides.override_output_directory.assert_called_once_with("/tmp/out")
    overrides.override_starttime.assert_called_once_with("2026-01-01T00:00:00.000000")
    overrides.override_run_id.assert_called_once_with("run-1")
    return


def test_run_without_options_applies_no_metadata_overrides() -> None:
    """
        Options that were not given must not override anything, so the values
        resolved from configuration survive.
    """
    with _temporary_root() as root:
        invocation = _invoke_run(["--root", root])

    overrides = invocation.runtime_overrides
    overrides.override_build_branch.assert_not_called()
    overrides.override_job_name.assert_not_called()
    overrides.override_output_directory.assert_not_called()
    overrides.override_run_id.assert_not_called()
    return


def test_run_without_a_breakpoint_leaves_the_debugger_alone() -> None:
    """
        No ``--breakpoint`` means no breakpoint override and no debugger
        override; a plain run must not turn on debugpy.
    """
    with _temporary_root() as root:
        invocation = _invoke_run(["--root", root])

    invocation.runtime_overrides.override_debug_breakpoints.assert_not_called()
    invocation.runtime_overrides.override_debug_debugger.assert_not_called()
    return


def test_run_breakpoint_without_a_debugger_defaults_to_debugpy() -> None:
    """
        Asking for a breakpoint without naming a debugger selects debugpy.
    """
    with _temporary_root() as root:
        invocation = _invoke_run(["--root", root, "--breakpoint", "test-discovery"])

    invocation.runtime_overrides.override_debug_breakpoints.assert_called_once_with(("test-discovery",))
    invocation.runtime_overrides.override_debug_debugger.assert_called_once_with("debugpy")
    return


def test_run_breakpoint_with_a_named_debugger_uses_that_debugger() -> None:
    """
        A named debugger wins over the debugpy default.
    """
    with _temporary_root() as root:
        invocation = _invoke_run(["--root", root, "--breakpoint", "testrun-start", "--debugger", "pdb"])

    invocation.runtime_overrides.override_debug_debugger.assert_called_once_with("pdb")
    return


def test_run_diagnostic_flags_override_the_runtime_variables() -> None:
    """
        The pre- and post-run diagnostic flags each enable their diagnostic
        capture through the application.
    """
    with _temporary_root() as root:
        invocation = _invoke_run(["--root", root, "--prerun-diagnostic", "--postrun-diagnostic"])

    assert invocation.app.override_for(RuntimeVariablesDesc.AM_DIAGNOSTICS_PRERUN) == {}
    assert invocation.app.override_for(RuntimeVariablesDesc.AM_DIAGNOSTICS_POSTRUN) == {}
    return


def test_run_marker_expressions_become_metafilters_on_the_job() -> None:
    """
        Include and exclude marker expressions are parsed into metafilters:
        include expressions become inclusive filters and exclude expressions
        exclusive ones, in the order given.
    """
    with _temporary_root() as root:
        invocation = _invoke_run(["--root", root, "--include-marker-exp", "'priority==1'",
                                  "--exclude-marker-exp", "\"category==slow\""])

    metafilters = invocation.job.metafilters
    assert len(metafilters) == 2
    include_filter, exclude_filter = metafilters
    assert include_filter.include is True
    assert exclude_filter.include is False
    return
