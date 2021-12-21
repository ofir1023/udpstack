from typing import Optional, Tuple
import struct
from io import BytesIO
from asyncio import Event

from ip_utils import IPAddress
from stack import NetworkAdapterInterface, stack
from protocol import Protocol
from ipv4 import IPv4
from utils import calculate_checksum
from packet import Packet
from icmp import ICMP, ICMPCodes


class PortAlreadyOpenedException(Exception):
    pass


class PacketQueue:
    def __init__(self):
        self._queue = []
        self._event = Event()

    def pop(self):
        if len(self._queue) == 0:
            return None
        return self._queue.pop()

    async def wait_for_packet(self):
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
    PORT_UNREACHABLE = 3

    def __init__(self):
        self.queues = {}

    async def build(self, adapter: NetworkAdapterInterface, packet: bytes, options) -> bytes:
        # pseudo header for checksum
        pseudo_header = self.PSEUDO_HEADER_STRUCT.pack(
            int(adapter.ip), int(IPAddress(options['dst_ip'])), 0, self.PROTOCOL_ID,
            self.PROTOCOL_STRUCT.size + len(options['data']), options['src_port'], options['dst_port'],
            self.PROTOCOL_STRUCT.size + len(options['data']), 0)
        udp_header = self.PROTOCOL_STRUCT.pack(
            options['src_port'], options['dst_port'], self.PROTOCOL_STRUCT.size + len(options['data']), 
            calculate_checksum(pseudo_header + options['data']))
        return udp_header + options['data']

    async def handle(self, packet: Packet, adapter: NetworkAdapterInterface) -> Optional[int]:
        packet_io = BytesIO(packet.current_packet)

        src_port, dst_port, length, checksum = self.PROTOCOL_STRUCT.unpack(packet_io.read(self.PROTOCOL_STRUCT.size))
        data = packet_io.read(length)

        # pseudo header for checksum
        ip_layer = packet.get_layer('ip')
        pseudo_header = self.PSEUDO_HEADER_STRUCT.pack(
            int(ip_layer.attributes['src']), int(ip_layer.attributes['dst']),
            0, self.PROTOCOL_ID, length, src_port, dst_port, length, 0)

        if checksum != 0 and checksum != calculate_checksum(pseudo_header + data):
            return None

        if (str(ip_layer.attributes['dst']), dst_port) in self.queues.keys():
            self.queues[(str(ip_layer.attributes['dst']), dst_port)].append((str(ip_layer.attributes['src']), src_port, data))
        elif (None, dst_port) in self.queues.keys():
            self.queues[(None, dst_port)].append((str(ip_layer.attributes['src']), src_port, data))
        else:
            await stack.send(ICMP, dst_ip=ip_layer.attributes['src'], icmp_type=ICMPCodes.DESTINATION_UNREACHABLE,
                             unreachable_code=self.PORT_UNREACHABLE, error_packet=ip_layer.data + packet.current_packet)

        return None

    def open_port(self, ip: str, port: int):
        """
        Mark the (ip, port) as open and expects packets
        """
        if (None, port) in self.queues.keys() or (ip, port) in self.queues.keys():
            raise PortAlreadyOpenedException(f"port {port} is already open")

        self.queues[(ip, port)] = PacketQueue()

    def close_port(self, ip: str, port: int):
        """
        Mark the (ip, port) as closed. We will not expect packets in this port anymore
        """
        self.queues.pop((ip, port), None)

    async def get_packet(self, ip: str, port: int):
        """
        Get a packet that was sent to the given (ip, port)
        """
        if (ip, port) not in self.queues.keys():
            raise Exception(f"port {port} is not open")

        # check if there is available packet to consume
        data = self.queues[(ip, port)].pop()
        if data is not None:
            return data

        # if no available packet, then wait for packet to arrive
        return await self.queues[(ip, port)].wait_for_packet()
