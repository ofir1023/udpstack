from __future__ import annotations
import abc
from typing import Optional, Tuple, Type, List
from treelib import Tree

from route_table import RouteTable
from ip_utils import IPAddress
from adapter import NetworkAdapterInterface
from task_creator import TaskCreator


class ProtocolInterface(abc.ABC):
    ABOVE_PROTOCOLS = {}
    PROTOCOL_ID = None
    NEXT_PROTOCOL = None

    @abc.abstractmethod
    async def build(self, adapter: NetworkAdapterInterface, packet: bytes, options: dict) -> bytes:
        """
        build the struct of the protocol
        :param adapter: the adapter in which the packet will be sent
        :param packet: the packet that was built by previous protocols
        :param options: options about what to build
        :return: built protocol structure
        """
        pass

    @abc.abstractmethod
    async def handle(self, packet: bytes, adapter: NetworkAdapterInterface, packet_description: dict) \
            -> Optional[Tuple[bytes, int]]:
        """
        handle a packet that contains the given protocol
        :param packet: the packet, starting from the layer of this protocol
        :param adapter: the adapter from which the packet was received
        :param packet_description: information about the packet from lower layers. information inferred in this layer
                                   should be added to it.
        :return: if None, stop handling this packet
                 else, tuple of (packet starting in the next layer, next layer id)
        """
        pass


class NetworkStack(TaskCreator):
    _protocols = Tree()

    def __init__(self):
        self._route_table = RouteTable()
        super().__init__()

    def add_adapter(self, adapter: NetworkAdapterInterface):
        self._route_table.add_adapter(adapter)

    def remove_adapter(self, adapter: NetworkAdapterInterface):
        self._route_table.remove_adapter(adapter)

    def get_adapter(self, ip: str) -> NetworkAdapterInterface:
        return self._route_table.get_adapter(ip)

    @classmethod
    def register_protocol(cls, protocol: Type[ProtocolInterface]):
        parent = None
        if protocol.NEXT_PROTOCOL is not None:
            parent = cls._protocols.get_node(protocol.NEXT_PROTOCOL)
        cls._protocols.create_node(identifier=protocol, parent=parent, data=protocol())

    def add_packet(self, packet: bytes, adapter: NetworkAdapterInterface):
        self.create_task(self._handle_packet(packet, adapter))

    async def send(self, top_protocol: ProtocolInterface, dst_ip: IPAddress,
                   expected_adapter: NetworkAdapterInterface = None, **options):
        options['dst_ip'] = dst_ip
        adapter, gateway = self._route_table.route(dst_ip)
        if gateway is not None:
            options['gateway'] = gateway
        assert expected_adapter is None or expected_adapter is adapter, "expected adapter don't fit"

        packet = b''
        protocol_node = self._protocols.get_node(top_protocol)
        while protocol_node is not None:
            packet = await protocol_node.data.build(adapter, packet, options)
            options['previous_protocol_id'] = protocol_node.data.PROTOCOL_ID
            protocol_node = self._protocols.parent(protocol_node.identifier)

        await adapter.send(packet)

    @classmethod
    def get_protocol(cls, protocol_type: type) -> ProtocolInterface:
        return cls._protocols.get_node(protocol_type).data

    async def _handle_packet(self, packet: bytes, adapter: NetworkAdapterInterface):
        protocol_node = self._protocols.get_node(self._protocols.root)
        packet_description = {}
        while True:
            result = await protocol_node.data.handle(packet, adapter, packet_description)
            if result is None:
                # handler decided to dump packet
                break
            packet, protocol_id = result

            next_protocol_candidates = [node for node in self._protocols.children(protocol_node.identifier)
                                        if node.data.PROTOCOL_ID == protocol_id]
            if len(next_protocol_candidates) == 0:
                # no handlers for the packet
                break
            elif len(next_protocol_candidates) == 1:
                protocol_node = next_protocol_candidates[0]
            else:
                raise Exception("too many handlers for packet")


stack = NetworkStack()
