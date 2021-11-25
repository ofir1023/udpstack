from stack import NetworkAdapterInterface
from ip_utils import IPAddress
import asyncio


class MockNetworkAdapter(NetworkAdapterInterface):
    def __init__(self):
        self.sent_packets = asyncio.Queue()

    @property
    def mac(self) -> str:
        return '01:23:45:67:89:ab'

    @property
    def ip(self) -> IPAddress:
        return IPAddress('1.2.3.4')

    async def send(self, packet: bytes):
        await self.sent_packets.put(packet)

    async def get_next_packet(self):
        return await self.sent_packets.get()

    def get_next_packet_nowait(self):
        return self.sent_packets.get_nowait()
