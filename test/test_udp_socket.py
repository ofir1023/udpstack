from scapy.all import Ether, IP, Padding
from scapy.all import UDP as SCAPY_UDP
import pytest
import asyncio

from stack import stack, NetworkAdapterInterface
from udp import UDP
from ethernet import Ethernet, MacResolverInterface
from udp_socket import UDPSocket
from network_adapter import MockNetworkAdapter
from ip_utils import IPAddress


TEST_DST_IP = IPAddress('1.1.1.1')
TEST_DST_MAC = 'aa:aa:aa:aa:aa:aa'
TEST_PREVIOUS_ID = 123
TEST_PAYLOAD = b'abcde'
TEST_SRC_PORT = 1234
TEST_DST_PORT = 1337


class MockMacResolver(MacResolverInterface):
    async def get_mac(self, adapter: NetworkAdapterInterface, dst_ip: IPAddress) -> str:
        assert dst_ip == TEST_DST_IP
        return TEST_DST_MAC

def assert_packet(packet: bytes, adapter: MockNetworkAdapter):
    packet = Ether(packet)
    assert packet.layers() == [Ether, IP, SCAPY_UDP, Padding]

    ether = packet.getlayer(Ether)
    assert ether.src == adapter.mac
    assert ether.dst == TEST_DST_MAC

    ip = packet.getlayer(IP)
    assert ip.src == adapter.ip
    assert ip.dst == TEST_DST_IP

    udp = packet.getlayer(SCAPY_UDP)
    assert udp.sport == TEST_SRC_PORT
    assert udp.dport == TEST_DST_PORT
    assert udp.payload.load == TEST_PAYLOAD


@pytest.mark.asyncio
async def test_send(adapter: MockNetworkAdapter):
    stack.get_protocol(Ethernet).set_mac_resolver(MockMacResolver())
    s = UDPSocket()
    s.bind(TEST_SRC_PORT)
    s.connect(TEST_DST_IP, TEST_DST_PORT)
    await s.send(TEST_PAYLOAD)
    assert_packet(adapter.get_next_packet_nowait(), adapter)


@pytest.mark.asyncio
async def test_handle(adapter: MockNetworkAdapter):
    s = UDPSocket()
    s.bind(TEST_DST_PORT)

    udp = SCAPY_UDP(sport=TEST_SRC_PORT, dport=TEST_DST_PORT)
    packet = udp / TEST_PAYLOAD
    description = {'src_ip': adapter.ip, 'dst_ip': TEST_DST_IP}
    await stack.get_protocol(UDP).handle(packet.build(), adapter, description)

    assert await s.recv(len(TEST_PAYLOAD)) == TEST_PAYLOAD
    s.close()

@pytest.mark.asyncio
async def test_two_binds(adapter: MockNetworkAdapter):
    s1 = UDPSocket()
    s1.bind(TEST_DST_PORT)

    s2 = UDPSocket()
    try:
        s2.bind(TEST_DST_PORT)
        assert False, "an exception should have been thrown"
    except:
        pass


@pytest.mark.asyncio
async def test_send_without_connect(adapter: MockNetworkAdapter):
    stack.get_protocol(Ethernet).set_mac_resolver(MockMacResolver())
    s = UDPSocket()
    try:
        s.send(TEST_PAYLOAD)
        assert False, "an exception should have been thrown"
    except:
        pass

@pytest.mark.asyncio
async def test_send_without_bind(adapter: MockNetworkAdapter):
    stack.get_protocol(Ethernet).set_mac_resolver(MockMacResolver())
    s = UDPSocket()
    s.connect(TEST_DST_IP, TEST_DST_PORT)
    await s.send(TEST_PAYLOAD)
    assert s.src_port is not None, "socket should be bound now"
    s.close()

@pytest.mark.asyncio
async def test_recv_without_bind(adapter: MockNetworkAdapter):
    s = UDPSocket()
    try:
        s.recv(len(TEST_PAYLOAD))
        assert False, "an exception should have been thrown"
    except:
        pass

@pytest.mark.asyncio
async def test_enter_and_exit(adapter: MockNetworkAdapter):
    stack.get_protocol(Ethernet).set_mac_resolver(MockMacResolver())
    with UDPSocket() as s: 
        s.bind(TEST_SRC_PORT)
        s.connect(TEST_DST_IP, TEST_DST_PORT)
        await s.send(TEST_PAYLOAD)
        assert_packet(adapter.get_next_packet_nowait(), adapter)
    assert s.src_port is None, "socket should be unbound now"