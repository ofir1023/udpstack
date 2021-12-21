import pytest
from os_utils.sniffer_adapter import SnifferNetworkAdapter
from udp_socket import UDPSocket
from ip_utils import IPAddress

TEST_DST_IP = IPAddress('1.1.1.2')
TEST_DST_MAC = 'aa:aa:aa:aa:aa:aa'
TEST_PREVIOUS_ID = 123
TEST_PAYLOAD = b'abcde'
TEST_SRC_PORT = 1337
TEST_DST_PORT = 1234


@pytest.mark.asyncio
async def test_echo_server(sniffer_adapter: SnifferNetworkAdapter):
    with UDPSocket() as s:
        s.bind(None, TEST_SRC_PORT)
        s.connect(str(TEST_DST_IP), TEST_DST_PORT)
        await s.send(TEST_PAYLOAD)
        data = await s.recv()
        assert data == TEST_PAYLOAD
