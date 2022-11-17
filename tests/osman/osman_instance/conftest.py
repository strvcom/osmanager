"""
Osman instance test configuration and setup
"""
import time
import logging
import pytest

def get_random_index_name(prefix: str) -> str:
    """
    Return a random index name
    """
    return prefix + "_" + str(int(time.time()*1000000))

@pytest.fixture
def random_index_name(request):
    """
    Fixture for getting random index name. Usefull when testing
    manual index manipulation
    """
    return get_random_index_name(request.function.__name__)

@pytest.fixture
def index_handler(request):
    """
    Creates new index, yields index name to test case so it can use it
    and after the test is done deletes the index.
    Expects the following params in 'request':
    os_man: Osman
        Osman instance
    mapping: dict
        Index mapping, can be None
    """
    assert request.param
    assert request.param["os_man"]
    assert request.param["mapping"]

    # Get name of the caller function (name of the test)
    caller_name = request.function.__name__

    # Create index name as `caller_name` + timestamp
    index_name = get_random_index_name(caller_name)
    logging.info("Creating index '%s'", index_name)

    mapping = request.param["mapping"]
    os_man = request.param["os_man"]

    # Create new index with `index_name` and optional mapping using the helper
    res = os_man.create_index(index_name, mapping)
    logging.debug(res)

    # Return name of the index to the test that is using this fixture
    yield index_name

    # Once the test ends (or crash) this line will be executed
    os_man.delete_index(index_name)
