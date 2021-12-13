import random
from typing import Optional

from stack import stack
from udp import UDP
from ip_utils import IPAddress


class UDPSocket:
    def __init__(self):
        self.src_ip = None
        self.src_adapter = None
        self.src_port = None
        self.dst_ip = None
        self.dst_port = None
        self.closed = False

    def __enter__(self):
        return self
  
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def bind(self, src_ip: Optional[str], src_port: int):
        if self.closed:
            raise Exception("socket is closed")

        if src_port < 0 or src_port > 65535:
            raise Exception("trying to bind to invalid port number")

        if src_ip and src_ip != '0.0.0.0':
            self.src_adapter = stack.get_adapter(src_ip)
            self.src_ip = src_ip

        if src_port == 0:
            src_port = random.randint(1, 65535)
            while True:
                try:
                    stack.get_protocol(UDP).open_port(src_ip, src_port)
                    break
                except:
                    src_port = random.randint(1, 65535)
                
        else:
            stack.get_protocol(UDP).open_port(src_ip, src_port)
            self.src_ip = src_ip
                
        self.src_port = src_port

    def connect(self, dst_ip: str, dst_port: int):
        if self.closed:
            raise Exception("socket is closed")

        self.dst_ip = IPAddress(dst_ip)
        self.dst_port = dst_port

    async def send(self, data):
        if self.closed:
            raise Exception("socket is closed")

        if self.dst_port is None or self.dst_ip is None:
            raise Exception("cannot send on an unconnected socket")

        if self.src_port is None:
            self.bind(None, 0)

        await stack.send(UDP, src_port=self.src_port, dst_port=self.dst_port, dst_ip=self.dst_ip,
                         data=data, expected_adapter=self.src_adapter)

    async def sendto(self, data, dst_ip: str, dst_port: int):
        if self.closed:
            raise Exception("socket is closed")

        if self.src_port is None:
            self.bind(None, 0)

        return stack.send(UDP, src_port=self.src_port, dst_port=dst_port, dst_ip=dst_ip, data=data)
    
    async def recv(self, buffer_size):
        packet = await self.recvfrom(buffer_size)
        return packet[2]

    async def recvfrom(self, buffer_size):
        if self.closed:
            raise Exception("socket is closed")

        if self.src_port is None:
            raise Exception("cannot receive on an unbound socket")

        packet = await stack.get_protocol(UDP).get_packet(self.src_ip, self.src_port)
        packet = (packet[0], packet[1], packet[2][:buffer_size])
        return packet

    def close(self):
        if self.closed:
            return

        self.closed = True

        if self.src_port:
            stack.get_protocol(UDP).close_port(self.src_ip, self.src_port)
            self.src_port = None
