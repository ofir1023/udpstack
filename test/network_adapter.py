from stack import NetworkAdapterInterface
from ip_utils import IPAddress
import asyncio
from typing import Optional


class MockNetworkAdapter(NetworkAdapterInterface):
    def __init__(self):
        self.sent_packets = asyncio.Queue()

    @property
    def mac(self) -> str:
        return '01:23:45:67:89:ab'

    @property
    def ip(self) -> IPAddress:
        return IPAddress('1.2.3.4')

    @property
    def netmask(self) -> IPAddress:
        # everything goes through this adapter
        return IPAddress('0.0.0.0')

    @property
    def gateway(self) -> Optional[IPAddress]:
        return None

    async def send(self, packet: bytes):
        await self.sent_packets.put(packet)

    async def get_next_packet(self):
        return await self.sent_packets.get()

    def get_next_packet_nowait(self):
        return self.sent_packets.get_nowait()
