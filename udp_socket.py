import random
from typing import Optional

from stack import stack
from udp import UDP, PortAlreadyOpenedException
from ip_utils import IPAddress


class UDPSocket:
    BIND_TRIES = 1000

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
        """
        Bind the socket to the given ip and port
        This means that every packet will be sent from this ip and port
        Can be called with src_ip=None to bind on all adapters.
        Can be called with src_port=0 and this function will find an open port to bind on.
        """
        if self.closed:
            raise Exception("socket is closed")

        if src_port < 0 or src_port > 65535:
            raise Exception("trying to bind to invalid port number")

        if src_ip and src_ip != '0.0.0.0':
            self.src_adapter = stack.get_adapter(src_ip)
            self.src_ip = src_ip

        if src_port == 0:
            src_port = random.randint(1, 65535)
            for _ in range(self.BIND_TRIES):
                try:
                    stack.get_protocol(UDP).open_port(src_ip, src_port)
                    break
                except PortAlreadyOpenedException:
                    src_port = random.randint(1, 65535)
                
        else:
            stack.get_protocol(UDP).open_port(src_ip, src_port)
            self.src_ip = src_ip
                
        self.src_port = src_port

    def connect(self, dst_ip: str, dst_port: int):
        """
        Mark the given ip and port as destinations of this socket.
        From now, `send` can be used and not only `sento`
        """
        if self.closed:
            raise Exception("socket is closed")

        self.dst_ip = IPAddress(dst_ip)
        self.dst_port = dst_port

    async def send(self, data):
        """
        Send the data to the destination. `connect` should be used before this function to mark the destination.
        """
        if self.closed:
            raise Exception("socket is closed")

        if self.dst_port is None or self.dst_ip is None:
            raise Exception("cannot send on an unconnected socket")

        if self.src_port is None:
            self.bind(None, 0)

        await stack.send(UDP, src_port=self.src_port, dst_port=self.dst_port, dst_ip=self.dst_ip,
                         data=data, expected_adapter=self.src_adapter)

    async def sendto(self, data, dst_ip: str, dst_port: int):
        """
        Send the given data to the given ip and port
        """
        if self.closed:
            raise Exception("socket is closed")

        if self.src_port is None:
            self.bind(None, 0)

        return stack.send(UDP, src_port=self.src_port, dst_port=dst_port, dst_ip=dst_ip, data=data)
    
    async def recv(self):
        """
        Recv the next packet sent to this socket. `bind` should be called before to mark what port and ip should
        be the destination of the returned packet
        """
        packet = await self.recvfrom()
        return packet[2]

    async def recvfrom(self):
        """
        See `recv` documentation. This function also returns the information of the sender.
        Returns a tuple of (source ip, source port, packet data)
        """
        if self.closed:
            raise Exception("socket is closed")

        if self.src_port is None:
            raise Exception("cannot receive on an unbound socket")

        packet = await stack.get_protocol(UDP).get_packet(self.src_ip, self.src_port)
        packet = (packet[0], packet[1], packet[2])
        return packet

    def close(self):
        """
        Close the socket and stop listening on the port we listened on.
        """
        if self.closed:
            return

        self.closed = True

        if self.src_port:
            stack.get_protocol(UDP).close_port(self.src_ip, self.src_port)
            self.src_port = None
