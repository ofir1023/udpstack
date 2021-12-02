from typing import Optional, Tuple
import struct
from io import BytesIO

from ip_utils import IPAddress
from stack import NetworkAdapterInterface
from protocol import Protocol
from ipv4 import IPv4
from utils import calculate_checksum
from asyncio import Event

class PacketQueue:
    def __init__(self):
        self._queue = []
        self._event = Event()

    def pop(self):
        if len(self._queue) == 0:
            return None
        return self._queue.pop()

    async def wait_for_data(self):
        await self._event.wait()
        return self.pop()

    def append(self, data: bytes):
        self._queue.append(data)
        self._event.set()


class UDP(Protocol):
    NEXT_PROTOCOL = IPv4
    PROTOCOL_ID = 0x11
    PROTOCOL_STRUCT = struct.Struct('>HHHH')
    PSEUDO_HEADER_STRUCT = struct.Struct('>IIBBHHHHH')

    def __init__(self):
        self.queues = {}

    async def build(self, adapter: NetworkAdapterInterface, packet: bytes, options) -> bytes:
        # pseudo header for checksum
        pseudo_header = self.PSEUDO_HEADER_STRUCT.pack(
            int(adapter.ip), int(IPAddress(options['dst_ip'])), 0, self.PROTOCOL_ID,
            self.PROTOCOL_STRUCT.size + len(packet), options['src_port'], options['dst_port'],
            self.PROTOCOL_STRUCT.size + len(packet), 0)
        udp_header = self.PROTOCOL_STRUCT.pack(
            options['src_port'], options['dst_port'], len(packet), 
            calculate_checksum(pseudo_header + packet))
        return udp_header + options['data']

    async def handle(self, packet: bytes, adapter: NetworkAdapterInterface, packet_description: dict) \
            -> Optional[Tuple[bytes, int]]:
        packet_io = BytesIO(packet)

        src_port, dst_port, length, checksum = self.PROTOCOL_STRUCT.unpack(packet_io.read(self.PROTOCOL_STRUCT.size))
        data = packet_io.read(length)

        # pseudo header for checksum
        pseudo_header = self.PSEUDO_HEADER_STRUCT.pack(
            int(IPAddress(packet_description['src_ip'])), int(IPAddress(packet_description['dst_ip'])), 
            0, self.PROTOCOL_ID, length, src_port, dst_port, length, 0)

        if checksum != 0 and checksum != calculate_checksum(pseudo_header + data):
            return None

        if dst_port in self.queues.keys():
            self.queues[dst_port].append((str(packet_description['src_ip']), src_port, data))
        else:
            # TODO: icmp unreachable?
            return None

        return None

    def open_port(self, port: int):
        if port in self.queues.keys():
            return False

        self.queues[port] = PacketQueue()
        return True

    def close_port(self, port: int):
        self.queues.pop(port, None)

    async def get_packet(self, port: int):
        if port in self.queues.keys():
            data = self.queues[port].pop()
            if data is not None:
                return data

        return await self.queues[port].wait_for_data()