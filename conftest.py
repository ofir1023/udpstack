import sys
sys.path.append('..')


import pytest
from test.network_adapter import MockNetworkAdapter


@pytest.fixture()
def adapter():
    return MockNetworkAdapter()
