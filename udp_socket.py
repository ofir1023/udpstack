import random
from stack import stack
from udp import UDP, PacketQueue

class UDPSocket:
    def __init__(self):
        self.src_port = None
        self.dst_ip = None
        self.dst_port = None

    def __enter__(self):
        return self
  
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def bind(self, src_port: int):
        if src_port < 0 or src_port > 65535:
            raise Exception("trying to bind to invalid port number")

        if src_port == 0:
            src_port = random.randint(1, 65535)

        if not stack.get_protocol(UDP).open_port(src_port):
            raise Exception("there's already a bound socket on port {}".format(src_port))

        self.src_port = src_port

    def connect(self, dst_ip: str, dst_port: int):
        self.dst_ip = dst_ip
        self.dst_port = dst_port

    async def send(self, data):
        if self.dst_port is None or self.dst_ip is None:
            raise Exception("cannot send on an unconnected socket")

        if self.src_port is None:
            self.bind(0)

        await stack.send(UDP, src_port=self.src_port, dst_port=self.dst_port, dst_ip=self.dst_ip, data=data)

    async def sendto(self, data, dst_ip: str, dst_port: int):
        if self.src_port is None:
            self.bind(0)

        return stack.send(UDP, src_port=self.src_port, dst_port=dst_port, dst_ip=dst_ip, data=data)
    
    async def recv(self, buffer_size):
        packet = await self.recvfrom(buffer_size)
        return packet[2]

    async def recvfrom(self, buffer_size):
        if self.src_port is None:
            raise Exception("cannot receive on an unbound socket")

        packet = await stack.get_protocol(UDP).get_packet(self.src_port)
        packet = (packet[0], packet[1], packet[2][:buffer_size])
        return packet

    def close(self):
        if self.src_port:
            stack.get_protocol(UDP).close_port(self.src_port)
            self.src_port = None
    

