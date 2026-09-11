"""
    .. module:: test_cli_query
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for ``testplus testing query``: argument validation,
               the listing format and import-error reporting, driven with
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
from ccai.runtime import optionoverrides as runtime_optionoverrides

from ccai.thisapp import wellknown

from ccai.testplus import initialize
from ccai.testplus.cli.cmdtree.testing.query import command_testplus_testing_query

from ccai.tests.testplus.singlehost.fakes import (
    CallRecorder,
    FakeSubscription,
    FakeSuperFactory,
    FakeTestRef,
    FakeThisApplication,
    StubTestJob,
    make_stub_job_type,
)


class QueryInvocation:
    """
        Everything one invocation of ``query`` touched.
    """

    def __init__(self, job_type: Type[StubTestJob]):
        self.job_type = job_type
        self.app = FakeThisApplication()
        self.super_factory = FakeSuperFactory(job_type)
        self.resolve_configuration_maps = CallRecorder()
        self.initialize_results = CallRecorder()
        self.runtime_overrides = create_autospec(runtime_optionoverrides.AM_RUNTIME_OPTION_OVERRIDES)
        self.result = None
        return

    @property
    def job(self) -> StubTestJob:
        assert len(self.job_type.instances) == 1, "expected exactly one job to be constructed"
        rtnval = self.job_type.instances[0]
        return rtnval


def _invoke_query(args: List[str], job_type: Optional[Type[StubTestJob]] = None) -> QueryInvocation:
    if job_type is None:
        job_type = make_stub_job_type()
    invocation = QueryInvocation(job_type)
    runner = CliRunner()
    saved_path = list(sys.path)

    try:
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(configurationmaps, "resolve_configuration_maps", invocation.resolve_configuration_maps))
            stack.enter_context(patch.object(initialize, "initialize_testplus_results", invocation.initialize_results))
            stack.enter_context(patch.object(wellknown, "ThisApplicationSingleton", lambda: invocation.app))
            stack.enter_context(patch.object(wellknown, "ConfiguredSuperFactorySingleton", lambda: invocation.super_factory))
            stack.enter_context(patch.object(runtime_optionoverrides, "AM_RUNTIME_OPTION_OVERRIDES", invocation.runtime_overrides))
            invocation.result = runner.invoke(command_testplus_testing_query, args)
    finally:
        sys.path[:] = saved_path

    return invocation


@contextlib.contextmanager
def _temporary_root():
    root = tempfile.mkdtemp(prefix="testplus-query-")
    try:
        yield root
    finally:
        os.rmdir(root)
    return


def test_query_rejects_a_root_that_does_not_exist() -> None:
    """
        A missing root directory is a parameter error and no job is built.
    """
    job_type = make_stub_job_type()
    missing_root = os.path.join(tempfile.gettempdir(), "testplus-no-such-root")

    invocation = _invoke_query(["--root", missing_root], job_type=job_type)

    assert invocation.result.exit_code == 2
    assert "does not exist" in invocation.result.output
    assert job_type.instances == []
    return


def test_query_builds_the_job_with_the_selection_and_queries_it() -> None:
    """
        The job is built with the absolute root and the include and exclude
        expressions, queried rather than executed, and the command succeeds.
    """
    job_type = make_stub_job_type()

    with _temporary_root() as root:
        invocation = _invoke_query(["--root", root, "-i", "pkg.a", "-x", "pkg.b"], job_type=job_type)
        expected_root = os.path.abspath(root)

    assert invocation.result.exit_code == 0, invocation.result.output
    job = invocation.job
    assert job.testroot == expected_root
    assert tuple(job.includes) == ("pkg.a",)
    assert tuple(job.excludes) == ("pkg.b",)
    assert job.queried is True
    assert job.executed is False
    return


def test_query_resolves_no_configuration_maps() -> None:
    """
        A query never loads credentials, landscape, runtime or topology maps,
        and still records the test root and initialises results.
    """
    with _temporary_root() as root:
        invocation = _invoke_query(["--root", root])

    assert invocation.resolve_configuration_maps.calls == [
        ((), {"use_credentials": False, "use_landscape": False, "use_runtime": False, "use_topology": False})
    ]
    invocation.runtime_overrides.override_testroot.assert_called_once_with(root)
    assert invocation.initialize_results.call_count == 1
    return


def test_query_lists_the_discovered_tests_in_sorted_order() -> None:
    """
        Test names are printed under a ``Tests:`` heading, indented and sorted.
    """
    query_results = {
        "pkg.test_mod#test_zulu": FakeTestRef(),
        "pkg.test_mod#test_alpha": FakeTestRef(),
        "pkg.test_mod#test_mike": FakeTestRef(),
    }
    job_type = make_stub_job_type(query_results=query_results)

    with _temporary_root() as root:
        invocation = _invoke_query(["--root", root], job_type=job_type)

    lines = invocation.result.output.splitlines()
    assert "Tests:" in lines
    heading_index = lines.index("Tests:")
    listed = lines[heading_index + 1:heading_index + 4]
    assert listed == ["    pkg.test_mod#test_alpha", "    pkg.test_mod#test_mike", "    pkg.test_mod#test_zulu"]
    return


def test_query_lists_parameter_sources_under_each_test() -> None:
    """
        Each subscribed parameter is listed under its test with the source the
        subscription describes, sorted by parameter name.
    """
    subscriptions = {
        "zeta": FakeSubscription("factories.make_zeta"),
        "alpha": FakeSubscription("factories.make_alpha"),
    }
    query_results = {"pkg.test_mod#test_one": FakeTestRef(subscriptions=subscriptions)}
    job_type = make_stub_job_type(query_results=query_results)

    with _temporary_root() as root:
        invocation = _invoke_query(["--root", root], job_type=job_type)

    lines = invocation.result.output.splitlines()
    test_index = lines.index("    pkg.test_mod#test_one")
    assert lines[test_index + 1] == "        alpha: factories.make_alpha"
    assert lines[test_index + 2] == "        zeta: factories.make_zeta"
    return


def test_query_reports_import_errors_after_the_listing() -> None:
    """
        Files that failed to import are reported under an ``IMPORT ERRORS:``
        heading so a silently missing module is visible.
    """
    broken_file = os.path.join("pkg", "test_broken.py")
    job_type = make_stub_job_type(import_error_files=[broken_file])

    with _temporary_root() as root:
        invocation = _invoke_query(["--root", root], job_type=job_type)

    assert invocation.result.exit_code == 0, invocation.result.output
    assert "IMPORT ERRORS:" in invocation.result.output
    assert "    " + broken_file in invocation.result.output
    return


def test_query_without_import_errors_prints_no_error_section() -> None:
    """
        A clean query does not print the import error heading.
    """
    with _temporary_root() as root:
        invocation = _invoke_query(["--root", root])

    assert "IMPORT ERRORS:" not in invocation.result.output
    return


def test_query_marker_expressions_become_metafilters_on_the_job() -> None:
    """
        Include and exclude marker expressions are parsed into inclusive and
        exclusive metafilters and handed to the job.
    """
    with _temporary_root() as root:
        invocation = _invoke_query(["--root", root, "--include-marker-exp", "priority==1",
                                    "--exclude-marker-exp", "category==slow"])

    metafilters = invocation.job.metafilters
    assert len(metafilters) == 2
    include_filter, exclude_filter = metafilters
    assert include_filter.include is True
    assert exclude_filter.include is False
    return
