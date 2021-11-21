import abc
from typing import Optional, Tuple
import struct
import codecs

import consts
from protocol import Protocol
from stack import NetworkAdapterInterface, ProtocolInterface


class MacResolverInterface(abc.ABC):
    """
    mac resolver for ethernet protocol
    can be for example arp for ipv4 or Neighbor Solicitation for ipv6
    """
    async def get_mac(self, adapter: NetworkAdapterInterface, dst_ip: str) -> str:
        """
        find the mac for the given ip
        """
        pass


class Ethernet(Protocol):
    _mac_resolver = None  # type: Optional[MacResolverInterface]
    MAC_LENGTH = 6
    _PROTOCOL_ID_STRUCT = struct.Struct('>H')

    @classmethod
    def set_mac_resolver(cls, mac_resolver: MacResolverInterface):
        cls._mac_resolver = mac_resolver

    @staticmethod
    def build_mac(mac: str) -> bytes:
        parts = mac.split(':')
        assert len(parts) == Ethernet.MAC_LENGTH, 'bad format mac'
        return b''.join(codecs.decode(part, 'hex') for part in parts)

    @staticmethod
    def parse_mac(mac: bytes) -> str:
        return ':'.join(hex(part)[2:].zfill(2) for part in mac)

    async def build(self, adapter: NetworkAdapterInterface, packet: bytes,  options) -> bytes:
        dst_mac = options.get('dst_mac')
        if dst_mac is None:
            assert self._mac_resolver is not None, 'mac resolver is not set and got a packet without destination mac'
            dst_ip = options.get('dst_ip')
            assert dst_ip, 'destination ip or mac must be set'
            dst_mac = await self._mac_resolver.get_mac(adapter, dst_ip)

        dst_mac = self.build_mac(dst_mac)
        previous_protocol_id = options.get('previous_protocol_id')
        assert previous_protocol_id, "Ethernet can't be top protocol"
        src_mac = self.build_mac(adapter.mac)
        ethernet_header = dst_mac + src_mac + self._PROTOCOL_ID_STRUCT.pack(previous_protocol_id)
        return ethernet_header + packet

    async def handle(self, packet: bytes, adapter: NetworkAdapterInterface, packet_description: dict) \
            -> Optional[Tuple[bytes, int]]:
        dst_mac = self.parse_mac(packet[:self.MAC_LENGTH])
        if not self.relevant_mac(adapter, dst_mac):
            return None
        src_mac = self.parse_mac(packet[self.MAC_LENGTH:self.MAC_LENGTH*2])

        packet_description['dst_mac'] = dst_mac
        packet_description['src_mac'] = src_mac

        protocol_id_start = 2 * self.MAC_LENGTH
        protocol_id_bytes = packet[protocol_id_start:protocol_id_start + self._PROTOCOL_ID_STRUCT.size]
        protocol_id, = self._PROTOCOL_ID_STRUCT.unpack(protocol_id_bytes)
        return packet[protocol_id_start + self._PROTOCOL_ID_STRUCT.size:], protocol_id

    @staticmethod
    def relevant_mac(adapter: NetworkAdapterInterface, mac: str):
        return mac == adapter.mac or mac == consts.BROADCAST_MAC
