

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []



from typing import Generator

from ccai import testplus

from ccai.landscaping.landscape import Landscape
from ccai.landscaping.includefilters import IncludeDeviceByDeviceType

from ccai.landscaping.clients.linux.linuxclient import LinuxClient

@testplus.register.resource_factory()
def each_client(lscape: Landscape, constraints={}) -> Generator[LinuxClient, None, None]:
    
    includes = [IncludeDeviceByDeviceType("network/client-linux")]

    client_list = lscape.get_devices(include_filters=includes)

    for client in client_list:
        yield client


@testplus.attach.parameter(each_client, identifier="client")
def test_ssh_say_hello(client: LinuxClient):

    cmd = "echo 'Hello'"

    status, stdout, stderr = client.ssh.run_cmd(cmd)
    testplus.assert_equal(stdout.strip(), "Hello")

    return
