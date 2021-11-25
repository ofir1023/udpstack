from __future__ import annotations

from typing import Union
import ipaddress


class IPAddress:
    ADDRESS_LENGTH = 4

    def __init__(self, ip: Union[str, bytes, int, IPAddress]):
        if isinstance(ip, bytes):
            ip = '.'.join(str(part) for part in ip)
        elif isinstance(ip, int):
            ip = str(ipaddress.IPv4Address(ip))
        elif isinstance(ip, IPAddress):
            ip = str(ip)
        assert isinstance(ip, str)
        self._ip = ip

    def __bytes__(self):
        assert len(self._ip.split('.')) == self.ADDRESS_LENGTH
        return bytes(map(int, self._ip.split('.')))

    def __int__(self):
        return int(ipaddress.IPv4Address(self._ip))

    def __str__(self):
        return self._ip

    def __eq__(self, other: Union[IPAddress, str, bytes, int]):
        return self._ip == IPAddress(other)._ip

    def in_network(self, ip: IPAddress, netmask: IPAddress):
        return (int(ip) & int(netmask)) == (int(self) & int(netmask))
