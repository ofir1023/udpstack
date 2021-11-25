from ip_utils import IPAddress
from adapter import NetworkAdapterInterface
from typing import List, Tuple, Optional


class RouteEntry:
    def __init__(self, adapter: NetworkAdapterInterface, dst_ip: IPAddress, netmask: IPAddress,
                 gateway: Optional[IPAddress] = None):
        self._adapter = adapter
        self._dst_ip = dst_ip
        self._netmask = netmask
        self._gateway = gateway

    @property
    def gateway(self):
        return self._gateway

    @property
    def adapter(self):
        return self._adapter

    def route(self, ip: IPAddress) -> int:
        """
        returns a "grade" of routing to this ip with this entry. higher grade means that this route is preferable.
        -1 means that it can't be used
        """
        if ip.in_network(self._dst_ip, self._netmask):
            # if the netmask is bigger, it means the route is more specific which is preferable
            return int(self._netmask)
        return -1


class RouteTable:
    def __init__(self):
        self._entries = []  # type: List[RouteEntry]

    def add_adapter(self, adapter: NetworkAdapterInterface):
        if adapter.gateway is not None:
            assert adapter.gateway.in_network(adapter.ip, adapter.netmask), 'gateway must be in LAN'
            # if the adapter has gateway anything can be route through it
            self._entries.append(RouteEntry(adapter, IPAddress('0.0.0.0'), IPAddress('0.0.0.0'), adapter.gateway))
        self._entries.append(RouteEntry(adapter, adapter.ip, adapter.netmask))

    def add_static_route(self, entry: RouteEntry):
        self._entries.append(entry)

    def route(self, ip: IPAddress) -> Tuple[NetworkAdapterInterface, Optional[IPAddress]]:
        """
        find an adapter to use for the given ip
        returns (adapter, gateway). gateway can be None if there is no need for gateway
        """
        best_grade = -1
        best_entry = None
        for entry in self._entries:
            entry_grade = entry.route(ip)
            if entry_grade > best_grade:
                best_grade = entry_grade
                best_entry = entry
        assert best_entry is not None, 'no route for address'
        return best_entry.adapter, best_entry.gateway

    def remove_adapter(self, adapter: NetworkAdapterInterface):
        self._entries = [entry for entry in self._entries if entry.adapter is not adapter]
