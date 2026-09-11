"""
    Single-host tests for testplus.

    Everything in this package runs on one machine with no landscape.  The
    ``test_helloworld`` module is the original integration-layer smoke test;
    the remaining modules are unit tests for the sequencer, the entry point,
    the initialisation helpers and the ``testplus`` command tree.

    The testplus product modules need an application persona at import time:
    ``ccai.testplus.distributedtestsequencer`` imports the landscape model,
    whose class body resolves ``ThisApplicationSingleton``.  Under the merge
    gate the ``testplus`` root command has already established the persona
    before discovery imports any test module, so the block below is a no-op
    there.  It exists so the same modules also import (and can be debugged)
    under plain ``pytest`` or a script runner, where nothing else has done it.
    The persona is the one ``initialize_testplus_runtime`` establishes, with
    the presence directory pointed at a throw-away temporary folder so a
    debugging run never writes into the developer's ``~/ccai`` tree.
"""

import tempfile

from ccai.thisapp import persona

if not persona.APP_PERSONA_ESTABLISHED:
    _presence_dir = tempfile.mkdtemp(prefix="ccai-testplus-singlehost-")
    persona.establish_app_persona(name="ccai", presence_dir=_presence_dir, logger_name="TP",
                                  extensions="ccai.testplus.testplusdefaulttypefactory",
                                  log_basename="testrun")
