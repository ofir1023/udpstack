from typing import Optional, Tuple, Type
import struct

from stack import NetworkAdapterInterface, ProtocolInterface
from protocol import Protocol
from ethernet import Ethernet, MacResolverInterface


class IPv4(Protocol):
    NEXT_PROTOCOL = Ethernet
    PROTOCOL_ID = 0x800
    VERSION = 4
    HEADER_LENGTH = 5
    TTL = 128
    PROTOCOL_STRUCT = struct.Struct('>BBHHHBBHII')

    ADDRESS_LENGTH = 4

    @staticmethod
    def build_ip(ip: str) -> bytes:
        assert len(ip.split('.')) == IPv4.ADDRESS_LENGTH
        return bytes(map(int, ip.split('.')))

    @staticmethod
    def parse_ip(ip: bytes) -> str:
        return '.'.join(str(part) for part in ip)

    @staticmethod
    def calculate_checksum(header: bytes) -> bytes:
        s = 0
        for i in range(0, len(header), 2):
            w = header[i+1] + (header[i] << 8)
            c = s + w
            s = (c & 0xffff) + (c >> 16)
        return ~s & 0xffff


    async def build(self, adapter: NetworkAdapterInterface, packet: bytes, options) -> bytes:
        ip_header = self.PROTOCOL_STRUCT.pack(
            (self.VERSION << 4) + self.HEADER_LENGTH, 0, len(packet) + self.HEADER_LENGTH * 4, 
            0, 0, self.TTL, options['protocol'])
        ip_header += struct.pack('H', IPv4.calculate_checksum(ip_header))
        ip_header += IPv4.build_ip(adapter.ip)
        ip_header += IPv4.build_ip(options['dst_ip'])
        return ip_header + packet

    async def handle(self, packet: bytes, adapter: NetworkAdapterInterface, packet_description: dict) \
            -> Optional[Tuple[bytes, int]]:
        # TODO
        pass
