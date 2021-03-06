from typing import Optional, Tuple, List
import struct
from io import BytesIO
import abc

from ip_utils import IPAddress
from stack import NetworkAdapterInterface
from protocol import Protocol
from ethernet import Ethernet
from utils import calculate_checksum
from packet import Packet
from consts import IPV4_PROTOCOL_ID

# This will add arp to the stack
import arp


class TTLExceededHandler:
    @abc.abstractmethod
    async def handle_ttl_exceeded(self, packet: Packet):
        """
        this function will be called every time a ttl exceeded packet will arrive
        """
        pass


class IPv4(Protocol):
    NEXT_PROTOCOL = Ethernet
    PROTOCOL_ID = IPV4_PROTOCOL_ID
    VERSION = 4
    HEADER_LENGTH = 5
    TTL = 128
    PROTOCOL_STRUCT = struct.Struct('>BBHHHBBHII')
    DF_FLAG = 0x4000

    def __init__(self):
        self._ttl_exceeded_handlers = []  # type: List[TTLExceededHandler]

    def register_to_ttl_exceeded_callback(self, handler: TTLExceededHandler):
        self._ttl_exceeded_handlers.append(handler)

    async def build(self, adapter: NetworkAdapterInterface, packet: bytes, options) -> bytes:
        ip_header = self.PROTOCOL_STRUCT.pack(
            (self.VERSION << 4) + self.HEADER_LENGTH, 0, len(packet) + self.HEADER_LENGTH * 4, 
            0, 0, self.TTL, options['previous_protocol_id'], 0, int(adapter.ip),
            int(IPAddress(options['dst_ip'])))
        checksum = calculate_checksum(ip_header)
        ip_header = ip_header[:10] + struct.pack('>H', checksum) + ip_header[12:]  # insert real checksum
        return ip_header + packet

    async def handle(self, packet: Packet, adapter: NetworkAdapterInterface) -> Optional[int]:
        packet_io = BytesIO(packet.current_packet)
        header_data = packet_io.read(self.PROTOCOL_STRUCT.size)
        version_and_header_length, options, total_length, identification, flags_and_fragment_offset, ttl, protocol, header_checksum, src_ip, dst_ip = self.PROTOCOL_STRUCT.unpack(header_data)

        calculated_checksum = calculate_checksum(header_data[:10] + b'\x00' * 2 + header_data[12:])
        if header_checksum != calculated_checksum:
            return None

        # support only basic IP header, with no options or fragmentation
        if version_and_header_length != (self.VERSION << 4) + self.HEADER_LENGTH \
                or options != 0 \
                or (flags_and_fragment_offset != 0 and flags_and_fragment_offset != self.DF_FLAG):
            return None

        src_ip = IPAddress(src_ip)
        dst_ip = IPAddress(dst_ip)

        if dst_ip != adapter.ip:
            return None

        packet.add_layer('ip', {'src': src_ip, 'dst': dst_ip}, packet_io.tell())

        if ttl == 0:
            for handler in self._ttl_exceeded_handlers:
                await handler.handle_ttl_exceeded(packet)
            return None

        return protocol
