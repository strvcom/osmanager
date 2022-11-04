#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import urllib
from opensearchpy import OpenSearch

class OsmanConfig:
    """
    Osman configuration holder class
    """

    """
    Class Attributes
    ----------------
    Class attributes are initialized by the environment variables with
    the same name.
   
    OPENSEARCH_HOST: str
        OpenSearch instance host
    OPENSEARCH_PORT: int
        OpenSearch instance port. Default: 443
    OPENSEARCH_SSL_ENABLED: bool
        True -- use SSL, False -- don't use SSL. Default: True
    OPENSEARCH_USER: str
        OpenSearch user, for backward compatibility AWS_USER env variable
        is also read
    OPENSEARCH_SECRET: str
        OpenSearch password, for backward compatibility AWS_SECRET env variable
        is also read

    AUTH_METHOD: str
        "url" -- use standard uri/url scheme for OpenSearch host
        "user" -- the same as "url", for backward compatibility
        "awsauth" -- use aws4auth for http_auth, the connection parameters
             are read from the following AWS_* attributes

    See also aws4auth documentation https://github.com/tedder/requests-aws4auth
    AWS_ACCESS_KEY_ID: str
        Access key for AWS authentication
    AWS_SECRET_ACCESS_KEY: str
        Secret access key for AWS authentication
    AWS_REGION: str
        Default: "us-east-1"
    AWS_SERVICE: str
        Default: "es"

    """
    OPENSEARCH_HOST = os.environ.get('OPENSEARCH_HOST', None)
    OPENSEARCH_PORT = os.environ.get('OPENSEARCH_PORT', 443)
    OPENSEARCH_SSL_ENABLED = os.environ.get('OPENSEARCH_SSL_ENABLED', True)

    # For backward compatibility we allow AWS_USER and AWS_SECRET variables
    OPENSEARCH_USER = os.environ.get('OPENSEARCH_USER',
        os.environ.get('AWS_USER', None))
    OPENSEARCH_SECRET = os.environ.get('OPENSEARCH_SECRET',
        os.environ.get('AWS_SECRET', None))

    AUTH_METHOD = os.environ.get('AUTH_METHOD', None)

    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', None)
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)

    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    AWS_SERVICE = os.environ.get('AWS_SERVICE', 'es')

    """
    Instance Attributes
    -------------------
    host_url: str
        a complete url of the OpenSearch instance, with schema/user/pass
   
    For the following attributes description see the class attributes above.

    opensearch_host: str
    opensearch_port: int
    opensearch_ssl_enabled: bool
    opensearch_user: str
    opensearch_secret: str

    auth_method: str

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    aws_service: str

    """
    def __init__(self,
        host_url=None,

        opensearch_host=OPENSEARCH_HOST,
        opensearch_port=OPENSEARCH_PORT,
        opensearch_ssl_enabled=OPENSEARCH_SSL_ENABLED,
        opensearch_user=OPENSEARCH_USER,
        opensearch_secret=OPENSEARCH_SECRET,

        auth_method=AUTH_METHOD,

        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_region=AWS_REGION,
        aws_service=AWS_SERVICE,
        ):

        """
        Init OsmanConfig

        Parameters
        ----------
        see Instance Attributes
        """

        # non empty host_url takes precedence over auth_method
        if host_url:
            assert not auth_method or (auth_method in ["url", "user"])
            logging.info(f"Using host_url: '{host_url}'")
            self.host_url = host_url
            self.auth_method = "url"

            parsed_url = urllib.parse.urlparse(host_url)

            assert parsed_url.scheme in ["http", "https"]
            self.opensearch_ssl_enabled = \
                True if parsed_url.scheme == 'https' else False

            self.opensearch_host = parsed_url.hostname
            if not parsed_url.port:
                if parsed_url.scheme == "http":
                    self.opensearch_port = 80
                else:
                    self.opensearch_port = 443
            else:
                self.opensearch_port = parsed_url.port

            self.opensearch_user = parsed_url.username
            self.opensearch_secret = parsed_url.password
            # All other parameters are ignored
            return
        
        assert auth_method in ["url", "user", "awsauth"]

        assert opensearch_host
        assert opensearch_port
        assert type(opensearch_ssl_enabled) == bool

        self.opensearch_host = opensearch_host
        self.opensearch_port = opensearch_port
        self.opensearch_ssl_enabled = opensearch_ssl_enabled

        if auth_method in ["url", "user"]:
            self.auth_method = "url"
            assert opensearch_user
            assert opensearch_secret
            logging.info(f"Using auth_method 'url' and '{opensearch_host}:{opensearch_port}'")
            os_creds_user = urllib.parse.quote_plus(f'{opensearch_user}')
            os_creds_pass = urllib.parse.quote_plus(f'{opensearch_secret}')
            os_scheme = 'https' if opensearch_ssl_enabled else 'http'

            self.auth_method = "url"
            self.host_url = \
              f'{os_scheme}://{os_creds_user}:{os_creds_pass}@{opensearch_host}:{opensearch_port}'

            self.opensearch_user = opensearch_user
            self.opensearch_secret = opensearch_secret
            return            
         
        # AWS auth method
        self.auth_method = "awsauth"
        logging.info(f"Using auth_method 'awsauth' and '{opensearch_host}:{opensearch_port}'")
        self.host_url = ''

        assert aws_access_key_id
        assert aws_secret_access_key
        assert aws_region
        assert aws_service
 
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region
        self.aws_service = aws_service
        return
