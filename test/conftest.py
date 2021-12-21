import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.dirname(__file__))

import pytest
from test.network_adapter import MockNetworkAdapter
from stack import stack
from adapter import SnifferNetworkAdapter
from os_utils.udp_echo_server import UDPEchoServer
from ip_utils import IPAddress

ADAPTER_NAME = 'test_adapter'
ADAPTER_MAC = 'aa:bb:cc:dd:ee:ff'
SERVER_IP = '1.1.1.2'
SERVER_PORT = 1234
ADAPTER_MTU = 1514
ADAPTER_IP = '1.1.1.1'
ADAPTER_GATEWAY = '1.1.1.254'
ADAPTER_NETMASK = '255.255.255.0'


@pytest.fixture(autouse=True)
def adapter():
    adapter = MockNetworkAdapter()
    stack.add_adapter(adapter)
    yield adapter
    stack.remove_adapter(adapter)

@pytest.fixture
@pytest.mark.asyncio
def sniffer_adapter():    
    with UDPEchoServer(ADAPTER_NAME, ADAPTER_MAC, SERVER_IP, SERVER_PORT) as udp_echo_server:
        adapter = SnifferNetworkAdapter(ADAPTER_NAME, ADAPTER_MAC, IPAddress(ADAPTER_IP), IPAddress(ADAPTER_NETMASK), 
            IPAddress(ADAPTER_GATEWAY), ADAPTER_MTU)
        stack.add_adapter(adapter)
        yield adapter
        stack.remove_adapter(adapter)