import abc
from ip_utils import IPAddress
from typing import Optional


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

    @property
    @abc.abstractmethod
    def netmask(self) -> IPAddress:
        """
        the netmask of this adapter
        """
        pass

    @property
    @abc.abstractmethod
    def gateway(self) -> Optional[IPAddress]:
        """
        the gateway of destinations outside LAN
        """
        pass

    @abc.abstractmethod
    async def send(self, packet: bytes):
        """
        send packet through the adapter
        :param packet: the packet to send
        """
        pass
