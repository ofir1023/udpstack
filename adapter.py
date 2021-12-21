import abc
from task_creator import TaskCreator
from stack import stack
from adapter_interface import NetworkAdapterInterface


class TaskNetworkAdapter(NetworkAdapterInterface, TaskCreator):
    def __init__(self):
        super().__init__()
        self.create_task(self.handle_packets())

    async def handle_packets(self):
        """
        A task for packet processing
        Gets a packet using abstract get_packet and add it to the stack
        """
        packet = await self.get_packet()
        stack.add_packet(packet, self)
        self.create_task(self.handle_packets())

    @abc.abstractmethod
    async def get_packet(self):
        """
        Abstract method for getting a packet
        Adapter implementation should implement that according to the adapter type
        """
        pass
