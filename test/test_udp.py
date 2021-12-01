from scapy.all import Ether, IP
from scapy.all import UDP as SCAPY_UDP
import pytest
import asyncio

from stack import stack
from udp import UDP
from network_adapter import MockNetworkAdapter
from ip_utils import IPAddress


TEST_DST_IP = IPAddress('1.1.1.1')
TEST_DST_MAC = 'aa:aa:aa:aa:aa:aa'
TEST_PREVIOUS_ID = 123
TEST_PAYLOAD = b'abcde'
TEST_SRC_PORT = 1234
TEST_DST_PORT = 1337


def assert_packet(packet: bytes, adapter: MockNetworkAdapter):
    packet = Ether(packet)
    assert packet.layers() == [Ether, IP, SCAPY_UDP]

    ether = packet.getlayer(Ether)
    assert ether.src == adapter.mac
    assert ether.dst == TEST_DST_MAC

    ip = packet.getlayer(IP)
    assert ip.src == adapter.ip
    assert ip.dst == TEST_DST_IP

    udp = packet.getlayer(SCAPY_UDP)
    assert udp.sport == TEST_SRC_PORT
    assert udp.dport == TEST_DST_PORT


def assert_received_packet(packet: bytes, adapter: MockNetworkAdapter):
    packet = Ether(packet)
    assert packet.layers() == [Ether, IP]

    ether = packet.getlayer(Ether)
    assert ether.src == TEST_DST_MAC
    assert ether.dst == adapter.mac

    ip = packet.getlayer(IP)
    assert ip.src == TEST_DST_IP
    assert ip.dst == adapter.ip


@pytest.mark.asyncio
async def test_send(adapter: MockNetworkAdapter):
    await stack.send(UDP, src_port=1234, dst_port=1337, dst_ip=TEST_DST_IP, dst_mac=TEST_DST_MAC)
    assert_packet(adapter.get_next_packet_nowait(), adapter)


@pytest.mark.asyncio
async def test_handle(adapter: MockNetworkAdapter):
    udp = SCAPY_UDP(sport=TEST_SRC_PORT, dport=TEST_DST_PORT)
    packet = udp / TEST_PAYLOAD
    udp_protocol = UDP()
    description = {'src_ip': adapter.ip, 'dst_ip': TEST_DST_IP}
    await udp_protocol.handle(packet.build(), adapter, description)
    assert TEST_DST_PORT in udp_protocol.queue.keys()
    assert udp_protocol.queue[TEST_DST_PORT] == TEST_PAYLOAD
