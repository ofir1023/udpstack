import pytest
from inspect import iscoroutine
from time import sleep

from arp_table import ARPTable, ARPEntry
from ip_utils import IPAddress

TEST_IP = IPAddress('1.1.1.1')
TEST_MAC = '01:23:45:67:89:ab'
BAD_MAC = '00:00:00:00:00:00'


@pytest.fixture()
def arp_table():
    return ARPTable()


def test_mac_exists(arp_table):
    arp_table.update(TEST_IP, TEST_MAC)
    assert arp_table.get_mac(TEST_IP) == TEST_MAC


@pytest.mark.asyncio
async def test_wait_for_mac(arp_table):
    result = arp_table.get_mac(TEST_IP)
    assert iscoroutine(result), 'we should wait for the mac'
    arp_table.update(TEST_IP, TEST_MAC)
    assert await result == TEST_MAC


def test_change_mac(arp_table):
    arp_table.update(TEST_IP, BAD_MAC)
    arp_table.update(TEST_IP, TEST_MAC)
    assert arp_table.get_mac(TEST_IP) == TEST_MAC


@pytest.mark.asyncio
async def test_mac_expired(arp_table):
    ARPEntry.UP_TO_DATE_TIMEOUT = 0.1  # we don't really want to wait
    arp_table.update(TEST_IP, TEST_MAC)
    sleep(1)

    result = arp_table.get_mac(TEST_IP)
    assert iscoroutine(result), 'mac should not be available'

    arp_table.update(TEST_IP, TEST_MAC)
    assert await result == TEST_MAC
