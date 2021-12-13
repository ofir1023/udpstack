from typing import Optional
import struct
from io import BytesIO

from stack import NetworkAdapterInterface, stack
from protocol import Protocol
from ethernet import Ethernet, MacResolverInterface
from ipv4 import IPv4
from arp_table import ARPTable
import consts
from ip_utils import IPAddress
from packet import Packet


class ARP(Protocol, MacResolverInterface):
    NEXT_PROTOCOL = Ethernet
    PROTOCOL_ID = 0x806

    REQUEST_OPCODE = 1
    REPLY_OPCODE = 2
    PROTOCOL_STRUCT = struct.Struct('>HHBBH')
    ETHERNET_ID = 1

    def __init__(self):
        self._arp_tables = {}
        stack.get_protocol(Ethernet).set_mac_resolver(self)

    async def build(self, adapter: NetworkAdapterInterface, packet: bytes, options) -> bytes:
        assert packet == b'', 'packet given to arp layer should be empty'

        arp_opcode = options['arp_opcode']
        dst_ip = IPAddress(options['dst_ip'])
        if arp_opcode == self.REPLY_OPCODE:
            dst_mac = options.get('dst_mac')
            if dst_mac is None:
                dst_mac = await self.get_mac(adapter, dst_ip)
        else:
            dst_mac = consts.BROADCAST_MAC
        options['dst_mac'] = dst_mac  # hint for ethernet layer

        packet += self.PROTOCOL_STRUCT.pack(self.ETHERNET_ID, IPv4.PROTOCOL_ID, Ethernet.MAC_LENGTH,
                                            IPAddress.ADDRESS_LENGTH, arp_opcode)
        packet += Ethernet.build_mac(adapter.mac)
        packet += bytes(adapter.ip)
        packet += Ethernet.build_mac(dst_mac)
        packet += bytes(dst_ip)

        return packet

    async def handle(self, packet: Packet, adapter: NetworkAdapterInterface) -> Optional[int]:
        packet_io = BytesIO(packet.current_packet)
        header = self.PROTOCOL_STRUCT.unpack(packet_io.read(self.PROTOCOL_STRUCT.size))
        ethernet_id, ipv4_id, mac_length, ip_length, opcode = header
        if ethernet_id != self.ETHERNET_ID \
                or ipv4_id != IPv4.PROTOCOL_ID \
                or mac_length != Ethernet.MAC_LENGTH \
                or ip_length != IPAddress.ADDRESS_LENGTH:
            return None

        src_mac = Ethernet.parse_mac(packet_io.read(Ethernet.MAC_LENGTH))
        src_ip = IPAddress(packet_io.read(IPAddress.ADDRESS_LENGTH))
        dst_mac = Ethernet.parse_mac(packet_io.read(Ethernet.MAC_LENGTH))
        dst_ip = IPAddress(packet_io.read(IPAddress.ADDRESS_LENGTH))

        if dst_ip != adapter.ip or not Ethernet.relevant_mac(adapter, dst_mac):
            return None

        self.add_arp_entry(adapter, src_ip, src_mac)

        if opcode == self.REQUEST_OPCODE:
            await stack.send(ARP, expected_adapter=adapter, arp_opcode=self.REPLY_OPCODE, dst_ip=src_ip)

    def _get_arp_table(self, adapter: NetworkAdapterInterface):
        return self._arp_tables.setdefault(adapter, ARPTable())

    def add_arp_entry(self, adapter: NetworkAdapterInterface, src_ip: IPAddress, src_mac: str):
        self._arp_tables.setdefault(adapter, ARPTable()).update(src_ip, src_mac)

    async def get_mac(self, adapter: NetworkAdapterInterface, dst_ip: IPAddress) -> str:
        arp_table = self._get_arp_table(adapter)
        result = arp_table.get_mac(dst_ip)
        if isinstance(result, str):
            # we already have the mac
            return result

        # we got a coroutine, which means there's no available mac for this ip. send arp request and wait for the result
        await stack.send(ARP, arp_opcode=self.REQUEST_OPCODE, dst_ip=dst_ip, expected_adapter=adapter)
        return await result
