from scapy.all import Ether, IP
import pytest
import asyncio

from stack import stack
from ipv4 import IPv4, TTLExceededHandler
from network_adapter import MockNetworkAdapter
from ip_utils import IPAddress
from packet import Packet


TEST_DST_IP = IPAddress('1.1.1.1')
TEST_DST_MAC = 'aa:aa:aa:aa:aa:aa'
TEST_PREVIOUS_ID = 123
TEST_PAYLOAD = b'abcde'


def assert_packet(packet: bytes, adapter: MockNetworkAdapter):
    packet = Ether(packet)
    assert packet.layers() == [Ether, IP]

    ether = packet.getlayer(Ether)
    assert ether.src == adapter.mac
    assert ether.dst == TEST_DST_MAC

    ip = packet.getlayer(IP)
    assert ip.src == adapter.ip
    assert ip.dst == TEST_DST_IP


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
    await stack.send(IPv4, dst_ip=TEST_DST_IP, previous_protocol_id=TEST_PREVIOUS_ID, dst_mac=TEST_DST_MAC)
    assert_packet(adapter.get_next_packet_nowait(), adapter)


@pytest.mark.asyncio
async def test_handle(adapter: MockNetworkAdapter):
    ip = IP(src=str(TEST_DST_IP), dst=str(adapter.ip), proto=TEST_PREVIOUS_ID)
    packet_layers = ip / TEST_PAYLOAD
    packet = Packet(packet_layers.build())

    prev_id = await IPv4().handle(packet, adapter)
    ip_layer = packet.get_layer('ip')
    assert ip_layer.attributes['src'] == TEST_DST_IP
    assert ip_layer.attributes['dst'] == adapter.ip
    assert packet.current_packet == TEST_PAYLOAD
    assert prev_id == TEST_PREVIOUS_ID


@pytest.mark.asyncio
async def test_ttl_exceeded(adapter: MockNetworkAdapter):
    class TTLExceededTestHandler(TTLExceededHandler):
        def __init__(self):
            self.event = asyncio.Event()
            self.packet = None

        async def handle_ttl_exceeded(self, packet: Packet):
            assert self.packet is None, 'handle should be called once'
            self.event.set()
            self.packet = packet

    handler = TTLExceededTestHandler()
    stack.get_protocol(IPv4).register_to_ttl_exceeded_callback(handler)

    ether = Ether(src=TEST_DST_MAC, dst=adapter.mac)
    ip = IP(src=str(TEST_DST_IP), dst=str(adapter.ip), ttl=0)
    full_packet = ether / ip
    stack.add_packet(full_packet.build(), adapter)

    await handler.event.wait()
    assert handler.packet is not None
    handler.packet.get_layer('ip')  # make sure layer exists, since the handler should be called after processing
    assert handler.packet.current_packet == b''
