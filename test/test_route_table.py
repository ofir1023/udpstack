from route_table import RouteTable, RouteEntry
from adapter_interface import NetworkAdapterInterface
from ip_utils import IPAddress
from typing import Optional


class NetworkAdapter(NetworkAdapterInterface):
    def __init__(self, ip: str, netmask: str, gateway: Optional[str] = None):
        self._ip = IPAddress(ip)
        self._netmask = IPAddress(netmask)
        self._gateway = IPAddress(gateway) if gateway is not None else None

    @property
    def mac(self) -> str:
        # unused in route tests
        return ''

    @property
    def ip(self) -> IPAddress:
        return self._ip

    @property
    def netmask(self) -> IPAddress:
        return self._netmask

    @property
    def gateway(self) -> Optional[IPAddress]:
        return self._gateway

    async def send(self, packet: bytes):
        pass


def test_sanity():
    table = RouteTable()
    adapter = NetworkAdapter('1.1.1.1', '255.255.0.0')
    table.add_adapter(adapter)
    assert table.route(IPAddress('1.1.2.2')) == (adapter, None)


def test_two_adapters():
    table = RouteTable()

    adapter1 = NetworkAdapter('1.1.1.1', '255.255.0.0')
    table.add_adapter(adapter1)

    adapter2 = NetworkAdapter('1.2.1.1', '255.255.0.0')
    table.add_adapter(adapter2)

    assert table.route(IPAddress('1.1.2.2')) == (adapter1, None)


def test_gateway():
    table = RouteTable()
    adapter = NetworkAdapter('1.1.1.1', '255.255.0.0', '1.1.1.2')
    table.add_adapter(adapter)

    assert table.route(IPAddress('2.2.2.2')) == (adapter, '1.1.1.2')

    # prefer not using gateway
    assert table.route(IPAddress('1.1.2.2')) == (adapter, None)


def test_more_specific_route():
    table = RouteTable()

    adapter1 = NetworkAdapter('1.1.1.1', '255.255.0.0', '1.1.1.2')
    table.add_adapter(adapter1)

    adapter2 = NetworkAdapter('1.1.1.1', '255.255.255.0', '1.1.1.2')
    table.add_adapter(adapter2)

    assert table.route(IPAddress('1.1.1.2')) == (adapter2, None)


def test_illegal_gateway():
    table = RouteTable()
    try:
        table.add_adapter(NetworkAdapter('1.1.1.1', '255.255.255.0', '1.1.2.2'))
    except AssertionError:
        pass
    else:
        assert False, 'gateway must be in lan'


def test_no_route():
    table = RouteTable()
    table.add_adapter(NetworkAdapter('1.1.1.1', '255.255.255.0'))
    try:
        table.route(IPAddress('1.1.2.2'))
    except AssertionError:
        pass
    else:
        assert False, 'how did it find a route'


def test_remove_adapter():
    table = RouteTable()

    adapter1 = NetworkAdapter('1.1.1.1', '255.255.0.0', '1.1.1.2')
    table.add_adapter(adapter1)

    adapter2 = NetworkAdapter('1.1.1.1', '255.255.255.0', '1.1.1.2')
    table.add_adapter(adapter2)
    table.remove_adapter(adapter2)

    assert table.route(IPAddress('1.1.1.2')) == (adapter1, None)
