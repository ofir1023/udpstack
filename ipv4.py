from typing import Optional, Tuple, Type
import struct
from io import BytesIO
import ipaddress

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
    def encode_ip(ip: str) -> int:
        return int(ipaddress.IPv4Address(ip))

    @staticmethod
    def decode_ip(ip: int) -> str:
        return str(ipaddress.IPv4Address(ip))

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
            0, 0, self.TTL, options['protocol'], 0, IPv4.encode_ip(adapter.ip), IPv4.encode_ip(options['dst_ip']))
        checksum = IPv4.calculate_checksum(ip_header)
        ip_header = ip_header[:10] + struct.pack('>H', checksum) + ip_header[12:]  # insert real checksum
        return ip_header + packet

    async def handle(self, packet: bytes, adapter: NetworkAdapterInterface, packet_description: dict) \
            -> Optional[Tuple[bytes, int]]:
        packet_io = BytesIO(packet)
        header_data = packet_io.read(self.PROTOCOL_STRUCT.size)
        version_and_header_length, options, total_length, identification, flags_and_fragment_offset, ttl, protocol, header_checksum, src_ip, dst_ip = self.PROTOCOL_STRUCT.unpack(header_data)

        calculated_checksum = IPv4.calculate_checksum(header_data[:10] + b'\x00' * 2 + header_data[12:])
        assert header_checksum == calculated_checksum, "received checksum doesn't match calculated checksum"

        if version_and_header_length != 0x45 \
                or options != 0 \
                or flags_and_fragment_offset != 0:
            return None

        src_ip = IPv4.decode_ip(src_ip)
        dst_ip = IPv4.decode_ip(dst_ip)

        if dst_ip != adapter.ip:
            return None

        packet_description['src_ip'] = src_ip
        packet_description['dst_ip'] = dst_ip

        payload = packet_io.read(total_length - 20)
        return payload, protocol
