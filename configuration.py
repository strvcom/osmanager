import os

class Configuration:
    OPENSEARCH_HOST = os.environ.get('OPENSEARCH_HOST', None)
    AUTH_METHOD = os.environ.get('AUTH_METHOD', None)
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', None)
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    AWS_SERVICE = os.environ.get('AWS_SERVICE', 'es')
    AUTH_METHOD = os.environ.get('AUTH_METHOD', None)
    AWS_USER = os.environ.get('AWS_USER', None)
    AWS_SECRET = os.environ.get('AWS_SECRET', None)
