from scapy.all import Ether
import pytest

from stack import stack, NetworkAdapterInterface
from ethernet import Ethernet, MacResolverInterface
from network_adapter import MockNetworkAdapter
from ip_utils import IPAddress


TEST_DST_IP = IPAddress('1.1.1.1')
TEST_DST_MAC = 'aa:aa:aa:aa:aa:aa'
TEST_PREVIOUS_ID = 0x2000


class MockMacResolver(MacResolverInterface):
    async def get_mac(self, adapter: NetworkAdapterInterface, dst_ip: IPAddress) -> str:
        assert dst_ip == TEST_DST_IP
        return TEST_DST_MAC


def assert_ether_packet(adapter: MockNetworkAdapter):
    packet = Ether(adapter.get_next_packet_nowait())
    assert packet.layers() == [Ether]
    assert packet.src == adapter.mac
    assert packet.dst == TEST_DST_MAC
    assert packet.type == TEST_PREVIOUS_ID


@pytest.mark.asyncio
async def test_build(adapter):
    await stack.send(Ethernet, previous_protocol_id=TEST_PREVIOUS_ID, dst_mac=TEST_DST_MAC, dst_ip=TEST_DST_IP)
    assert_ether_packet(adapter)


@pytest.mark.asyncio
async def test_handle(adapter):
    packet = Ether(src=TEST_DST_MAC, dst=adapter.mac, type=TEST_PREVIOUS_ID)
    description = {}
    rest_of_packet, prev_id = await Ethernet().handle(packet.build(), adapter, description)
    assert description['src_mac'] == TEST_DST_MAC
    assert description['dst_mac'] == adapter.mac
    assert rest_of_packet == b''
    assert prev_id == TEST_PREVIOUS_ID


@pytest.mark.asyncio
async def test_bad_mac(adapter):
    packet = Ether(src=TEST_DST_MAC, dst=TEST_DST_MAC, type=TEST_PREVIOUS_ID)
    assert await Ethernet().handle(packet.build(), adapter, {}) is None


@pytest.mark.asyncio
async def test_mac_resolver(adapter):
    stack.get_protocol(Ethernet).set_mac_resolver(MockMacResolver())
    await stack.send(Ethernet, previous_protocol_id=TEST_PREVIOUS_ID, dst_ip=TEST_DST_IP)
    assert_ether_packet(adapter)
