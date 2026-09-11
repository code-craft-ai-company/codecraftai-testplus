"""
    .. module:: test_cli_root
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the ``testplus`` root command: runtime
               initialisation, verbosity handling and the mounted command tree.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import contextlib

from typing import List, Tuple
from unittest.mock import patch

from click.testing import CliRunner

from ccai.testbase.properties import run_property
from ccai.testbase.properties import strategies as st

from ccai.thisapp.runtimevariables import RuntimeVariablesDesc

from ccai.testplus.cli import testplus_command
from ccai.testplus.cli.testplus_command import testplus_root_command

from ccai.tests.testplus.singlehost.fakes import CallRecorder, FakeThisApplication


def _invoke_root(args: List[str]) -> Tuple[object, FakeThisApplication, CallRecorder]:
    """
        Invokes the root command with ``args`` followed by the harmless
        ``testing jobs list`` subcommand, so the root callback runs to
        completion without starting a test run.
    """
    app = FakeThisApplication()
    initialize_runtime = CallRecorder()
    runner = CliRunner()

    with contextlib.ExitStack() as stack:
        stack.enter_context(patch.object(testplus_command, "initialize_testplus_runtime", initialize_runtime))
        stack.enter_context(patch.object(testplus_command, "ThisApplicationSingleton", lambda: app))
        result = runner.invoke(testplus_root_command, list(args) + ["testing", "jobs", "list"])

    rtnval = (result, app, initialize_runtime)
    return rtnval


def _expected_console_level(verbose: int) -> str:
    if verbose <= 0:
        rtnval = "WARNING"
    elif verbose == 1:
        rtnval = "INFO"
    elif verbose == 2:
        rtnval = "DEBUG"
    else:
        rtnval = "NOTSET"
    return rtnval


def test_root_command_initialises_the_runtime_before_dispatching() -> None:
    """
        The root callback initialises the testplus runtime exactly once and
        then hands off to the subcommand.
    """
    result, _app, initialize_runtime = _invoke_root([])

    assert result.exit_code == 0, result.output
    assert initialize_runtime.call_count == 1
    return


def test_root_command_without_verbosity_selects_an_interactive_console() -> None:
    """
        No ``-v`` means an interactive console at the WARNING level.
    """
    _result, app, _initialize_runtime = _invoke_root([])

    assert app.override_for(RuntimeVariablesDesc.AM_INTERACTIVE_CONSOLE) is True
    assert app.override_for(RuntimeVariablesDesc.AM_LOG_LEVEL_CONSOLE) == "WARNING"
    return


def test_root_command_verbosity_disables_the_interactive_console() -> None:
    """
        Any ``-v`` switches the console from interactive to plain logging.
    """
    _result, app, _initialize_runtime = _invoke_root(["-v"])

    assert app.override_for(RuntimeVariablesDesc.AM_INTERACTIVE_CONSOLE) is False
    return


def test_root_command_verbosity_count_maps_to_the_console_log_level() -> None:
    """
        For every verbosity count: none is WARNING, one is INFO, two is DEBUG
        and three or more is NOTSET.
    """
    def check(verbose: int) -> None:
        args = ["-v"] * verbose
        _result, app, _initialize_runtime = _invoke_root(args)
        assert app.override_for(RuntimeVariablesDesc.AM_LOG_LEVEL_CONSOLE) == _expected_console_level(verbose)
        return

    examples = run_property(check, max_examples=12, verbose=st.integers(min_value=0, max_value=6))

    assert examples == 12
    return


def test_root_command_mounts_only_the_testing_group() -> None:
    """
        Only the ``testing`` group is mounted on the root (testbase's arcli
        groups cannot be dispatched by a click group), and it carries the
        ``jobs``, ``query`` and ``run`` commands.
    """
    assert sorted(testplus_root_command.commands.keys()) == ["testing"]

    testing_group = testplus_root_command.commands["testing"]
    assert sorted(testing_group.commands.keys()) == ["jobs", "query", "run"]
    return


def test_root_help_renders_every_mounted_command() -> None:
    """
        ``testplus --help`` renders (formatting root help walks every mounted
        command, which is what broke when arcli groups were mounted).
    """
    runner = CliRunner()

    result = runner.invoke(testplus_root_command, ["--help"])

    assert result.exit_code == 0, result.output
    assert "testing" in result.output
    return
