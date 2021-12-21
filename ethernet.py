import abc
from typing import Optional, Tuple
import struct
import codecs

import consts
from protocol import Protocol
from stack import NetworkAdapterInterface
from ip_utils import IPAddress
from packet import Packet


class MacResolverInterface(abc.ABC):
    """
    mac resolver for ethernet protocol
    can be for example arp for ipv4 or Neighbor Solicitation for ipv6
    """
    async def get_mac(self, adapter: NetworkAdapterInterface, dst_ip: IPAddress) -> str:
        """
        find the mac for the given ip
        """
        pass


class Ethernet(Protocol):
    MAC_LENGTH = 6
    _PROTOCOL_ID_STRUCT = struct.Struct('>H')

    def __init__(self):
        self._mac_resolver = None  # type: Optional[MacResolverInterface]

    def set_mac_resolver(self, mac_resolver: MacResolverInterface):
        self._mac_resolver = mac_resolver

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
            dst_ip = options.get('gateway')
            if dst_ip is None:
                dst_ip = options.get('dst_ip')
            assert dst_ip, 'destination ip or mac must be set'
            dst_mac = await self._mac_resolver.get_mac(adapter, dst_ip)

        dst_mac = self.build_mac(dst_mac)
        previous_protocol_id = options.get('previous_protocol_id')
        assert previous_protocol_id, "Ethernet can't be top protocol"
        src_mac = self.build_mac(adapter.mac)
        ethernet_header = dst_mac + src_mac + self._PROTOCOL_ID_STRUCT.pack(previous_protocol_id)
        return ethernet_header + packet

    async def handle(self, packet: Packet, adapter: NetworkAdapterInterface) \
            -> Optional[Tuple[bytes, int]]:
        data = packet.current_packet
        dst_mac = self.parse_mac(data[:self.MAC_LENGTH])

        if not self.relevant_mac(adapter, dst_mac):
            return None

        src_mac = self.parse_mac(data[self.MAC_LENGTH:self.MAC_LENGTH*2])
        protocol_id_start = 2 * self.MAC_LENGTH
        protocol_id_bytes = data[protocol_id_start:protocol_id_start + self._PROTOCOL_ID_STRUCT.size]
        protocol_id, = self._PROTOCOL_ID_STRUCT.unpack(protocol_id_bytes)

        size = protocol_id_start + self._PROTOCOL_ID_STRUCT.size
        packet.add_layer('ethernet', {'dst': dst_mac, 'src': src_mac}, size)
        return protocol_id

    @staticmethod
    def relevant_mac(adapter: NetworkAdapterInterface, mac: str):
        """
        Returns true if the a packet with the given mac as destination mac is relevant to the given adapter
        """
        return mac == adapter.mac or mac == consts.BROADCAST_MAC
