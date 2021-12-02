from scapy.all import Ether, IP, Padding
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
    await stack.send(UDP, src_port=TEST_SRC_PORT, dst_port=TEST_DST_PORT, 
    dst_ip=TEST_DST_IP, dst_mac=TEST_DST_MAC, data=TEST_PAYLOAD)
    assert_packet(adapter.get_next_packet_nowait(), adapter)


@pytest.mark.asyncio
async def test_handle(adapter: MockNetworkAdapter):
    udp = SCAPY_UDP(sport=TEST_SRC_PORT, dport=TEST_DST_PORT)
    packet = udp / TEST_PAYLOAD
    description = {'src_ip': adapter.ip, 'dst_ip': TEST_DST_IP}

    stack.get_protocol(UDP).open_port(TEST_DST_PORT)
    await stack.get_protocol(UDP).handle(packet.build(), adapter, description)
    assert await stack.get_protocol(UDP).get_packet(TEST_DST_PORT) == (str(adapter.ip), TEST_SRC_PORT, TEST_PAYLOAD)
    stack.get_protocol(UDP).close_port(TEST_DST_PORT)
