"""
    .. module:: test_distributedtestjob
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for :class:`DistributedTestJob` and the testplus
               default type factory, without a landscape.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import os
import tempfile

from ccai.extension.factory.factoryextension import FactoryExtension

from ccai.integrationruntime.integratedtestjob import IntegratedTestJob
from ccai.integrationruntime.integrationruntimedefaulttypefactory import IntegrationRuntimeDefaultTypeFactory

from ccai.landscaping.testing.testjob import LandscapeTestJob

from ccai.testbase.factoryprotocols import TestBaseFactoryProtocol
from ccai.testbase.markers import parse_marker_expression
from ccai.testbase.output.outputcontext import SimpleOutputContext
from ccai.testbase.testjob import TestJob

from ccai.thisapp.wellknown import ConfiguredSuperFactorySingleton

from ccai.testplus.distributedtestjob import DefaultDistributedTestJob, DistributedTestJob
from ccai.testplus.distributedtestsequencer import DistributedTestSequencer
from ccai.testplus.testplusdefaulttypefactory import TestPlusDefaultTypeFactory


class FakeRunMetadata:
    """
        Supplies the job seed the sequencer factory reads from run metadata.
    """

    def __init__(self, job_seed: str):
        self.job_seed = job_seed
        return


def _make_unactivated_job(title: str, testroot: str, includes, excludes, metafilters, job_seed: str,
                          output_context: SimpleOutputContext) -> DistributedTestJob:
    """
        Builds a :class:`DistributedTestJob` without running its constructor,
        which would require an activated test-run process, and gives it only
        the state the sequencer factory reads.
    """
    job = object.__new__(DistributedTestJob)
    job._title = title
    job._testroot = testroot
    job.includes = includes
    job.excludes = excludes
    job.metafilters = metafilters
    job._run_metadata = FakeRunMetadata(job_seed)
    job._output_context = output_context
    return job


def test_distributed_job_sits_at_the_bottom_of_the_job_chain() -> None:
    """
        The job chain is ``TestJob -> IntegratedTestJob -> LandscapeTestJob ->
        DistributedTestJob`` so the landscape lifecycle and integration
        recording are both inherited.
    """
    assert issubclass(DistributedTestJob, LandscapeTestJob)
    assert issubclass(LandscapeTestJob, IntegratedTestJob)
    assert issubclass(IntegratedTestJob, TestJob)
    assert issubclass(DefaultDistributedTestJob, DistributedTestJob)
    return


def test_distributed_job_requires_no_configuration_maps_by_default() -> None:
    """
        Configuration maps are opt-in: a job that does not declare a need for
        them must not force the entry point to load any.
    """
    assert DistributedTestJob.requires_credentials is False
    assert DistributedTestJob.requires_landscape is False
    assert DistributedTestJob.requires_runtime is False
    assert DistributedTestJob.requires_topology is False
    return


def test_create_sequencer_builds_a_distributed_sequencer_from_the_job_settings() -> None:
    """
        The sequencer hook returns a :class:`DistributedTestSequencer` carrying
        the job's title, root, includes, excludes, metafilters, seed and output
        context, so the landscape-aware attachment methods are the ones the
        run uses.
    """
    output_dir = tempfile.mkdtemp(prefix="testplus-job-")
    try:
        testroot = os.path.join(output_dir, "root")
        includes = ["ccai.tests@#test_a"]
        excludes = ["ccai.tests@#test_b"]
        metafilters = [parse_marker_expression("+priority==1")]
        output_context = SimpleOutputContext(output_dir)
        job = _make_unactivated_job("Unit Job", testroot, includes, excludes, metafilters, "seed-123", output_context)

        sequencer = job._create_sequencer()

        assert isinstance(sequencer, DistributedTestSequencer)
        assert sequencer._jobtitle == "Unit Job"
        assert sequencer._root == testroot
        assert sequencer._includes is includes
        assert sequencer._excludes is excludes
        assert sequencer._metafilters is metafilters
        assert sequencer.job_seed == "seed-123"
        assert sequencer.output_context is output_context
    finally:
        os.rmdir(output_dir)
    return


def test_default_type_factory_supplies_the_distributed_job_as_a_classmethod() -> None:
    """
        The factory answers the protocol on the class itself, as the protocol
        declares, and names :class:`DistributedTestJob` as the default job.
    """
    job_type = TestPlusDefaultTypeFactory.get_testbase_default_job_type()

    assert job_type is DistributedTestJob
    assert isinstance(TestPlusDefaultTypeFactory.__dict__["get_testbase_default_job_type"], classmethod)
    return


def test_default_type_factory_outranks_the_lower_tier_factories() -> None:
    """
        The testplus factory must take precedence over the testbase and
        integration-runtime default factories so the ``testplus`` command
        builds distributed jobs rather than their single-host parents.
    """
    assert issubclass(TestPlusDefaultTypeFactory, FactoryExtension)
    assert issubclass(TestPlusDefaultTypeFactory, TestBaseFactoryProtocol)
    assert TestPlusDefaultTypeFactory.PRECEDENCE > IntegrationRuntimeDefaultTypeFactory.PRECEDENCE
    assert TestPlusDefaultTypeFactory.PRECEDENCE > FactoryExtension.PRECEDENCE
    return


def test_configured_super_factory_resolves_the_distributed_job_as_default() -> None:
    """
        With the testplus persona established, the configured super factory
        resolves the default job type to :class:`DistributedTestJob`, which is
        what the CLI's ``run`` and ``query`` commands rely on.
    """
    super_factory = ConfiguredSuperFactorySingleton()

    job_type = super_factory.get_override_types_by_order(TestBaseFactoryProtocol.get_testbase_default_job_type)

    assert job_type is DistributedTestJob
    return
