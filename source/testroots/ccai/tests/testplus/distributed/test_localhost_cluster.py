"""
    .. module:: test_localhost_cluster
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Distributed scenarios driven against helper processes on
               127.0.0.1, so they run on a single machine.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import threading
import time

from typing import Dict, List

from ccai.tests.testplus.distributed.factories import HelperCluster


def test_every_node_answers_ping(cluster: HelperCluster) -> None:
    """
        Every node in the cluster is reachable and is a distinct process.
    """
    replies = cluster.call_all("ping")

    assert all(reply["ok"] for reply in replies)
    assert [reply["node"] for reply in replies] == [node.node_id for node in cluster.nodes]
    assert len({reply["pid"] for reply in replies}) == len(cluster.nodes)
    return


def test_fan_out_echo_keeps_payloads_with_their_node(cluster: HelperCluster) -> None:
    """
        A fan-out sends a different payload to each node and every reply
        comes back from the node it was sent to, carrying that payload.
    """
    payloads = {node.node_id: "payload-for-{}".format(node.node_id) for node in cluster.nodes}

    replies = [node.call("echo", payload=payloads[node.node_id]) for node in cluster.nodes]

    for node, reply in zip(cluster.nodes, replies):
        assert reply["node"] == node.node_id
        assert reply["payload"] == payloads[node.node_id]
    return


def test_concurrent_calls_do_not_cross_wires(cluster: HelperCluster) -> None:
    """
        Many callers hitting the cluster at once each get exactly their
        own reply -- no interleaving between connections.
    """
    results: Dict[int, dict] = {}
    errors: List[BaseException] = []

    def worker(index: int) -> None:
        node = cluster.nodes[index % len(cluster.nodes)]
        try:
            results[index] = node.call("echo", payload=index)
        except BaseException as xcpt:  # surfaced below; a thread cannot fail the test itself
            errors.append(xcpt)

    threads = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(24)]
    for thread in threads:
        thread.start()
    # One deadline for the whole fan-in, not one per thread: a stuck worker
    # must fail the test in seconds, not stall it for minutes.
    deadline = time.time() + 20.0
    for thread in threads:
        thread.join(timeout=max(0.0, deadline - time.time()))
    assert not any(thread.is_alive() for thread in threads), "workers still running at the deadline"

    assert errors == []
    assert len(results) == 24
    for index, reply in results.items():
        assert reply["payload"] == index
        assert reply["node"] == cluster.nodes[index % len(cluster.nodes)].node_id
    return


def test_slow_node_does_not_block_the_others(cluster: HelperCluster) -> None:
    """
        A node busy with a long request must not delay replies from its
        peers: the cluster's nodes are independent.
    """
    slow = cluster.nodes[0]
    slow_thread = threading.Thread(target=slow.call, args=("sleep",), kwargs={"seconds": 1.5})
    slow_thread.start()
    time.sleep(0.1)

    started = time.time()
    replies = [node.call("ping") for node in cluster.nodes[1:]]
    elapsed = time.time() - started

    slow_thread.join(timeout=10.0)

    assert all(reply["ok"] for reply in replies)
    assert elapsed < 1.0, "peers waited {:.2f}s behind a busy node".format(elapsed)
    return


def test_a_dead_node_is_isolated_from_its_peers() -> None:
    """
        Killing one node leaves the rest answering, and the dead node's
        endpoint refuses rather than hanging.  Uses a private cluster so
        the shared one stays intact for other tests.
    """
    private = HelperCluster.spawn(2)
    try:
        private.nodes[0].kill()

        assert private.nodes[1].call("ping")["ok"]

        refused = False
        try:
            private.nodes[0].call("ping")
        except (ConnectionRefusedError, EOFError, OSError):
            refused = True
        assert refused
    finally:
        private.shutdown()
    return
