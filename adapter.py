from sniffer import Sniffer
from task_creator import TaskCreator
from stack import stack


class TaskNetworkAdapter(NetworkAdapterInterface, TaskCreator):
    def __init__(self):
        super().__init__()

    def start(self):
        self.create_task(self.handle_packets())

    async def handle_packets(self):
        while True:
            packet = await self.get_packet()
            stack.add_packet(packet, self)

    @abc.abstractmethod
    async def get_packet(self):
        pass


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