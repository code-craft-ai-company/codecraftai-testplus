"""
    .. module:: testplusdefaulttypefactory
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module that contains the factories for extending the TestPlus package to
    support included landscaping and interop protocols.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Type

from automojo.extension.factory.factoryextension import FactoryExtension

from automojo.testbase.factoryprotocols import TestBaseFactoryProtocol
from automojo.testbase.testjob import TestJob

from automojo.testplus.distributedtestjob import DistributedTestJob

class TestPlusDefaultTypeFactory(FactoryExtension, TestBaseFactoryProtocol):
    """
        Provides the default implementations used by TestPlus.

        This factory supplies the default job type when none is explicitly
        specified.
    """

    PRECEDENCE = 20

    @classmethod
    def get_testbase_default_job_type(cls) -> Type[TestJob]:
        """
            Used to lookup and return the most relevant default job type as determined
            by the super factory search path.

            Mirrors the parent contract on
            :class:`automojo.testbase.factoryprotocols.TestBaseFactoryProtocol`,
            which declares this as a classmethod.  Without ``@classmethod`` the
            override fails to satisfy the protocol — it would be either an
            unbound function (no ``self`` / ``cls``) that crashes at call time,
            or an instance method whose signature differs from the parent's.
        """
        return DistributedTestJob
