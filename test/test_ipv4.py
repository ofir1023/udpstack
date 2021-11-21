from scapy.all import Ether, IP
import pytest
import asyncio

from stack import stack
from ipv4 import IPv4
from ethernet import Ethernet
from network_adapter import MockNetworkAdapter
import consts

TEST_DST_IP = '1.1.1.1'
TEST_DST_MAC = 'aa:aa:aa:aa:aa:aa'

def assert_packet(packet: bytes, adapter: MockNetworkAdapter):
    packet = Ether(packet)
    assert packet.layers() == [Ether, IP]

    ether = packet.getlayer(Ether)
    assert ether.src == adapter.mac
    assert ether.dst == TEST_DST_MAC

    ip = packet.getlayer(IP)
    assert ip.src == adapter.ip
    assert ip.dst == TEST_DST_IP

@pytest.mark.asyncio
async def test_send(adapter: MockNetworkAdapter):
    await stack.send(IPv4, adapter, dst_ip=TEST_DST_IP, protocol=123, dst_mac=TEST_DST_MAC)
    assert_packet(adapter.get_next_packet_nowait(), adapter)