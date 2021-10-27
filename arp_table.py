import time
from asyncio import Event


class ARPEntry:
    UP_TO_DATE_TIMEOUT = 10

    def __init__(self):
        self._mac = None
        self._event = Event()
        self._update_time = time.time()  # doesn't matter since mac is None

    def _is_up_to_date(self):
        return time.time() - self._update_time < self.UP_TO_DATE_TIMEOUT

    def get_mac(self):
        if self._mac is not None and self._is_up_to_date():
            return self._mac
        return None

    async def wait_for_mac(self):
        await self._event.wait()
        return self.get_mac()

    def update(self, mac: str):
        self._mac = mac
        self._update_time = time.time()
        self._event.set()


class ARPTable:
    def __init__(self):
        self.table = {}

    def _get_entry(self, ip: str):
        return self.table.setdefault(ip, ARPEntry())

    def update(self, ip: str, mac: str):
        self._get_entry(ip).update(mac)

    def get_mac(self, ip: str):
        entry = self._get_entry(ip)
        mac = entry.get_mac()
        if mac is not None:
            return mac
        return entry.wait_for_mac()
