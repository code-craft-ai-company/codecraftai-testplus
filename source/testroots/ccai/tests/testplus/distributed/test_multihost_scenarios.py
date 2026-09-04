"""
    .. module:: test_multihost_scenarios
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The distributed scenarios over REAL hosts declared in a
               landscape.

    These are written to run under a DistributedTestJob with a landscape
    that declares at least two SSH-reachable hosts.  They are gated: unless
    ``CCAI_DISTRIBUTED_TESTS=1`` is set AND such a landscape is active, every
    test here raises SkipError.  That keeps the package safe in a
    single-host gate while the scenarios themselves are complete.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import os
import threading
import uuid

from typing import Dict, List

from ccai.errors.exceptions import SkipError

GATE_VARIABLE = "CCAI_DISTRIBUTED_TESTS"
MINIMUM_HOSTS = 2


def _require_ssh_hosts() -> List:
    """
        The SSH devices of the active landscape, or a skip explaining what
        is missing.
    """
    if os.environ.get(GATE_VARIABLE) != "1":
        raise SkipError("multi-host scenarios are gated; set {}=1 with a landscape "
                        "declaring at least {} ssh hosts".format(GATE_VARIABLE, MINIMUM_HOSTS))

    from ccai.landscaping.coordinators.ssh.sshdevice import SshDevice
    from ccai.landscaping.wellknown import LandscapeSingleton

    devices = [dev for dev in LandscapeSingleton().get_devices() if isinstance(dev, SshDevice)]
    if len(devices) < MINIMUM_HOSTS:
        raise SkipError("landscape declares {} ssh host(s); these scenarios need {}".format(
            len(devices), MINIMUM_HOSTS))
    return devices


def test_every_host_answers() -> None:
    """
        Every declared host runs a trivial command successfully.
    """
    hosts = _require_ssh_hosts()

    for host in hosts:
        status, stdout, _stderr = host.ssh.run_cmd("echo alive")
        assert status == 0, host
        assert stdout.strip() == "alive", host
    return


def test_hosts_are_distinct_machines() -> None:
    """
        The declared hosts are different machines, not one host listed
        twice: their hostnames are all distinct.
    """
    hosts = _require_ssh_hosts()

    hostnames = []
    for host in hosts:
        status, stdout, _stderr = host.ssh.run_cmd("hostname")
        assert status == 0, host
        hostnames.append(stdout.strip())

    assert len(set(hostnames)) == len(hosts), hostnames
    return


def test_fan_out_command_completes_on_every_host() -> None:
    """
        A command fanned out concurrently to all hosts completes on each
        and each reply is tied to the host it ran on.
    """
    hosts = _require_ssh_hosts()
    tokens = {id(host): uuid.uuid4().hex for host in hosts}
    replies: Dict[int, str] = {}
    errors: List[BaseException] = []

    def worker(host) -> None:
        try:
            _status, stdout, _stderr = host.ssh.run_cmd("echo {}".format(tokens[id(host)]))
            replies[id(host)] = stdout.strip()
        except BaseException as xcpt:  # surfaced below; a thread cannot fail the test itself
            errors.append(xcpt)

    threads = [threading.Thread(target=worker, args=(host,)) for host in hosts]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=120.0)

    assert errors == []
    assert replies == tokens
    return


def test_a_failing_host_does_not_fail_its_peers() -> None:
    """
        A command that fails on one host reports failure there only; the
        other hosts still complete.
    """
    hosts = _require_ssh_hosts()
    victim, peers = hosts[0], hosts[1:]

    status, _stdout, _stderr = victim.ssh.run_cmd("exit 3", exp_status=3)
    assert status == 3

    for host in peers:
        status, stdout, _stderr = host.ssh.run_cmd("echo ok")
        assert status == 0 and stdout.strip() == "ok", host
    return
