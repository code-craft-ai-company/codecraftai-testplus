"""
    .. module:: distributedtestjob
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing the :class:`DistributedTestJob` class which is the
               TestPlus parent container for distributed (multi-host) test runs.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Any

from automojo.interop.testing.testjob import InteropLibraryTestJob

from automojo.landscaping.wellknown import LandscapeSingleton

from automojo.testplus.distributedtestsequencer import DistributedTestSequencer


class DistributedTestJob(InteropLibraryTestJob):
    """
        TestPlus parent container for a distributed test run.

        Layered inheritance:

        * :class:`automojo.testbase.testjob.TestJob` — single-host base
          (lifecycle, recorder, sequencer factory, properties, ``execute``);
          standalone-default seams (stdout recorder).
        * :class:`automojo.integrationruntime.integratedtestjob.IntegratedTestJob` —
          integration tier: JSOS/HTML/presence-folder result recording and run
          metadata sourced from ``RuntimeVariables``.
        * :class:`automojo.interop.testing.testjob.InteropLibraryTestJob` —
          adds the landscape-activation hooks (``fire_attach_to_environment``,
          ``fire_attach_to_framework``, ``fire_activate_configuration``,
          ``fire_activate_integration``, ``fire_activate_operations``).
        * :class:`DistributedTestJob` (this class) — supplies the concrete
          landscape via :meth:`_get_landscape` and constructs a
          :class:`DistributedTestSequencer` so the sequencer's
          ``attach_to_environment`` / ``attach_to_framework`` methods accept
          the landscape and so distributed-test scheduling primitives become
          available.

        Single Instance.  Setup Test Landscape.  Jobs have an expected number
        of tests based on includes / excludes.  Collects and organises results
        across hosts.  Can be subclassed to customise the sequencing of test
        packs across distributed infrastructure.
    """

    def _get_landscape(self) -> Any:
        """
            Returns the singleton :class:`Landscape` instance for the
            distributed test environment.

            :returns: The active :class:`Landscape`.
        """
        landscape = LandscapeSingleton()
        return landscape

    def _create_sequencer(self) -> DistributedTestSequencer:
        """
            Hook used by :meth:`TestJob.execute` to construct the test
            sequencer for this job.  Returns a
            :class:`DistributedTestSequencer` so the sequencer's
            ``attach_to_environment`` / ``attach_to_framework`` methods
            accept the landscape supplied by
            :class:`InteropLibraryTestJob`.

            :returns: A :class:`DistributedTestSequencer` configured with
                      this job's title, test root, includes / excludes,
                      metafilters, and ``job_seed`` for reproducible
                      property-based testing.
        """
        inst = DistributedTestSequencer(
            self.title,
            self._testroot,
            includes=self.includes,
            excludes=self.excludes,
            metafilters=self.metafilters,
            job_seed=self.job_seed,
        )
        return inst


class DefaultDistributedTestJob(DistributedTestJob):
    """
        The :class:`DefaultDistributedTestJob` is utilized as a job container when a
        job was not specified.
    """
    name = "Test Job"
    description = "Unspecified test job."
