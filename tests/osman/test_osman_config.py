import pytest
import logging
from parameterized import parameterized

from osman import OsmanConfig

@parameterized.expand(
    [
        ("test http url", "http://example.com", {
            'opensearch_host': "example.com",
            'opensearch_port': 80,
            'opensearch_ssl_enabled': False,
            'opensearch_user': None,
            'opensearch_secret': None,
        }),
        ("test https url", "https://example2.com", {
            'opensearch_host': "example2.com",
            'opensearch_port': 443,
            'opensearch_ssl_enabled': True,
            'opensearch_user': None,
            'opensearch_secret': None,
        }),
         ("test user/secret/default port", "https://user:secret@example3.com", {
            'opensearch_host': "example3.com",
            'opensearch_port': 443,
            'opensearch_ssl_enabled': True,
            'opensearch_user': "user",
            'opensearch_secret': "secret",
        }),
        ("test user/secret/port", "https://user:secret@example3.com:12345", {
            'opensearch_host': "example3.com",
            'opensearch_port': 12345,
            'opensearch_ssl_enabled': True,
            'opensearch_user': "user",
            'opensearch_secret': "secret",
        }),
    ]
)
def test_creating_osman_config_by_host_url(_, host_url, expected):
    """
    Test OsmanConfig initialized by host url
    """
    oc = OsmanConfig(host_url=host_url)
    # FIXME is there a better way to do this?
    for key, val in expected.items():
        assert oc.__dict__[key] == val
        pass

@parameterized.expand(
    [
        ("test 'url' auth method", {
                'opensearch_host': "example.com",
                'opensearch_port': 12345,
                'opensearch_ssl_enabled': True,
                'opensearch_user': "user",
                'opensearch_secret': "secret",
                'auth_method': "url",
            }, {
                'host_url': "https://user:secret@example.com:12345"
            }
        ),
        ("test 'user' auth method", {
                'opensearch_host': "example.com",
                'opensearch_port': 12345,
                'opensearch_ssl_enabled': True,
                'opensearch_user': "user",
                'opensearch_secret': "secret",
                'auth_method': "user",
            }, {
                'host_url': "https://user:secret@example.com:12345",
                'auth_method': "url",
            }
        ),
        ("test 'awsauth' auth method and default aws_region and aws_service", {
                'opensearch_host': "example.com",
                'opensearch_port': 12345,
                'auth_method': "awsauth",
                'aws_access_key_id': "access_key",
                'aws_secret_access_key': "secret_key",
            }, {
                'opensearch_host': "example.com",
                'opensearch_port': 12345,
                'auth_method': "awsauth",
                'aws_access_key_id': "access_key",
                'aws_secret_access_key': "secret_key",
                'aws_region': "us-east-1",
                'aws_service':"es",
            }
        ),
        ("test 'awsauth' auth method", {
                'opensearch_host': "example2.com",
                'opensearch_port': 12345,
                'auth_method': "awsauth",
                'aws_access_key_id': "access_key",
                'aws_secret_access_key': "secret_key",
                'aws_region': "region",
                'aws_service':"service",
            }, {
                'opensearch_host': "example2.com",
                'opensearch_port': 12345,
                'auth_method': "awsauth",
                'aws_access_key_id': "access_key",
                'aws_secret_access_key': "secret_key",
                'aws_region': "region",
                'aws_service':"service",
            }
        ),
    ]
)
def test_creating_osman_config_auth_method_url_par(_, params, expected):
    """
    Test OsmanConfig for 'url' auth_method initialized by host, port,
            user, secret parameters
    """
    oc = OsmanConfig(**params)
    # FIXME is there a better way to do this?
    for key, val in expected.items():
        assert oc.__dict__[key] == val
        pass

    pass


