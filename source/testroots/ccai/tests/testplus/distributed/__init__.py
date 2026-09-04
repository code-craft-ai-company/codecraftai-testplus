"""
    Distributed-scenario tests for testplus.

    Two tiers live here:

    * ``test_localhost_cluster`` -- runs everywhere.  A cluster of helper
      PROCESSES on 127.0.0.1 stands in for remote nodes, so fan-out,
      isolation and concurrency behaviour is exercised without any second
      machine.
    * ``test_multihost_scenarios`` -- the same scenarios over real hosts
      declared in a landscape.  Gated behind ``CCAI_DISTRIBUTED_TESTS=1``
      and skipped otherwise, so the package is safe in a single-host gate.

    The helper cluster is originated here with package lifespan so every
    test in the package shares one set of nodes.
"""

from ccai import testbase
from ccai.testbase.resourcelifespan import ResourceLifespan

from ccai.tests.testplus.distributed.factories import create_helper_cluster

testbase.originate.parameter(create_helper_cluster, identifier="cluster",
                             life_span=ResourceLifespan.Package)
