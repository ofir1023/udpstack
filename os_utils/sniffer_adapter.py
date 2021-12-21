from os_utils.sniffer import Sniffer
from adapter import TaskNetworkAdapter
from ip_utils import IPAddress

from typing import Optional


class SnifferNetworkAdapter(TaskNetworkAdapter):
    def __init__(self, device: str, mac: str, ip: IPAddress, netmask: IPAddress, gateway: IPAddress, mtu: int):
        super().__init__()
        self._mac = mac
        self._ip = ip
        self._netmask = netmask
        self._gateway = gateway
        self._mtu = mtu
        self.sniffer = Sniffer(device)

    async def get_packet(self):
        return await self.sniffer.recv(self._mtu)

    @property
    def mac(self) -> str:
        return self._mac

    @property
    def ip(self) -> IPAddress:
        return self._ip

    @property
    def netmask(self) -> IPAddress:
        # everything goes through this adapter
        return self._netmask

    @property
    def gateway(self) -> Optional[IPAddress]:
        return self._gateway

    async def send(self, packet: bytes):
        await self.sniffer.send(packet)