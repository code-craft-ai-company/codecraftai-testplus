"""
    .. module:: _helpernode
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: A helper process that stands in for one remote node.

    Run as a script with a node id.  Listens on an ephemeral 127.0.0.1 port,
    announces ``PORT <n>`` on stdout, then serves small request dicts until
    told to shut down.  Standard library only, so it needs nothing the
    testplus package does not already have.

    Each accepted connection is served on its own thread and the listen
    backlog is generous: the scenarios deliberately hit a node with many
    concurrent callers and with a slow request while others are in flight,
    and a single-threaded accept loop with the default backlog of 1 makes
    the kernel drop SYNs, which the clients then retry with exponential
    back-off -- a minutes-long stall that looks like a hang.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import os
import sys
import threading
import time

from multiprocessing.connection import Listener

AUTHKEY = b"ccai-testplus-helper"
BACKLOG = 64


def _handle(conn, node_id: str, stop: threading.Event) -> None:
    try:
        request = conn.recv()
        op = request.get("op")
        if op == "ping":
            conn.send({"ok": True, "node": node_id, "pid": os.getpid()})
        elif op == "echo":
            conn.send({"ok": True, "node": node_id, "payload": request.get("payload")})
        elif op == "sleep":
            time.sleep(float(request.get("seconds", 0.0)))
            conn.send({"ok": True, "node": node_id})
        elif op == "shutdown":
            conn.send({"ok": True, "node": node_id})
            stop.set()
        else:
            conn.send({"ok": False, "node": node_id, "error": "unknown op {!r}".format(op)})
    except EOFError:
        pass
    finally:
        conn.close()
    return


def serve(node_id: str) -> int:
    listener = Listener(("127.0.0.1", 0), backlog=BACKLOG, authkey=AUTHKEY)
    sys.stdout.write("PORT {}\n".format(listener.address[1]))
    sys.stdout.flush()

    stop = threading.Event()
    while not stop.is_set():
        try:
            conn = listener.accept()
        except OSError:
            break
        threading.Thread(target=_handle, args=(conn, node_id, stop), daemon=True).start()

    listener.close()
    return 0


if __name__ == "__main__":
    sys.exit(serve(sys.argv[1] if len(sys.argv) > 1 else "node"))
