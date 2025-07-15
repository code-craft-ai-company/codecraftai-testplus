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

from automojo.testbase.extensionprotocols import TestBaseExtensionProtocol
from automojo.testbase.testjob import TestJob

from automojo.testplus.distributedtestjob import DistributedTestJob

class TestPlusDefaultTypeFactory(FactoryExtension, TestBaseExtensionProtocol):
    """
        Provides the default implementations used by TestPlus.

        This factory supplies the default job type when none is explicitly
        specified.
    """

    PRECEDENCE = 20

    def get_testbase_default_job_type() -> Type[TestJob]:
        """
            Used to lookup and return the most relevant default job type as determined
            by the super factory search path.
        """
        return DistributedTestJob
