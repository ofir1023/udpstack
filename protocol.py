from abc import ABC, ABCMeta

from stack import ProtocolInterface, NetworkStack


class ProtocolMeta(ABCMeta):
    def __new__(mcs, name, *args, **kwargs):
        obj = super().__new__(mcs, name, *args, **kwargs)
        if name != 'Protocol':
            NetworkStack.register_protocol(obj)
        return obj


class Protocol(ProtocolInterface, ABC, metaclass=ProtocolMeta):
    pass
