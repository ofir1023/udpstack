from stack import NetworkAdapterInterface
from protocol import Protocol
from ipv4 import IPv4, TTLExceededHandler
from utils import calculate_checksum
from typing import Optional, Tuple
from stack import stack
from packet import Packet

import struct
from enum import Enum


class ICMPCodes(Enum):
    DESTINATION_UNREACHABLE = 3
    TTL_EXCEEDED = 11


class ICMP(Protocol, TTLExceededHandler):
    NEXT_PROTOCOL = IPv4
    PROTOCOL_ID = 1

    HEADER_STRUCT = struct.Struct('BBH')

    ECHO_IDENTIFIER = 0x1337
    ECHO_DEFAULT_DATA = b'udpstack'
    ECHO_STRUCT = struct.Struct('>HH')

    ERROR_CODES = (ICMPCodes.DESTINATION_UNREACHABLE, ICMPCodes.TTL_EXCEEDED)

    def __init__(self):
        self._builders = {
            ICMPCodes.TTL_EXCEEDED: self._build_ttl_exceeded,
            ICMPCodes.DESTINATION_UNREACHABLE: self._build_icmp_destination_unreachable
        }
        stack.get_protocol(IPv4).register_to_ttl_exceeded_callback(self)

    async def handle_ttl_exceeded(self, packet: Packet):
        ip = packet.get_layer('ip')
        await stack.send(ICMP, dst_ip=ip.attributes['src'], icmp_type=ICMPCodes.TTL_EXCEEDED,
                         error_packet=ip.data + packet.current_packet)

    @staticmethod
    def _pack(type: ICMPCodes, code: int, data: bytes):
        no_checksum = ICMP.HEADER_STRUCT.pack(type.value, code, 0) + data
        checksum = calculate_checksum(no_checksum)
        return ICMP.HEADER_STRUCT.pack(type.value, code, checksum) + data

    @staticmethod
    def _build_error_packet(options: dict):
        return struct.pack('I', 0) + options['error_packet']

    @staticmethod
    def _build_ttl_exceeded(options: dict):
        return ICMP._pack(ICMPCodes.TTL_EXCEEDED, 0, ICMP._build_error_packet(options))

    @staticmethod
    def _build_icmp_destination_unreachable(options: dict):
        return ICMP._pack(ICMPCodes.DESTINATION_UNREACHABLE, options['unreachable_code'],
                          ICMP._build_error_packet(options))

    async def build(self, adapter: NetworkAdapterInterface, packet: bytes, options: dict) -> bytes:
        builder = self._builders[options['icmp_type']]
        return packet + builder(options)

    async def handle(self, packet: Packet, adapter: NetworkAdapterInterface) -> Optional[int]:
        # nothing to do with incoming icmp packet
        pass
