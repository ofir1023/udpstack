import asyncio
import socket


class Sniffer:
    ETH_P_ALL = 3

    def __init__(self, device: str):
        self.sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(self.ETH_P_ALL))
        self.sock.bind((device, 0))
        self.loop = asyncio.get_event_loop()

    async def recv(self, size: int):
        return await self.loop.sock_recv(self.sock, size)

    async def send(self, data: bytes):
        await self.loop.sock_sendall(self.sock, data)
