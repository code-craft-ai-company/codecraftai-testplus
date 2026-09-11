"""
    .. module:: test_cli_jobs
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for ``testplus testing jobs``: the placeholder
               ``list`` and ``show`` commands and the ``run`` command's job
               identifier handling, driven with ``click.testing.CliRunner``.

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
from unittest.mock import patch

from click.testing import CliRunner

from ccai.thisapp import activation
from ccai.thisapp import wellknown
from ccai.thisapp.enumerations import JobType

from ccai.testplus import initialize
from ccai.testplus.cli.cmdtree.testing.jobs import (
    command_testing_jobs_list,
    command_testplus_testing_jobs_run,
    command_testplus_testing_jobs_show,
    group_testplus_testing_jobs,
)

from ccai.tests.testplus.singlehost.fakes import (
    CallRecorder,
    FakeSuperFactory,
    NamedStubJob,
    StubTestJob,
    make_stub_job_type,
)

NAMED_JOB_IDENTIFIER = "ccai.tests.testplus.singlehost.fakes@NamedStubJob"


class JobsRunInvocation:
    """
        Everything one invocation of ``jobs run`` touched.
    """

    def __init__(self, default_job_type: Type[StubTestJob]):
        self.default_job_type = default_job_type
        self.super_factory = FakeSuperFactory(default_job_type)
        self.activate_profile_job = CallRecorder()
        self.initialize_results = CallRecorder()
        self.result = None
        self.python_path_after: List[str] = []
        return


def _invoke_jobs_run(args: List[str], default_job_type: Optional[Type[StubTestJob]] = None) -> JobsRunInvocation:
    if default_job_type is None:
        default_job_type = make_stub_job_type()
    invocation = JobsRunInvocation(default_job_type)
    runner = CliRunner()
    saved_path = list(sys.path)

    try:
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(activation, "activate_profile_job", invocation.activate_profile_job))
            stack.enter_context(patch.object(initialize, "initialize_testplus_results", invocation.initialize_results))
            stack.enter_context(patch.object(wellknown, "ConfiguredSuperFactorySingleton", lambda: invocation.super_factory))
            invocation.result = runner.invoke(command_testplus_testing_jobs_run, args)
        invocation.python_path_after = list(sys.path)
    finally:
        sys.path[:] = saved_path

    return invocation


@contextlib.contextmanager
def _temporary_root():
    root = tempfile.mkdtemp(prefix="testplus-jobs-")
    try:
        yield root
    finally:
        os.rmdir(root)
    return


def test_jobs_group_mounts_list_show_and_run() -> None:
    """
        The ``jobs`` group carries exactly the ``list``, ``show`` and ``run``
        commands.
    """
    assert sorted(group_testplus_testing_jobs.commands.keys()) == ["list", "run", "show"]
    return


def test_jobs_list_reports_that_it_is_not_implemented() -> None:
    """
        ``jobs list`` is a placeholder: it succeeds but says so.
    """
    runner = CliRunner()

    result = runner.invoke(command_testing_jobs_list, [])

    assert result.exit_code == 0, result.output
    assert "'jobs list' command is not yet implemented" in result.output
    return


def test_jobs_show_requires_a_job_and_reports_that_it_is_not_implemented() -> None:
    """
        ``jobs show`` insists on ``--job`` and is otherwise a placeholder.
    """
    runner = CliRunner()

    missing = runner.invoke(command_testplus_testing_jobs_show, [])
    given = runner.invoke(command_testplus_testing_jobs_show, ["--job", "pkg.mod@Job"])

    assert missing.exit_code == 2
    assert given.exit_code == 0, given.output
    assert "'jobs show' command is not yet implemented" in given.output
    return


def test_jobs_run_rejects_a_root_that_does_not_exist() -> None:
    """
        A missing root is a ``--root`` parameter error.
    """
    missing_root = os.path.join(tempfile.gettempdir(), "testplus-no-such-root")

    invocation = _invoke_jobs_run(["--root", missing_root, "--job", NAMED_JOB_IDENTIFIER])

    assert invocation.result.exit_code == 2
    assert "does not exist" in invocation.result.output
    return


def test_jobs_run_rejects_a_job_identifier_without_a_class_part() -> None:
    """
        ``--job`` must be ``package.module@JobClass``.
    """
    with _temporary_root() as root:
        invocation = _invoke_jobs_run(["--root", root, "--job", "ccai.testplus.distributedtestjob"])

    assert invocation.result.exit_code == 2
    assert "package.module@JobClass" in invocation.result.output
    return


def test_jobs_run_rejects_a_job_package_that_cannot_be_imported() -> None:
    """
        An unimportable job package is reported as a ``--job`` parameter error
        rather than a traceback.
    """
    with _temporary_root() as root:
        invocation = _invoke_jobs_run(["--root", root, "--job", "ccai.testplus.no_such_module@Job"])

    assert invocation.result.exit_code == 2
    assert "Failure while importing job package" in invocation.result.output
    return


def test_jobs_run_rejects_a_missing_job_class() -> None:
    """
        A job package without the named class is a ``--job`` parameter error.
    """
    with _temporary_root() as root:
        invocation = _invoke_jobs_run(["--root", root, "--job", "ccai.testplus.distributedtestjob@NoSuchJob"])

    assert invocation.result.exit_code == 2
    assert "does not have a job type" in invocation.result.output
    return


def test_jobs_run_executes_the_named_job_type() -> None:
    """
        The job named by ``--job`` is imported, constructed with the absolute
        root and executed, and its result becomes the exit status; the default
        job type is not used.
    """
    default_job_type = make_stub_job_type()
    NamedStubJob.reset()

    with _temporary_root() as root:
        invocation = _invoke_jobs_run(["--root", root, "--job", NAMED_JOB_IDENTIFIER], default_job_type=default_job_type)
        expected_root = os.path.abspath(root)

    assert invocation.result.exit_code == NamedStubJob.exit_code, invocation.result.output
    assert default_job_type.instances == []
    assert len(NamedStubJob.instances) == 1
    job = NamedStubJob.instances[0]
    assert job.testroot == expected_root
    assert job.includes is None and job.excludes is None
    assert job.entered and job.executed and job.exited
    return


def test_jobs_run_activates_a_test_run_and_initialises_results() -> None:
    """
        Before the job runs the process is activated as a test run and the
        results output is initialised.
    """
    NamedStubJob.reset()

    with _temporary_root() as root:
        invocation = _invoke_jobs_run(["--root", root, "--job", NAMED_JOB_IDENTIFIER])

    assert invocation.activate_profile_job.calls == [((JobType.TestRun,), {})]
    assert invocation.initialize_results.call_count == 1
    return


def test_jobs_run_prepends_the_test_root_to_the_python_path() -> None:
    """
        The test root itself is put at the front of ``sys.path`` so the job
        package can be imported by name.
    """
    NamedStubJob.reset()

    with _temporary_root() as root:
        invocation = _invoke_jobs_run(["--root", root, "--job", NAMED_JOB_IDENTIFIER])
        expected_root = os.path.abspath(root)

    assert invocation.python_path_after[0] == expected_root
    return
