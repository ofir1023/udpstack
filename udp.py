from typing import Optional, Tuple
import struct
from io import BytesIO

from ip_utils import IPAddress
from stack import NetworkAdapterInterface
from protocol import Protocol
from ipv4 import IPv4
from utils import calculate_checksum


class UDP(Protocol):
    NEXT_PROTOCOL = IPv4
    PROTOCOL_ID = 0x11
    PROTOCOL_STRUCT = struct.Struct('>HHHH')
    PSEUDO_HEADER_STRUCT = struct.Struct('>IIBBHHHHH')

    def __init__(self):
        self.queue = {}

    async def build(self, adapter: NetworkAdapterInterface, packet: bytes, options) -> bytes:
        pseudo_header = self.PSEUDO_HEADER_STRUCT.pack(
            int(adapter.ip), int(IPAddress(options['dst_ip'])), 0, self.PROTOCOL_ID,
            self.PROTOCOL_STRUCT.size + len(packet), options['src_port'], options['dst_port'],
            self.PROTOCOL_STRUCT.size + len(packet), 0)
        udp_header = self.PROTOCOL_STRUCT.pack(
            options['src_port'], options['dst_port'], len(packet), 
            calculate_checksum(pseudo_header + packet))
        return udp_header + packet

    async def handle(self, packet: bytes, adapter: NetworkAdapterInterface, packet_description: dict) \
            -> Optional[Tuple[bytes, int]]:
        packet_io = BytesIO(packet)

        src_port, dst_port, length, checksum = self.PROTOCOL_STRUCT.unpack(packet_io.read(self.PROTOCOL_STRUCT.size))
        data = packet_io.read(length)

        pseudo_header = self.PSEUDO_HEADER_STRUCT.pack(
            int(IPAddress(packet_description['src_ip'])), int(IPAddress(packet_description['dst_ip'])), 
            0, self.PROTOCOL_ID, length, src_port, dst_port, length, 0)

        calculated_checksum = calculate_checksum(pseudo_header + data)
        if checksum != 0:
            assert checksum == calculated_checksum, "received checksum doesn't match calculated checksum"

        if dst_port in self.queue.keys():
            self.queue[dst_port].append(data)
        else:
            self.queue[dst_port] = [data]

        return None
