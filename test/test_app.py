import pytest
from adapter import SnifferNetworkAdapter
from stack import stack
from udp_socket import UDPSocket
import arp
from ip_utils import IPAddress
from conftest import sniffer_adapter

TEST_DST_IP = IPAddress('1.1.1.2')
TEST_DST_MAC = 'aa:aa:aa:aa:aa:aa'
TEST_PREVIOUS_ID = 123
TEST_PAYLOAD = b'abcde'
TEST_SRC_PORT = 1337
TEST_DST_PORT = 1234

@pytest.mark.asyncio
async def test_echo_server(sniffer_adapter: SnifferNetworkAdapter):
    sniffer_adapter.start()
    s = UDPSocket()
    s.bind(None, TEST_SRC_PORT)
    s.connect(str(TEST_DST_IP), TEST_DST_PORT)
    await s.send(TEST_PAYLOAD)
    data = await s.recv(len(TEST_PAYLOAD))
    assert data == TEST_PAYLOAD
    s.close()
