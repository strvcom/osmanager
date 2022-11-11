

import pytest
import time
import logging

from osman import Osman, OsmanConfig


def get_ids_from_response(response):
    """
    Extract id's from OS response dict (index search)
    """

    if "hits" not in response:
        logging.error("Missing `hits` in response.")
        return None

    if "hits" not in response["hits"]:
        logging.error("Missing `hits` in response['hits'].")
        return None

    if len(response["hits"]["hits"]) == 0:
        logging.error("Empty response.")
        return []

    if "id" not in response["hits"]["hits"][0]["_source"]:
        logging.error("Missing `post_id` in documents.")
        return None

    return [document["_source"]["id"] for document in response["hits"]["hits"]]


@pytest.fixture
def index_handler(request):
    """
    Creates new index, yields index name to test case so it can use it
    and after the test is done deletes the index
    """

    # Get name of the caller function (name of the test)
    caller_name = request.function.__name__

    # Create index name as `caller_name` + timestamp
    index_name = caller_name+"_"+str(int(time.time()*1000000))

    # Check if there is parameter with index mapping
    try:
        mapping = request.param
    except ValueError:
        mapping = None

    # Create new index with `index_name` and optional mapping using the helper
    config = OsmanConfig(host_url="http://opensearch-node:9200")
    o = Osman(config)

    res = o.create_index(index_name, mapping)
    logging.info(res)

    # Return name of the index to the test that is using this fixture
    yield index_name

    # Once the test ends (or crash) this line will be executed
    o.delete_index(index_name)
