"""
Tests for OsmanConfig class
"""
import logging
import pytest
from parameterized import parameterized

from osman import OsmanConfig

@parameterized.expand(
    [
        (
            "test http url",
            "http://example.com",
            {
                "opensearch_host": "example.com",
                "opensearch_port": 80,
                "opensearch_ssl_enabled": False,
                "opensearch_user": None,
                "opensearch_secret": None,
            }
        ),
        (
            "test https url",
            "https://example2.com",
            {
                "opensearch_host": "example2.com",
                "opensearch_port": 443,
                "opensearch_ssl_enabled": True,
                "opensearch_user": None,
                "opensearch_secret": None,
            }
        ),
        (
            "test user/secret/default port",
            "https://user:secret@example3.com",
            {
                "opensearch_host": "example3.com",
                "opensearch_port": 443,
                "opensearch_ssl_enabled": True,
                "opensearch_user": "user",
                "opensearch_secret": "secret",
            }
        ),
        (
            "test user/secret/port",
            "https://user:secret@example3.com:12345",
            {
                "opensearch_host": "example3.com",
                "opensearch_port": 12345,
                "opensearch_ssl_enabled": True,
                "opensearch_user": "user",
                "opensearch_secret": "secret",
            }
        ),
    ]
)
def test_creating_osman_config_by_host_url(_:str, host_url:str, expected:dict):
    """
    Test OsmanConfig initialized by host url
    """
    config = OsmanConfig(host_url=host_url)
    for key, val in expected.items():
        assert config.__dict__[key] == val

@parameterized.expand(
    [
        (
            "test 'http' auth method",
            {
                "opensearch_host": "example.com",
                "opensearch_port": 12345,
                "opensearch_ssl_enabled": True,
                "opensearch_user": "user",
                "opensearch_secret": "secret",
                "auth_method": "http",
            },
            {
                "host_url": "https://user:secret@example.com:12345"
            }
        ),
        (
            "test 'user' auth method",
            {
                "opensearch_host": "example.com",
                "opensearch_port": 12345,
                "opensearch_ssl_enabled": True,
                "opensearch_user": "user",
                "opensearch_secret": "secret",
                "auth_method": "user",
            },
            {
                "host_url": "https://user:secret@example.com:12345",
                "auth_method": "http",
            }
        ),
        (
            "test 'awsauth' auth method and default aws_region and aws_service",
            {
                "opensearch_host": "example.com",
                "opensearch_port": 12345,
                "auth_method": "awsauth",
                "aws_access_key_id": "access_key",
                "aws_secret_access_key": "secret_key",
            },
            {
                "opensearch_host": "example.com",
                "opensearch_port": 12345,
                "auth_method": "awsauth",
                "aws_access_key_id": "access_key",
                "aws_secret_access_key": "secret_key",
            }
        ),
        (
            "test 'awsauth' auth method",
            {
                "opensearch_host": "example2.com",
                "opensearch_port": 12345,
                "auth_method": "awsauth",
                "aws_access_key_id": "access_key",
                "aws_secret_access_key": "secret_key",
                "aws_region": "region",
                "aws_service":"service",
            },
            {
                "opensearch_host": "example2.com",
                "opensearch_port": 12345,
                "auth_method": "awsauth",
                "aws_access_key_id": "access_key",
                "aws_secret_access_key": "secret_key",
                "aws_region": "region",
                "aws_service":"service",
            }
        ),
    ]
)
def test_creating_osman_config_auth_method_url_par(_:str, params:dict, expected:dict):
    """
    Test OsmanConfig for different auth_methods initialized by host, port,
    user, secret parameters
    """
    config = OsmanConfig(**params)
    for key, val in expected.items():
        assert config.__dict__[key] == val

def test_default_config_values():
    """
    Test OsmanConfig default values when environment variables don't exist.
    NOTE: The external environment variables are deleted in conftest.py during init.
    """
    with pytest.raises(AssertionError) as ex:
        OsmanConfig()
    assert ex.match("auth_method wrong")

# NOTE: We can't use 'parametrized.expand' here as 'parametrized' doesn't support fixtures
@pytest.mark.parametrize(
    "test_case_name,env_vars,expected",
    [
        (
            "test 'http' auth method",
            {
                "OPENSEARCH_HOST": "example.com",
                "OPENSEARCH_PORT": 12345,
                "OPENSEARCH_SSL_ENABLED": True,
                "OPENSEARCH_USER": "user",
                "OPENSEARCH_SECRET": "secret",
                "AUTH_METHOD": "user",
            },
            {
                "host_url": "https://user:secret@example.com:12345",
                "opensearch_host": "example.com",
                "opensearch_port": 12345,
                "opensearch_ssl_enabled": True,
                "opensearch_user": "user",
                "opensearch_secret": "secret",
                "auth_method": "http",
            }
        ),
        (
            "test deprecated AWS_USER, AWS_SECRET variables",
            {
                "OPENSEARCH_HOST": "example.com",
                "OPENSEARCH_PORT": 12345,
                "OPENSEARCH_SSL_ENABLED": True,
                "AWS_USER": "user",
                "AWS_SECRET": "secret",
                "AUTH_METHOD": "user",
            },
            {
                "host_url": "https://user:secret@example.com:12345",
                "opensearch_host": "example.com",
                "opensearch_port": 12345,
                "opensearch_ssl_enabled": True,
                "opensearch_user": "user",
                "opensearch_secret": "secret",
                "auth_method": "http",
            }
        ),
        (
            "test 'awsauth' auth method",
            {
                "OPENSEARCH_HOST": "example2.com",
                "OPENSEARCH_PORT": 12345,
                "AUTH_METHOD": "awsauth",
                "AWS_ACCESS_KEY_ID": "access_key",
                "AWS_SECRET_ACCESS_KEY": "secret_key",
                "AWS_REGION": "region",
                "AWS_SERVICE":"service",
            },
            {
                "opensearch_host": "example2.com",
                "opensearch_port": 12345,
                "auth_method": "awsauth",
                "aws_access_key_id": "access_key",
                "aws_secret_access_key": "secret_key",
                "aws_region": "region",
                "aws_service":"service",
            }
        ),
    ]
)
def test_config_values_from_environment(
    monkeypatch,
    test_case_name:str,
    env_vars:dict,
    expected:dict):
    """
    Test OsmanConfig for setting corect attributes from environment variables.
    """
    logging.info("Testcase: '%s'", test_case_name)
    # Create some OsmanConfig instance, it will be overwritten
    config = OsmanConfig(host_url="http://example.com")

    # Use monkeypatch to save environment for the outside world
    for variable, val in env_vars.items():
        monkeypatch.setenv(variable, str(val))

    config._reload_defaults_from_env()
    for attribute, val in expected.items():
        assert config.__dict__[attribute] == val
