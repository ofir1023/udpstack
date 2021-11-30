from scapy.all import Ether, ICMP as SCAPY_ICMP, Raw, IP, IPerror
import pytest

from network_adapter import MockNetworkAdapter
from stack import stack
from icmp import ICMP, ICMPCodes
from ip_utils import IPAddress
from arp import ARP


TEST_DST_IP = IPAddress('1.1.1.1')
TEST_DST_MAC = 'aa:aa:aa:aa:aa:aa'
PAYLOAD = b'test!'
UNREACHABLE_CODE = 0xaa


def assert_ttl_exceeded(packet: Ether):
    icmp = packet.getlayer(SCAPY_ICMP)
    assert icmp.type == ICMPCodes.TTL_EXCEEDED.value
    assert icmp.code == 0


@pytest.mark.asyncio
async def test_ttl_exceeded_sanity(adapter: MockNetworkAdapter):
    await stack.send(ICMP, dst_ip=TEST_DST_IP, dst_mac=TEST_DST_MAC, icmp_type=ICMPCodes.TTL_EXCEEDED,
                     error_packet=PAYLOAD)
    packet = Ether(adapter.get_next_packet_nowait())
    assert_ttl_exceeded(packet)
    assert packet.getlayer(Raw).load == PAYLOAD


@pytest.mark.asyncio
async def test_ttl_exceeded(adapter: MockNetworkAdapter):
    stack.get_protocol(ARP).add_arp_entry(adapter, TEST_DST_IP, TEST_DST_MAC)

    ether = Ether(src=TEST_DST_MAC, dst=adapter.mac)
    ip = IP(src=str(TEST_DST_IP), dst=str(adapter.ip), ttl=0)
    full_packet = ether / ip
    stack.add_packet(full_packet.build(), adapter)

    ttl_exceeded = Ether(await adapter.get_next_packet())
    assert ttl_exceeded.getlayer(IP).dst == TEST_DST_IP
    assert_ttl_exceeded(ttl_exceeded)

    iperror = ttl_exceeded.getlayer(IPerror)
    assert iperror.src == str(TEST_DST_IP)
    assert iperror.dst == str(adapter.ip)


@pytest.mark.asyncio
async def test_port_unreachable(adapter: MockNetworkAdapter):
    await stack.send(ICMP, dst_ip=TEST_DST_IP, dst_mac=TEST_DST_MAC, icmp_type=ICMPCodes.DESTINATION_UNREACHABLE,
                     unreachable_code=UNREACHABLE_CODE, error_packet=PAYLOAD)
    packet = Ether(adapter.get_next_packet_nowait())
    icmp = packet.getlayer(SCAPY_ICMP)
    assert icmp.type == ICMPCodes.DESTINATION_UNREACHABLE.value
    assert icmp.code == UNREACHABLE_CODE
    assert packet.getlayer(Raw).load == PAYLOAD
