"""
    .. module:: fakes
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Small recording stand-ins used by the single-host unit tests for
               testplus.  Every fake is a plain class (never a ``SimpleNamespace``)
               so it can be held weakly by product code, and every fake records
               what product code did to it so tests assert on behaviour rather
               than on return values alone.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import os
import shutil
import sys
import tempfile
import textwrap
import uuid

from typing import Any, Dict, List, Optional, Tuple, Type


# Shared, process-wide record of what the temporary test roots built by
# :class:`TempTestRoot` dispatch.  The generated test modules import this name
# and append to it, so a test can read back the order the sequencer ran
# factories and tests in.  Tests clear it before use.
DISPATCH_LOG: List[Any] = []


class RecordingCoupling:
    """
        Stands in for an :class:`IntegrationCoupling` registered with a sequencer.
        Each lifecycle call is appended to a shared log as
        ``(coupling name, method name, kwargs)`` so dispatch order across several
        couplings is observable.
    """

    def __init__(self, name: str, log: List[Tuple[str, str, Dict[str, Any]]]):
        self.name = name
        self.log = log
        return

    def attach_to_framework(self, **kwargs) -> None:
        self.log.append((self.name, "attach_to_framework", kwargs))
        return

    def attach_to_environment(self, **kwargs) -> None:
        self.log.append((self.name, "attach_to_environment", kwargs))
        return

    def collect_resources(self) -> None:
        self.log.append((self.name, "collect_resources", {}))
        return

    def establish_presence(self) -> None:
        self.log.append((self.name, "establish_presence", {}))
        return


class StartupFileCheckingCoupling(RecordingCoupling):
    """
        A coupling that records whether the sequencer's startup configuration
        file already existed when ``attach_to_environment`` was called.
    """

    def __init__(self, name: str, log: List[Tuple[str, str, Dict[str, Any]]], startup_file: str):
        super().__init__(name, log)
        self.startup_file = startup_file
        return

    def attach_to_environment(self, **kwargs) -> None:
        file_present = os.path.exists(self.startup_file)
        self.log.append((self.name, "attach_to_environment", {"startup_file_present": file_present}))
        return


class StubTestJob:
    """
        A test job stand-in that records how the CLI and entry point construct
        and drive it.  Use :func:`make_stub_job_type` to get a fresh subclass with
        its own ``instances`` list and result settings for each test.
    """

    name = "Stub Job"
    description = "A recording stand-in for a distributed test job."

    # Flags read by ``distributed_test_entrypoint`` to decide which
    # configuration maps to resolve.
    requires_credentials = False
    requires_landscape = False
    requires_runtime = False
    requires_topology = False

    instances: List["StubTestJob"] = []
    exit_code = 0
    query_results: Dict[str, Any] = {}
    import_error_files: List[str] = []

    def __init__(self, logger: Any, testroot: str, includes: Optional[List[str]] = None,
                 excludes: Optional[List[str]] = None, metafilters: Optional[List[Any]] = None,
                 test_module: Optional[Any] = None, parser: Optional[Any] = None):
        self.logger = logger
        self.testroot = testroot
        self.includes = includes
        self.excludes = excludes
        self.metafilters = metafilters
        self.test_module = test_module
        self.parser = parser
        self.executed = False
        self.queried = False
        self.entered = False
        self.exited = False
        type(self).instances.append(self)
        return

    def __enter__(self) -> "StubTestJob":
        self.entered = True
        return self

    def __exit__(self, ex_type, ex_inst, ex_tb) -> bool:
        self.exited = True
        return False

    @property
    def import_errors(self) -> List[str]:
        rtnval = list(type(self).import_error_files)
        return rtnval

    def execute(self) -> int:
        self.executed = True
        rtnval = type(self).exit_code
        return rtnval

    def query(self) -> Dict[str, Any]:
        self.queried = True
        rtnval = type(self).query_results
        return rtnval


def make_stub_job_type(exit_code: int = 0, query_results: Optional[Dict[str, Any]] = None,
                       import_error_files: Optional[List[str]] = None,
                       requires_credentials: bool = False, requires_landscape: bool = False,
                       requires_runtime: bool = False, requires_topology: bool = False) -> Type[StubTestJob]:
    """
        Creates a fresh :class:`StubTestJob` subclass so each test owns its own
        instance record and result settings.

        :param exit_code: The value ``execute`` returns.
        :param query_results: The mapping ``query`` returns.
        :param import_error_files: The files reported through ``import_errors``.
        :param requires_credentials: Value for the credentials configuration flag.
        :param requires_landscape: Value for the landscape configuration flag.
        :param requires_runtime: Value for the runtime configuration flag.
        :param requires_topology: Value for the topology configuration flag.

        :returns: A new job type.
    """
    if query_results is None:
        query_results = {}
    if import_error_files is None:
        import_error_files = []

    attributes = {
        "instances": [],
        "exit_code": exit_code,
        "query_results": query_results,
        "import_error_files": import_error_files,
        "requires_credentials": requires_credentials,
        "requires_landscape": requires_landscape,
        "requires_runtime": requires_runtime,
        "requires_topology": requires_topology,
    }
    job_type = type("StubTestJobForTest", (StubTestJob,), attributes)
    return job_type


class NamedStubJob(StubTestJob):
    """
        A module-level job type the ``jobs run`` command can import by name as
        ``ccai.tests.testplus.singlehost.fakes@NamedStubJob``.  Call
        :meth:`reset` before use because its record is shared.
    """

    instances: List["StubTestJob"] = []
    exit_code = 4

    @classmethod
    def reset(cls) -> None:
        cls.instances = []
        return


class FakeSubscription:
    """
        Stands in for a parameter subscription on a queried test reference.
    """

    def __init__(self, source: str):
        self.source = source
        return

    def describe_source(self) -> str:
        return self.source


class FakeTestRef:
    """
        Stands in for a :class:`TestRef` returned from ``TestJob.query``.
    """

    def __init__(self, subscriptions: Optional[Dict[str, FakeSubscription]] = None):
        if subscriptions is None:
            subscriptions = {}
        self.subscriptions = subscriptions
        return


class FakeContext:
    """
        Stands in for the application context tree: ``lookup`` returns a
        pre-seeded value and ``insert`` records what was written.
    """

    def __init__(self):
        self.values: Dict[str, Any] = {"/environment": {}}
        self.inserted: List[Tuple[str, Any]] = []
        return

    def lookup(self, path: str) -> Any:
        rtnval = self.values[path]
        return rtnval

    def insert(self, path: str, value: Any) -> None:
        self.inserted.append((path, value))
        return


class FakeThisApplication:
    """
        Stands in for the ``ThisApplication`` singleton, recording every
        variable override.
    """

    def __init__(self):
        self.context = FakeContext()
        self.overrides: List[Tuple[Any, Any]] = []
        return

    def override_variable_value(self, var_desc: Any, value: Any) -> None:
        self.overrides.append((var_desc, value))
        return

    def override_for(self, var_desc: Any) -> Any:
        """
            Returns the last value overridden for ``var_desc``.

            :param var_desc: The variable descriptor to look up.

            :returns: The last override value.
            :raises: KeyError
        """
        matches = [value for desc, value in self.overrides if desc is var_desc]
        if len(matches) == 0:
            raise KeyError(var_desc)
        rtnval = matches[-1]
        return rtnval


class FakeSuperFactory:
    """
        Stands in for the configured super factory, always resolving the
        supplied job type and recording which protocol method was asked for.
    """

    def __init__(self, job_type: Type[Any]):
        self.job_type = job_type
        self.requests: List[Any] = []
        return

    def get_override_types_by_order(self, protocol_method: Any) -> Type[Any]:
        self.requests.append(protocol_method)
        return self.job_type


class CallRecorder:
    """
        A callable that records every call's positional and keyword arguments
        and returns a fixed value.
    """

    def __init__(self, return_value: Any = None):
        self.calls: List[Tuple[tuple, dict]] = []
        self.return_value = return_value
        return

    def __call__(self, *args, **kwargs) -> Any:
        self.calls.append((args, kwargs))
        return self.return_value

    @property
    def call_count(self) -> int:
        rtnval = len(self.calls)
        return rtnval


class TempTestRoot:
    """
        A throw-away testbase test root on disk with a unique root package name,
        so a sequencer can be driven end-to-end without touching the real test
        tree.  Modules written through :meth:`write_module` may import
        ``DISPATCH_LOG`` from this module to record what ran.

        The root's parent directory is added to ``sys.path`` on creation;
        :meth:`cleanup` removes it again along with any modules imported from
        the root and the directory itself.
    """

    def __init__(self):
        self.base_dir = tempfile.mkdtemp(prefix="testplus-seq-")
        self.root_name = "tproot_{}".format(uuid.uuid4().hex[:10])
        self.root_dir = os.path.join(self.base_dir, self.root_name)
        self.output_dir = os.path.join(self.base_dir, "output")
        os.makedirs(self.root_dir)
        os.makedirs(self.output_dir)
        with open(os.path.join(self.root_dir, "__testroot__.py"), "w") as rootf:
            rootf.write('ROOT_TYPE = "testbase"\n')
        with open(os.path.join(self.root_dir, "__init__.py"), "w") as initf:
            initf.write("")
        sys.path.insert(0, self.base_dir)
        return

    def write_module(self, dotted_name: str, source: str) -> str:
        """
            Writes a module under the root.  ``{root}`` in ``source`` is replaced
            with the root package name so modules can import each other.

            :param dotted_name: The module name relative to the root, ``pkg.test_mod``.
            :param source: The module source, dedented before writing.

            :returns: The full dotted module name including the root package.
        """
        parts = dotted_name.split(".")
        directory = self.root_dir
        for part in parts[:-1]:
            directory = os.path.join(directory, part)
            if not os.path.isdir(directory):
                os.makedirs(directory)
            init_file = os.path.join(directory, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, "w") as initf:
                    initf.write("")

        module_file = os.path.join(directory, parts[-1] + ".py")
        rendered = textwrap.dedent(source).replace("{root}", self.root_name)
        with open(module_file, "w") as modf:
            modf.write(rendered)

        full_name = "{}.{}".format(self.root_name, dotted_name)
        return full_name

    def write_package_init(self, dotted_name: str, source: str) -> None:
        """
            Overwrites a package's ``__init__.py`` with ``source`` (used to
            originate parameters at package scope).

            :param dotted_name: The package name relative to the root.
            :param source: The package source, dedented before writing.

            :returns: ``None``
        """
        directory = os.path.join(self.root_dir, *dotted_name.split("."))
        if not os.path.isdir(directory):
            os.makedirs(directory)
        rendered = textwrap.dedent(source).replace("{root}", self.root_name)
        with open(os.path.join(directory, "__init__.py"), "w") as initf:
            initf.write(rendered)
        return

    def qualified(self, dotted_name: str) -> str:
        """
            Returns ``dotted_name`` prefixed with the root package name.

            :param dotted_name: A name relative to the root.

            :returns: The fully qualified name.
        """
        rtnval = "{}.{}".format(self.root_name, dotted_name)
        return rtnval

    def cleanup(self) -> None:
        """
            Removes the root from ``sys.path`` and ``sys.modules`` and deletes
            the directory.

            :returns: ``None``
        """
        while self.base_dir in sys.path:
            sys.path.remove(self.base_dir)

        stale_names = [name for name in sys.modules.keys() if name == self.root_name or name.startswith(self.root_name + ".")]
        for name in stale_names:
            del sys.modules[name]

        shutil.rmtree(self.base_dir, ignore_errors=True)
        return
