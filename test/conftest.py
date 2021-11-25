import sys
sys.path.append('..')


import pytest
from network_adapter import MockNetworkAdapter
from stack import stack


@pytest.fixture(autouse=True)
def adapter():
    adapter = MockNetworkAdapter()
    stack.add_adapter(adapter)
    yield adapter
    stack.remove_adapter(adapter)
