import sys
sys.path.append('..')


import pytest
from network_adapter import MockNetworkAdapter


@pytest.fixture()
def adapter():
    return MockNetworkAdapter()
