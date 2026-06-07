==========================
Code Craft AI TestPlus
==========================

The ``codecraftai-testplus`` package extends the ``codecraftai-testbase`` test framework with support for distributed and multi-host test jobs. Where ``testbase`` focuses on single-host test runs, ``testplus`` adds the pieces required to coordinate tests across a cluster of machines drawn from an ``codecraftai-landscaping`` landscape, including the ``DistributedTestJob`` parent-container abstraction, a distributed test sequencer, and a default type factory used to materialise shared resources across hosts.

Highlights
==========

- ``DistributedTestJob`` parent-container abstraction for multi-host jobs.
- Distributed test sequencer for coordinating execution across hosts.
- Default type factory for materialising shared resources across a cluster.
- ``testplus`` CLI (entry point ``testplus_command``) with ``run``, ``jobs``, and ``query`` subcommands mirroring the ``testbase`` surface.
- Designed to be used alongside ``codecraftai-testbase`` and ``codecraftai-landscaping``.

Repository Structure
====================

- ``development/`` - Runtime environment scripts.
- ``repository-setup/`` - Repository homing and setup scripts.
- ``source/packages/`` - Package source code.
- ``source/testroots/ccai/`` - TestBase test roots.
- ``specs/`` - Requirements, design, and task documentation.
- ``userguide/`` - Standards, conventions, and documentation.

Environment Setup
=================

When working in a Codex container:

.. code-block:: bash

   ./development/setup-agent-container

For local development:

.. code-block:: bash

   ./repository-setup/rehome-repository
   ./development/setup-environment

Running Tests
=============

Activate the virtual environment:

.. code-block:: bash

   source .venv/bin/activate

Run the single-host test suite:

.. code-block:: bash

   testbase testing run --root source/testroots/ccai --includes=ccai.tests.testplus.singlehost --output=./.output

Standards and Conventions
=========================

- Naming conventions: ``userguide/10-02-naming-conventions.rst``
- Code organization: ``userguide/10-01-code-organization.rst``
- Coding standards: ``userguide/10-00-coding-standards.rst``

Additional Resources
====================

- User guide entry point: ``userguide/userguide.rst``
- Design documentation: ``specs/design.md``
- Requirements: ``specs/requirements.md``
