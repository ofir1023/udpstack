from typing import Dict


class Layer:
    def __init__(self, data: bytes, attributes: dict, tail=None):
        self.data = data
        self.attributes = attributes
        self.tail = tail


class Packet:
    def __init__(self, packet: bytes):
        self._rest_of_packet = packet
        self._all_packet = packet
        self._layers = {}  # type: Dict[str, Layer]

    def add_layer(self, name: str, attributes: dict, size: int, tail_size=0):
        data = self._rest_of_packet[:size]
        self._rest_of_packet = self._rest_of_packet[size:]

        tail = None
        if tail_size:
            tail = self._rest_of_packet[-tail_size:]
            self._rest_of_packet = self._rest_of_packet[:-tail_size]

        self._layers[name] = Layer(data, attributes, tail)

    def get_layer(self, name):
        return self._layers[name]

    @property
    def current_packet(self):
        return self._rest_of_packet

    @property
    def all_packet(self):
        return self._all_packet

