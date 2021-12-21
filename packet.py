from typing import Dict


class Layer:
    def __init__(self, data: bytes, attributes: dict, tail=None):
        self.data = data
        self.attributes = attributes
        self.tail = tail


class Packet:
    """
    This object represents a packet while in processing stack.
    It starts with the packet as raw bytes, and as we process the packet, every layer should call "add_layer" to declare
    a part of the data as a layer.
    """
    def __init__(self, packet: bytes):
        self._rest_of_packet = packet
        self._all_packet = packet
        self._layers = {}  # type: Dict[str, Layer]

    def add_layer(self, name: str, attributes: dict, size: int, tail_size=0):
        """
        Declare part of the data as a new layer
        @param name - the name of the layer, this name should be used in `get_layer`
        @param attributes - attributes of the layer. should be the information found while processing the protocol
        @param size - the size from the current packet of the new layer
        @param tail_size - add some data from the end of the current packet to the layer
        """
        data = self._rest_of_packet[:size]
        self._rest_of_packet = self._rest_of_packet[size:]

        tail = None
        if tail_size:
            tail = self._rest_of_packet[-tail_size:]
            self._rest_of_packet = self._rest_of_packet[:-tail_size]

        self._layers[name] = Layer(data, attributes, tail)

    def get_layer(self, name):
        """
        Get layer of the given name. Name should be the same name used before in `add_layer`
        """
        return self._layers[name]

    @property
    def current_packet(self):
        """
        Returns the part of the packet that wasn't declared yet as part of any layer
        """
        return self._rest_of_packet

    @property
    def all_packet(self):
        """
        Return all the raw packet
        """
        return self._all_packet

