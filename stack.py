from __future__ import annotations
import abc
from typing import Optional, Type, List
from treelib import Tree

from route_table import RouteTable, RouteEntry
from ip_utils import IPAddress
from adapter_interface import NetworkAdapterInterface
from task_creator import TaskCreator
from packet import Packet


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
    async def handle(self, packet: Packet, adapter: NetworkAdapterInterface) -> Optional[int]:
        """
        handle a packet that contains the given protocol
        :param packet: Packet object representing the packet. use packet.current_packet for buffer starting
                       with the current layer. you can use packet.get_layer to access previous layers.
                       if there is more processing to do, add your new layer with packet.add_layer
        :param adapter: the adapter from which the packet was received
        :return: the id of the next protocol to process the packet, or None if this packet shouldn't be processed more
        """
        pass


class NetworkStack(TaskCreator):
    _protocols = Tree()

    def __init__(self):
        self._route_table = RouteTable()
        self._adapters = []  # type: List[NetworkAdapterInterface]
        super().__init__()

    def add_adapter(self, adapter: NetworkAdapterInterface):
        """
        Add a new adapter to the stack
        Now, if a packet will be sent to an IP relevant to this adapter, This adapter will be used.
        """
        self._route_table.add_adapter(adapter)
        self._adapters.append(adapter)

    def remove_adapter(self, adapter: NetworkAdapterInterface):
        """
        Remove adapter from the stack. This adapter will not be used anymore as destination for packets
        """
        self._route_table.remove_adapter(adapter)
        self._adapters.remove(adapter)

    def get_adapter(self, ip: str) -> NetworkAdapterInterface:
        """
        Get an adapter that uses the given ip as source ip
        """
        for adapter in self._adapters:
            if adapter.ip == ip:
                return adapter
        raise Exception('The given ip is not the source ip of any adapter')

    def add_static_route(self, entry: RouteEntry):
        """
        Add a static route. This should be used to add a route that's not a natural route of the adapter
        """
        return self._route_table.add_static_route(entry)

    @classmethod
    def register_protocol(cls, protocol: Type[ProtocolInterface]):
        """
        Register a protocol to the stack. This protocol can be used now for building and handling packets
        """
        parent = None
        if protocol.NEXT_PROTOCOL is not None:
            parent = cls._protocols.get_node(protocol.NEXT_PROTOCOL)
        cls._protocols.create_node(identifier=protocol, parent=parent, data=protocol())

    def add_packet(self, packet: bytes, adapter: NetworkAdapterInterface):
        """
        Add a new packet to the stack.
        This should be called by adapters when they get a new packet
        """
        self.create_task(self._handle_packet(packet, adapter))

    async def send(self, top_protocol: ProtocolInterface, dst_ip: IPAddress,
                   expected_adapter: NetworkAdapterInterface = None, **options):
        """
        Send a packet using this stack
        @param top_protocol - the top protocol of the packet. This below protocol will be inferred automatically.
        @param dst_ip - the destination IP of the packet
        @param expected_adapter - optional parameter to guess the adapter that will be used for this packet. If the
                                  stack decides to use another adapter, it will raise
        @param options - another information about the packet. it will be passed to the protocols of packet.
                         this information is different per every packet type
        """
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
        """
        Get the protocol object of the given type
        """
        return cls._protocols.get_node(protocol_type).data

    async def _handle_packet(self, packet_data: bytes, adapter: NetworkAdapterInterface):
        """
        The task implementation of handling a packet.
        Iterating through the protocols until handling the whole packet
        """
        protocol_node = self._protocols.get_node(self._protocols.root)
        packet = Packet(packet_data)
        while True:
            protocol_id = await protocol_node.data.handle(packet, adapter)
            if protocol_id is None:
                # handler decided to dump packet
                break

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
