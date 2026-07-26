"""
    .. module:: distributedtestjob
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing the :class:`DistributedTestJob` class which is the
               TestPlus parent container for distributed (multi-host) test runs.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.landscaping.testing.testjob import LandscapeTestJob

from ccai.testplus.distributedtestsequencer import DistributedTestSequencer


class DistributedTestJob(LandscapeTestJob):
    """
        TestPlus parent container for a distributed test run.

        Layered inheritance:

        * :class:`ccai.testbase.testjob.TestJob` — single-host base
          (lifecycle, recorder, sequencer factory, properties, ``execute``);
          standalone-default seams (stdout recorder).
        * :class:`ccai.integrationruntime.integratedtestjob.IntegratedTestJob` —
          integration tier: JSOS/HTML/presence-folder result recording and run
          metadata sourced from ``RuntimeVariables``.
        * :class:`ccai.landscaping.testing.testjob.LandscapeTestJob` —
          the landscaping tier: supplies the landscape singleton and carries
          the landscape-activation lifecycle on the two attachment hooks
          (``activate_configuration`` / ``activate_integration`` /
          ``activate_operations``, ``collect_resources``,
          ``establish_presence``).
        * :class:`DistributedTestJob` (this class) — constructs a
          :class:`DistributedTestSequencer` so the sequencer's
          ``attach_to_environment`` / ``attach_to_framework`` methods accept
          the landscape and so distributed-test scheduling primitives become
          available.

        Single Instance.  Setup Test Landscape.  Jobs have an expected number
        of tests based on includes / excludes.  Collects and organises results
        across hosts.  Can be subclassed to customise the sequencing of test
        packs across distributed infrastructure.
    """

    # Derived jobs set these to indicate that the test framework must load the
    # corresponding configuration maps before the run (opt-in; default False).
    # ``distributed_test_entrypoint`` reads them to call ``resolve_configuration_maps``.
    requires_credentials = False
    requires_landscape = False
    requires_runtime = False
    requires_topology = False

    def _create_sequencer(self) -> DistributedTestSequencer:
        """
            Hook used by :meth:`TestJob.execute` to construct the test
            sequencer for this job.  Returns a
            :class:`DistributedTestSequencer` so the sequencer's
            ``attach_to_environment`` / ``attach_to_framework`` methods
            accept the landscape supplied by
            :class:`LandscapeTestJob`.

            :returns: A :class:`DistributedTestSequencer` configured with
                      this job's title, test root, includes / excludes,
                      metafilters, and ``job_seed`` for reproducible
                      property-based testing.
        """
        inst = DistributedTestSequencer(
            self._title,
            self._testroot,
            includes=self.includes,
            excludes=self.excludes,
            metafilters=self.metafilters,
            job_seed=self.job_seed,
            output_context=self._output_context,
        )
        return inst


class DefaultDistributedTestJob(DistributedTestJob):
    """
        The :class:`DefaultDistributedTestJob` is utilized as a job container when a
        job was not specified.
    """
    name = "Test Job"
    description = "Unspecified test job."
