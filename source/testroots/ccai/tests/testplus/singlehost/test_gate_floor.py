"""
    .. module:: test_gate_floor
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: A floor on the number of tests the merge gate collects, so a
               discovery regression fails loudly instead of quietly running
               fewer tests.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import contextlib
import io
import os

import ccai.tests

from ccai.testbase.testcollector import TestCollector

# The include expression the merge gate passes ('--includes=ccai.tests.testplus'
# in .github/workflows/merge_gate.yml).  The gate's '--root' is the directory
# that holds ``ccai/__testroot__.py``; it is derived from this package's
# location below so the check follows the checkout wherever it lives.
GATE_INCLUDES = "ccai.tests.testplus"

# The number of tests the gate collected when the single-host unit tests were
# added (roadmap phase 4a).  Raise it when tests are added; never lower it
# without removing tests on purpose.
TEST_COUNT_FLOOR = 86


def _gate_test_root() -> str:
    """
        The ``--root`` the gate uses: the parent of the ``ccai.tests`` package.
    """
    tests_dir = os.path.dirname(os.path.abspath(ccai.tests.__file__))
    root = os.path.dirname(tests_dir)
    return root


def test_gate_collects_at_least_the_roadmap_floor() -> None:
    """
        Counts the tests exactly the way the ``testplus testing run`` gate
        does: a :class:`TestCollector` over the gate's ``--root`` is asked to
        collect the gate's ``--includes`` expression, which walks the included
        packages, imports every module (modules already imported by the
        running gate are taken from ``sys.modules``, so nothing runs twice)
        and keeps the ``test_``-prefixed functions defined in each module.  The
        count of collected references is what the gate would run.

        Anything that makes discovery silently shrink -- a wrong ``--includes``
        prefix, a package missing its ``__init__``, an import error in a test
        module, a platform gate excluding a directory -- lowers the count below
        the floor and fails this test with the shortfall in the message.

        The traceback the collector prints for a module that fails to import is
        swallowed here because the gate's own discovery already reported it;
        the missing tests still count against the floor.
    """
    root = _gate_test_root()
    collector = TestCollector(root, excludes=[], metafilters=[])

    with contextlib.redirect_stdout(io.StringIO()):
        collector.collect_references(GATE_INCLUDES)
    collector.finalize_collection()

    collected = len(collector.references)

    errmsg_lines = [
        "The gate collected fewer tests than the floor. collected={} floor={}".format(collected, TEST_COUNT_FLOOR),
        "ROOT: {}".format(root),
        "INCLUDES: {}".format(GATE_INCLUDES),
    ]
    if len(collector.import_errors) > 0:
        errmsg_lines.append("IMPORT ERRORS:")
        for filename in sorted(collector.import_errors.keys()):
            errmsg_lines.append("    {}".format(filename))
    errmsg = os.linesep.join(errmsg_lines)

    assert collected >= TEST_COUNT_FLOOR, errmsg
    return
