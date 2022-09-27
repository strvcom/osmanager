from utils.opensearch_test_helper import OpenSearchTestHelper
from configuration import Configuration
import pytest
import json
import time


def get_opensearch_helper(config=Configuration):
    """
    Creates instance of OpenSearchHelper with credentials from testing Configuration or from provided one
    """
    return OpenSearchTestHelper(
            config.OPENSEARCH_HOST, 
            config.AWS_ACCESS_KEY_ID, 
            config.AWS_SECRET_ACCESS_KEY,
            config.AWS_REGION,
            config.AWS_SERVICE,
            config.AUTH_METHOD,
            config.AWS_USER,
            config.AWS_SECRET
        )


def add_bulk_data_to_index(index_name, data):
    """
    Bulk insert data to index.
    Data should have following format: [{document}, {document}, ...]
    """
    bulk_data = []
    for post_id, document in enumerate(data):
        bulk_data.append({"create": {"_index": index_name, '_id': post_id}})
        bulk_data.append(document)

    os_helper = get_opensearch_helper()
    return os_helper.bulk(bulk_data)


def add_data_to_index_from_json(index_name, json_path):
    """
    Loads data from JSON and bulk insert them to index.
    JSON should have following format: [{document}, {document}, ...]
    """
    with open(json_path) as json_file:
        json_data = json.load(json_file)

    return add_bulk_data_to_index(index_name, json_data)


def get_post_ids_from_response(response):
    if 'hits' not in response:
        print('Missing `hits` in response')
        return None
    
    if 'hits' not in response['hits']:
        print('Missing `hits` in response["hits"]')
        return None
    
    if len(response['hits']['hits']) == 0:
        print('Empty response')
        return []
    
    if 'post_id' not in response['hits']['hits'][0]['_source']:
        print('Missing `post_id` in documents')
        return None
    
    return [document['_source']['post_id'] for document in response['hits']['hits']]


@pytest.fixture
def index_handler(request):
    """
    Creates new index, yields index name to test case so it can use it
    and after the test is done deletes the index
    """
    # Get name of the caller function (name of the test)
    caller_name = request.function.__name__

    # Create index name as `caller_name` + timestamp
    index_name = caller_name+'_'+str(int(time.time()*1000000))

    # Check if there is parameter with index mapping
    try:
        mapping = request.param
    except:
        mapping = None

    # Create new index with `index_name` and optional mapping using the helper
    os_helper = get_opensearch_helper()
    os_helper.create_index(index_name, mapping)

    # Return name of the index to the test that is using this fixture
    yield index_name

    # Once the test ends (or crash) this line will be executed
    os_helper.delete_index(index_name)
