from scapy.all import Ether, ARP as SCAPY_ARP
import pytest
import asyncio

from stack import stack
from arp import ARP
from ethernet import Ethernet
from network_adapter import MockNetworkAdapter
import consts
from ip_utils import IPAddress


TEST_DST_IP = IPAddress('1.1.1.1')
TEST_DST_MAC = 'aa:aa:aa:aa:aa:aa'


def get_arp_packet(packet: bytes, adapter: MockNetworkAdapter):
    packet = Ether(packet)
    assert packet.layers() == [Ether, SCAPY_ARP]

    # general checks about the arp
    arp = packet.getlayer(SCAPY_ARP)
    assert arp.hwsrc == adapter.mac
    assert arp.psrc == adapter.ip
    assert arp.pdst == TEST_DST_IP

    return packet


def assert_request_packet(packet: bytes, adapter: MockNetworkAdapter):
    packet = get_arp_packet(packet, adapter)

    ether = packet.getlayer(Ether)
    assert ether.dst == 'ff:ff:ff:ff:ff:ff'

    arp = packet.getlayer(SCAPY_ARP)
    assert arp.op == ARP.REQUEST_OPCODE
    assert arp.hwdst == 'ff:ff:ff:ff:ff:ff'


def assert_reply_packet(packet: bytes, adapter: MockNetworkAdapter):
    packet = get_arp_packet(packet, adapter)

    ether = packet.getlayer(Ether)
    assert ether.dst == TEST_DST_MAC

    arp = packet.getlayer(SCAPY_ARP)
    assert arp.op == ARP.REPLY_OPCODE
    assert arp.hwdst == TEST_DST_MAC


def send_arp_request(adapter):
    arp = SCAPY_ARP(hwsrc=TEST_DST_MAC, hwdst=consts.BROADCAST_MAC, psrc=TEST_DST_IP, pdst=adapter.ip, op='who-has')
    ether = Ether(src=TEST_DST_MAC, dst=consts.BROADCAST_MAC)
    packet = ether / arp

    stack.add_packet(packet.build(), adapter)


def send_arp_reply(adapter):
    arp = SCAPY_ARP(hwsrc=TEST_DST_MAC, hwdst=adapter.mac, psrc=TEST_DST_IP, pdst=adapter.ip, op='is-at')
    ether = Ether(src=TEST_DST_MAC, dst=adapter.mac)
    packet = ether / arp

    stack.add_packet(packet.build(), adapter)


@pytest.mark.asyncio
async def test_send_request(adapter: MockNetworkAdapter):
    await stack.send(ARP, arp_opcode=ARP.REQUEST_OPCODE, dst_ip=TEST_DST_IP)
    assert_request_packet(adapter.get_next_packet_nowait(), adapter)


@pytest.mark.asyncio
async def test_send_reply(adapter: MockNetworkAdapter):
    await stack.send(ARP, arp_opcode=ARP.REPLY_OPCODE, dst_ip=TEST_DST_IP, dst_mac=TEST_DST_MAC)
    assert_reply_packet(adapter.get_next_packet_nowait(), adapter)


@pytest.mark.asyncio
async def test_handle_request(adapter: MockNetworkAdapter):
    send_arp_request(adapter)
    # this should generate arp reply (but we should wait for it since it happens async)
    assert_reply_packet(await adapter.get_next_packet(), adapter)


@pytest.mark.asyncio
async def test_handle_reply(adapter: MockNetworkAdapter):
    send_arp_reply(adapter)
    # make sure it saved the mac
    assert await Ethernet._mac_resolver.get_mac(adapter, TEST_DST_IP) == TEST_DST_MAC


@pytest.mark.asyncio
async def test_natural_mac_resolving(adapter: MockNetworkAdapter):
    # this will cause a arp resolving
    asyncio.create_task(stack.send(Ethernet, dst_ip=TEST_DST_IP, previous_protocol_id=0x2000))

    # wait for arp request
    assert_request_packet(await adapter.get_next_packet(), adapter)

    send_arp_reply(adapter)

    # wait for real packet
    packet = Ether(await adapter.get_next_packet())
    assert packet.dst == TEST_DST_MAC
