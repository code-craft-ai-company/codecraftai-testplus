"""
    .. module:: factories
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: A cluster of localhost helper processes for distributed
               scenarios that must run on one machine.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import os
import subprocess
import sys
import time

from collections.abc import Generator
from multiprocessing.connection import Client
from typing import Any, Dict, List, Optional

from ccai import testbase

from ccai.tests.testplus.distributed import _helpernode

HELPER_SCRIPT = os.path.abspath(_helpernode.__file__)
DEFAULT_CLUSTER_SIZE = 3
PORT_ANNOUNCE_TIMEOUT = 20.0


class HelperNode:
    """
        One helper process, addressed the way a remote node would be:
        by an endpoint, never by a shared object.
    """

    def __init__(self, node_id: str, process: subprocess.Popen, port: int) -> None:
        self.node_id = node_id
        self.process = process
        self.port = port
        return

    @property
    def endpoint(self) -> tuple:
        rtnval = ("127.0.0.1", self.port)
        return rtnval

    def call(self, op: str, **fields: Any) -> Dict[str, Any]:
        """
            Send one request and return the node's reply.  A fresh
            connection per call keeps the exchange stateless, as a remote
            RPC would be.
        """
        conn = Client(self.endpoint, authkey=_helpernode.AUTHKEY)
        try:
            conn.send(dict(op=op, **fields))
            rtnval = conn.recv()
        finally:
            conn.close()
        return rtnval

    def shutdown(self, timeout: float = 5.0) -> None:
        if self.process.poll() is None:
            try:
                self.call("shutdown")
            except (ConnectionRefusedError, EOFError, OSError):
                self.process.terminate()
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=timeout)
        return

    def kill(self) -> None:
        self.process.kill()
        self.process.wait(timeout=5.0)
        return


class HelperCluster:
    """
        The set of helper nodes a scenario runs against.
    """

    def __init__(self, nodes: List[HelperNode]) -> None:
        self.nodes = nodes
        return

    @classmethod
    def spawn(cls, size: int) -> "HelperCluster":
        nodes: List[HelperNode] = []
        try:
            for index in range(size):
                node_id = "node{}".format(index)
                process = subprocess.Popen(
                    [sys.executable, HELPER_SCRIPT, node_id],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                )
                port = _read_port(process, node_id)
                nodes.append(HelperNode(node_id, process, port))
        except BaseException:
            for node in nodes:
                node.kill()
            raise
        rtnval = cls(nodes)
        return rtnval

    def call_all(self, op: str, **fields: Any) -> List[Dict[str, Any]]:
        rtnval = [node.call(op, **fields) for node in self.nodes]
        return rtnval

    def shutdown(self) -> None:
        for node in self.nodes:
            node.shutdown()
        return


def _read_port(process: subprocess.Popen, node_id: str) -> int:
    deadline = time.time() + PORT_ANNOUNCE_TIMEOUT
    while time.time() < deadline:
        line = process.stdout.readline()
        if line.startswith("PORT "):
            rtnval = int(line.split()[1])
            return rtnval
        if process.poll() is not None:
            break
    raise RuntimeError("helper {} did not announce a port; stderr:\n{}".format(
        node_id, process.stderr.read()))


@testbase.register.resource_factory()
def create_helper_cluster(constraints: Optional[Dict[str, Any]] = None
                          ) -> Generator[HelperCluster, None, None]:
    """
        Spawn a cluster of helper processes and tear it down afterwards.

        :param constraints: Optional ``{"size": n}``.
    """
    size = (constraints or {}).get("size", DEFAULT_CLUSTER_SIZE)
    cluster = HelperCluster.spawn(size)
    try:
        yield cluster
    finally:
        cluster.shutdown()
