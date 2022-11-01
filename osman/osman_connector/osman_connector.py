import urllib.parse

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


class OsmanConnector:
    def __init__(
        self, 
        host, 
        aws_access_key_id, 
        aws_secret_access_key, 
        aws_region='us-east-1', 
        aws_service='es', 
        auth_method='service',
        aws_user='user',
        aws_secret='secret'
    ):
        self.host = host
        if auth_method == 'user':
            os_creds_user = urllib.parse.quote_plus(f'{aws_user}')
            os_creds_pass = urllib.parse.quote_plus(f'{aws_secret}')
            os_url = f'https://{os_creds_user}:{os_creds_pass}@{host}:443'
            connection = OpenSearch(
                hosts=[os_url],
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection
            )
        else:
            awsauth = AWS4Auth(aws_access_key_id, aws_secret_access_key,
                               aws_region, aws_service)
            connection = OpenSearch(
                hosts=[{'host': host, 'port': 443}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection
            )
        self.connection = connection