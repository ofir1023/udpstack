from scapy.all import Ether, IP, Raw,  ICMP, IPerror, UDPerror
from scapy.all import UDP as SCAPY_UDP
import pytest

from stack import stack
from udp import UDP
from network_adapter import MockNetworkAdapter
from ip_utils import IPAddress
from icmp import ICMPCodes
from arp import ARP


TEST_DST_IP = IPAddress('1.1.1.1')
TEST_DST_MAC = 'aa:aa:aa:aa:aa:aa'
TEST_PREVIOUS_ID = 123
TEST_PAYLOAD = b'abcde'
TEST_SRC_PORT = 1234
TEST_DST_PORT = 1337


def assert_packet(packet: bytes, adapter: MockNetworkAdapter):
    packet = Ether(packet)
    assert packet.layers() == [Ether, IP, SCAPY_UDP, Raw]

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


def build_udp_packet(adapter: MockNetworkAdapter):
    ether = Ether(src=TEST_DST_MAC, dst=adapter.mac)
    ip = IP(src=TEST_DST_IP, dst=adapter.ip)
    udp = SCAPY_UDP(sport=TEST_SRC_PORT, dport=TEST_DST_PORT)
    packet = ether / ip / udp / TEST_PAYLOAD
    return packet.build()


@pytest.mark.asyncio
async def test_send(adapter: MockNetworkAdapter):
    await stack.send(UDP, src_port=TEST_SRC_PORT, dst_port=TEST_DST_PORT, dst_ip=TEST_DST_IP, dst_mac=TEST_DST_MAC,
                     data=TEST_PAYLOAD)
    assert_packet(adapter.get_next_packet_nowait(), adapter)


@pytest.mark.asyncio
async def test_handle(adapter: MockNetworkAdapter):
    stack.get_protocol(UDP).open_port(TEST_DST_PORT)
    stack.add_packet(build_udp_packet(adapter), adapter)

    assert await stack.get_protocol(UDP).get_packet(TEST_DST_PORT) == (str(TEST_DST_IP), TEST_SRC_PORT, TEST_PAYLOAD)
    stack.get_protocol(UDP).close_port(TEST_DST_PORT)


@pytest.mark.asyncio
async def test_send_to_closed_port(adapter: MockNetworkAdapter):
    stack.get_protocol(ARP).add_arp_entry(adapter, TEST_DST_IP, TEST_DST_MAC)

    stack.add_packet(build_udp_packet(adapter), adapter)
    packet = Ether(await adapter.get_next_packet())

    icmp = packet.getlayer(ICMP)
    assert icmp.type == ICMPCodes.DESTINATION_UNREACHABLE.value
    assert icmp.code == UDP.PORT_UNREACHABLE

    iperror = packet.getlayer(IPerror)
    assert iperror.src == str(TEST_DST_IP)
    assert iperror.dst == str(adapter.ip)

    udperror = packet.getlayer(UDPerror)
    assert udperror.sport == TEST_SRC_PORT
    assert udperror.dport == TEST_DST_PORT
