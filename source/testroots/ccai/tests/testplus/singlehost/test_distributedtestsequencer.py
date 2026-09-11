"""
    .. module:: test_distributedtestsequencer
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for :class:`DistributedTestSequencer` driven with
               in-process recording couplings and a throw-away test root, so no
               landscape or remote host is needed.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import contextlib
import importlib.util
import io
import json
import logging
import os
import sys
import types
import uuid

from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import patch

from ccai.testbase.output.outputcontext import SimpleOutputContext
from ccai.testbase.results.model.renderinfo import RenderInfo
from ccai.testbase.results.recorders.stdoutresultrecorder import StdoutResultRecorder
from ccai.testbase.sequencing import testsequencer

from ccai.testplus import distributedtestsequencer
from ccai.testplus.distributedtestsequencer import DistributedTestSequencer

from ccai.tests.testplus.singlehost.fakes import (
    DISPATCH_LOG,
    RecordingCoupling,
    StartupFileCheckingCoupling,
    TempTestRoot,
)


class FakeLandscape:
    """
        A landscape stand-in: the sequencer only stores and forwards it.
    """

    def __init__(self, label: str):
        self.label = label
        return


def _make_sequencer(root: str, includes: Optional[List[str]] = None, excludes: Optional[List[str]] = None,
                    output_dir: Optional[str] = None) -> DistributedTestSequencer:
    """
        Builds a :class:`DistributedTestSequencer` over ``root`` with a
        :class:`SimpleOutputContext` rooted at ``output_dir``.
    """
    if includes is None:
        includes = []
    if excludes is None:
        excludes = []
    output_context = SimpleOutputContext(output_dir)
    sequencer = DistributedTestSequencer("unit", root, includes=includes, excludes=excludes, metafilters=[],
                                         output_context=output_context)
    return sequencer


def _write_dependency_tree(troot: TempTestRoot) -> None:
    """
        Writes a package that originates a ``token`` parameter from a factory,
        one module with a test that consumes it plus one that does not, and a
        second module with a further test.  Every factory step and test call
        is appended to ``DISPATCH_LOG``.
    """
    troot.write_module("pkg.factories", '''
        from typing import Generator

        from ccai import testbase

        from ccai.tests.testplus.singlehost.fakes import DISPATCH_LOG


        @testbase.register.resource_factory()
        def create_token(constraints=None) -> Generator[str, None, None]:
            DISPATCH_LOG.append("factory-start")
            yield "token-value"
            DISPATCH_LOG.append("factory-stop")
    ''')
    troot.write_package_init("pkg", '''
        from ccai import testbase
        from ccai.testbase.resourcelifespan import ResourceLifespan

        from {root}.pkg.factories import create_token

        testbase.originate.parameter(create_token, identifier="token", life_span=ResourceLifespan.Package)
    ''')
    troot.write_module("pkg.test_alpha", '''
        from ccai.tests.testplus.singlehost.fakes import DISPATCH_LOG


        def test_one(token):
            DISPATCH_LOG.append(("test_one", token))
            return


        def test_two():
            DISPATCH_LOG.append(("test_two", None))
            return
    ''')
    troot.write_module("pkg.test_beta", '''
        from ccai.tests.testplus.singlehost.fakes import DISPATCH_LOG


        def test_three():
            DISPATCH_LOG.append(("test_three", None))
            return
    ''')
    return


def _run_to_completion(sequencer: DistributedTestSequencer, output_dir: str) -> Dict[str, Any]:
    """
        Drives the sequencer through the same phases ``TestJob.execute`` uses:
        discover, attach, expand, generate the sequence document and execute it
        with a stdout recorder.  The recorder's console summary is swallowed so
        it does not masquerade as the gate's own summary.

        :returns: The recorder's summary mapping.
    """
    landscape = FakeLandscape("run")

    # Integrations are not collected: the injection registry is process-wide,
    # so a nested run inside the gate would otherwise pick up the couplings the
    # outer run registered and hand them the fake landscape.  The temporary
    # root declares no integrations of its own.
    count = sequencer.discover(include_integrations=False)
    assert count > 0, "the temporary root must contain tests"

    with patch.object(distributedtestsequencer, "get_path_for_output", lambda: output_dir):
        sequencer.attach_to_framework(landscape=landscape)
        sequencer.attach_to_environment(landscape=landscape)

    sequencer.expand_test_tree_based_on_query()

    sequence_file = os.path.join(output_dir, "testrun_sequence.py")
    sequencer.generate_testrun_sequence_document(sequence_file)

    render_info = RenderInfo(title="unit", summary_filename=os.path.join(output_dir, "testrun_summary.json"),
                             summary_template=None,
                             stream_results_filename=os.path.join(output_dir, "testrun_results_stream.jsos"),
                             consolidated_results_filename=os.path.join(output_dir, "testrun_results.json"),
                             static_resource_source=None, static_resource_destination=None)
    runid = str(uuid.uuid4())
    recorder = StdoutResultRecorder(runid=runid, start=datetime.now(), render_info=render_info)

    # ``execute_tests`` loads the sequence document through ``import_file``
    # under the fixed module name 'sequence_document', which is served from
    # ``sys.modules`` once any sequencer in the process has loaded one.  Under
    # the gate that would hand this nested run the OUTER run's document, so the
    # document is loaded here from its file under a unique name instead.
    #
    # The nested run's scope contexts log every test outcome through the
    # process logger; a deliberately failing test would print a traceback into
    # the gate's log and read as a gate failure, so logging is disabled for
    # the duration of the nested run and restored afterwards.
    with patch.object(testsequencer, "import_file", _load_sequence_document):
        with contextlib.redirect_stdout(io.StringIO()):
            logging.disable(logging.CRITICAL)
            try:
                with recorder:
                    sequencer.execute_tests(runid, recorder)
                recorder.finalize()
            finally:
                logging.disable(logging.NOTSET)

    summary = recorder.summary
    return summary


def _load_sequence_document(name: str, location: str, by_file_only: bool = False) -> types.ModuleType:
    """
        Loads a generated sequence document from ``location`` as a module with
        a unique name, without registering it in ``sys.modules``.
    """
    unique_name = "{}_{}".format(name, uuid.uuid4().hex)
    spec = importlib.util.spec_from_file_location(unique_name, location)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sequencer_has_no_landscape_until_attached() -> None:
    """
        A freshly constructed sequencer holds no landscape; the landscape is
        supplied by the job through ``attach_to_framework``.
    """
    troot = TempTestRoot()
    try:
        sequencer = _make_sequencer(troot.root_dir, output_dir=troot.output_dir)
        assert sequencer._landscape is None

        landscape = FakeLandscape("attached")
        sequencer.attach_to_framework(landscape=landscape)

        assert sequencer._landscape is landscape
    finally:
        troot.cleanup()
    return


def test_attach_to_framework_forwards_landscape_to_every_integration() -> None:
    """
        Every registered integration receives the landscape by keyword.
    """
    troot = TempTestRoot()
    try:
        sequencer = _make_sequencer(troot.root_dir, output_dir=troot.output_dir)
        log: List[Any] = []
        sequencer._integrations = {
            "first": RecordingCoupling("first", log),
            "second": RecordingCoupling("second", log),
        }
        landscape = FakeLandscape("framework")

        sequencer.attach_to_framework(landscape=landscape)

        assert len(log) == 2
        for _name, method, kwargs in log:
            assert method == "attach_to_framework"
            assert kwargs == {"landscape": landscape}
    finally:
        troot.cleanup()
    return


def test_attach_to_framework_dispatches_in_registration_order() -> None:
    """
        Integrations are attached in the order they were registered, which is
        the order the collector established.
    """
    troot = TempTestRoot()
    try:
        sequencer = _make_sequencer(troot.root_dir, output_dir=troot.output_dir)
        log: List[Any] = []
        names = ["gamma", "alpha", "beta"]
        sequencer._integrations = {name: RecordingCoupling(name, log) for name in names}

        sequencer.attach_to_framework(landscape=FakeLandscape("order"))

        dispatched = [entry[0] for entry in log]
        assert dispatched == names
    finally:
        troot.cleanup()
    return


def test_attach_to_environment_writes_startup_configuration() -> None:
    """
        Attaching to the environment records the command line, the environment
        and the loaded top-level packages in ``startup-configuration.json``
        under the run's output path.
    """
    troot = TempTestRoot()
    try:
        sequencer = _make_sequencer(troot.root_dir, output_dir=troot.output_dir)

        with patch.object(distributedtestsequencer, "get_path_for_output", lambda: troot.output_dir):
            sequencer.attach_to_environment(landscape=FakeLandscape("env"))

        startup_file = os.path.join(troot.output_dir, "startup-configuration.json")
        assert os.path.isfile(startup_file)

        with open(startup_file, "r") as startf:
            startup = json.load(startf)

        assert list(startup.keys()) == ["command", "environment", "packages"]
        assert startup["command"] == " ".join(sys.argv)
        assert "ccai" in startup["packages"]
    finally:
        troot.cleanup()
    return


def test_attach_to_environment_masks_password_variables() -> None:
    """
        Environment variables whose name contains ``PASSWORD`` are written as
        ``(hidden)``; other variables keep their values.
    """
    troot = TempTestRoot()
    try:
        sequencer = _make_sequencer(troot.root_dir, output_dir=troot.output_dir)
        injected = {"CCAI_UNIT_DB_PASSWORD": "secret-value", "CCAI_UNIT_PLAIN": "visible-value"}

        with patch.dict(os.environ, injected):
            with patch.object(distributedtestsequencer, "get_path_for_output", lambda: troot.output_dir):
                sequencer.attach_to_environment(landscape=FakeLandscape("env"))

        with open(os.path.join(troot.output_dir, "startup-configuration.json"), "r") as startf:
            startup = json.load(startf)

        environment = startup["environment"]
        assert environment["CCAI_UNIT_DB_PASSWORD"] == "(hidden)"
        assert environment["CCAI_UNIT_PLAIN"] == "visible-value"
        assert "secret-value" not in json.dumps(startup)
    finally:
        troot.cleanup()
    return


def test_attach_to_environment_forwards_landscape_after_recording_startup() -> None:
    """
        Integrations receive the landscape by keyword, in registration order,
        and only after the startup configuration has been written.
    """
    troot = TempTestRoot()
    try:
        sequencer = _make_sequencer(troot.root_dir, output_dir=troot.output_dir)
        startup_file = os.path.join(troot.output_dir, "startup-configuration.json")
        log: List[Any] = []
        sequencer._integrations = {
            "checker": StartupFileCheckingCoupling("checker", log, startup_file),
            "recorder": RecordingCoupling("recorder", log),
        }
        landscape = FakeLandscape("env")

        with patch.object(distributedtestsequencer, "get_path_for_output", lambda: troot.output_dir):
            sequencer.attach_to_environment(landscape=landscape)

        assert [entry[0] for entry in log] == ["checker", "recorder"]
        assert log[0][2] == {"startup_file_present": True}
        assert log[1][1] == "attach_to_environment"
        assert log[1][2] == {"landscape": landscape}
    finally:
        troot.cleanup()
    return


def test_discover_collects_every_test_under_the_included_package() -> None:
    """
        An include expression naming a package collects all of its tests.
    """
    troot = TempTestRoot()
    try:
        _write_dependency_tree(troot)
        sequencer = _make_sequencer(troot.root_dir, includes=[troot.qualified("pkg")], output_dir=troot.output_dir)

        count = sequencer.discover()

        expected = [
            troot.qualified("pkg.test_alpha#test_one"),
            troot.qualified("pkg.test_alpha#test_two"),
            troot.qualified("pkg.test_beta#test_three"),
        ]
        assert count == 3
        assert sorted(sequencer.references.keys()) == expected
    finally:
        troot.cleanup()
    return


def test_discover_with_test_name_filter_selects_a_partial_run() -> None:
    """
        An include expression carrying a test-name filter narrows discovery to
        the matching tests only.
    """
    troot = TempTestRoot()
    try:
        _write_dependency_tree(troot)
        include = troot.qualified("pkg.test_alpha@#test_one")
        sequencer = _make_sequencer(troot.root_dir, includes=[include], output_dir=troot.output_dir)

        count = sequencer.discover()

        assert count == 1
        assert list(sequencer.references.keys()) == [troot.qualified("pkg.test_alpha#test_one")]
    finally:
        troot.cleanup()
    return


def test_execute_runs_dependencies_before_tests_in_sequence_order() -> None:
    """
        A full in-process run creates the package-scoped resource before the
        tests that depend on it, runs the tests in module then definition
        order, and tears the resource down after the last test.
    """
    troot = TempTestRoot()
    try:
        _write_dependency_tree(troot)
        del DISPATCH_LOG[:]
        sequencer = _make_sequencer(troot.root_dir, includes=[troot.qualified("pkg")], output_dir=troot.output_dir)

        summary = _run_to_completion(sequencer, troot.output_dir)

        expected = [
            "factory-start",
            ("test_one", "token-value"),
            ("test_two", None),
            ("test_three", None),
            "factory-stop",
        ]
        assert DISPATCH_LOG == expected
        assert summary["result"] == "PASSED"
        assert summary["detail"]["passed"] == 3
        assert summary["detail"]["total"] == 3
    finally:
        del DISPATCH_LOG[:]
        troot.cleanup()
    return


def test_execute_partial_run_dispatches_only_selected_tests() -> None:
    """
        A partial run still provisions the dependency the selected test needs
        but dispatches nothing that was not selected.
    """
    troot = TempTestRoot()
    try:
        _write_dependency_tree(troot)
        del DISPATCH_LOG[:]
        include = troot.qualified("pkg.test_alpha@#test_one")
        sequencer = _make_sequencer(troot.root_dir, includes=[include], output_dir=troot.output_dir)

        summary = _run_to_completion(sequencer, troot.output_dir)

        assert DISPATCH_LOG == ["factory-start", ("test_one", "token-value"), "factory-stop"]
        assert summary["detail"]["total"] == 1
        assert summary["detail"]["passed"] == 1
    finally:
        del DISPATCH_LOG[:]
        troot.cleanup()
    return


def test_execute_reports_a_failing_test_without_stopping_the_run() -> None:
    """
        A failing assertion is recorded as a failure while the remaining tests
        still run, and the run result is not PASSED.
    """
    troot = TempTestRoot()
    try:
        troot.write_module("pkg.test_mixed", '''
            from ccai.tests.testplus.singlehost.fakes import DISPATCH_LOG


            def test_fails():
                DISPATCH_LOG.append("test_fails")
                assert False, "deliberate failure"


            def test_passes():
                DISPATCH_LOG.append("test_passes")
                return
        ''')
        del DISPATCH_LOG[:]
        sequencer = _make_sequencer(troot.root_dir, includes=[troot.qualified("pkg")], output_dir=troot.output_dir)

        summary = _run_to_completion(sequencer, troot.output_dir)

        assert DISPATCH_LOG == ["test_fails", "test_passes"]
        assert summary["result"] != "PASSED"
        assert summary["detail"]["failed"] == 1
        assert summary["detail"]["passed"] == 1
    finally:
        del DISPATCH_LOG[:]
        troot.cleanup()
    return
