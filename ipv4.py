from typing import Optional, Tuple, Type
import struct

from stack import NetworkAdapterInterface, ProtocolInterface
from protocol import Protocol
from ethernet import Ethernet, MacResolverInterface


class IPv4(Protocol):
    NEXT_PROTOCOL = Ethernet
    PROTOCOL_ID = 0x800

    ADDRESS_LENGTH = 4

    @staticmethod
    def build_ip(ip: str) -> bytes:
        assert len(ip.split('.')) == IPv4.ADDRESS_LENGTH
        return bytes(map(int, ip.split('.')))

    @staticmethod
    def parse_ip(ip: bytes) -> str:
        return '.'.join(str(part) for part in ip)

    async def build(self, adapter: NetworkAdapterInterface, options) -> bytes:
        # TODO
        pass

    async def handle(self, packet: bytes, adapter: NetworkAdapterInterface, packet_description: dict) \
            -> Optional[Tuple[bytes, int]]:
        # TODO
        pass
