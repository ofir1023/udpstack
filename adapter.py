import abc
from ip_utils import IPAddress


class NetworkAdapterInterface(abc.ABC):
    @property
    @abc.abstractmethod
    def mac(self) -> str:
        """
        the mac of the adapter
        :return:
        """
        pass

    @property
    @abc.abstractmethod
    def ip(self) -> IPAddress:
        """
        the ip of the adapter
        """
        pass

    @abc.abstractmethod
    async def send(self, packet: bytes):
        """
        send packet through the adapter
        :param packet: the packet to send
        """
        pass
