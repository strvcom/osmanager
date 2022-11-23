"""
Osman configuration module
"""
import logging
import os
import urllib

from opensearchpy import OpenSearch

from .environment import OSMAN_ENVIRONMENT_VARS


class OsmanConfig:
    """
    Osman configuration holder class

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
        "http" -- use standard uri/url scheme for OpenSearch host
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

    OPENSEARCH_HOST = os.environ.get("OPENSEARCH_HOST", None)
    OPENSEARCH_PORT = int(os.environ.get("OPENSEARCH_PORT", 443))
    OPENSEARCH_SSL_ENABLED = (
        os.environ.get("OPENSEARCH_SSL_ENABLED", "True") == "True"
    )

    # For backward compatibility we allow AWS_USER and AWS_SECRET variables
    OPENSEARCH_USER = os.environ.get(
        "OPENSEARCH_USER", os.environ.get("AWS_USER", None)
    )
    OPENSEARCH_SECRET = os.environ.get(
        "OPENSEARCH_SECRET", os.environ.get("AWS_SECRET", None)
    )

    AUTH_METHOD = os.environ.get("AUTH_METHOD", None)

    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", None)
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", None)

    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
    AWS_SERVICE = os.environ.get("AWS_SERVICE", "es")

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

    def __init__(
        self,
        host_url: str = None,
        opensearch_host: str = OPENSEARCH_HOST,
        opensearch_port: str = OPENSEARCH_PORT,
        opensearch_ssl_enabled: bool = OPENSEARCH_SSL_ENABLED,
        opensearch_user: str = OPENSEARCH_USER,
        opensearch_secret: str = OPENSEARCH_SECRET,
        auth_method: str = AUTH_METHOD,
        aws_access_key_id: str = AWS_ACCESS_KEY_ID,
        aws_secret_access_key: str = AWS_SECRET_ACCESS_KEY,
        aws_region: str = AWS_REGION,
        aws_service: str = AWS_SERVICE,
    ):

        """
        Init OsmanConfig

        Parameters
        ----------
        host_url: str
            a complete url of the OpenSearch instance, with schema/user/pass

        For the following attributes description see the class attributes above.
        NOTE: You have to provide either 'host_url' or 'auth_method' with aditional params

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

        # non empty host_url takes precedence over auth_method
        if host_url:
            logging.info("Using host_url: '%s'", host_url)
            self.host_url = host_url
            self.auth_method = "http"

            parsed_url = urllib.parse.urlparse(host_url)

            assert parsed_url.scheme in ["http", "https"]
            self.opensearch_ssl_enabled = parsed_url.scheme == "https"

            self.opensearch_host = parsed_url.hostname
            if not parsed_url.port:
                self.opensearch_port = (
                    80 if parsed_url.scheme == "http" else 443
                )
            else:
                self.opensearch_port = parsed_url.port

            self.opensearch_user = parsed_url.username
            self.opensearch_secret = parsed_url.password
            # All other parameters are ignored
            return

        assert auth_method in [
            "http",
            "user",
            "awsauth",
        ], "auth_method wrong or missing"

        assert opensearch_host
        assert opensearch_port
        assert isinstance(opensearch_port, int)
        assert isinstance(opensearch_ssl_enabled, bool)

        self.opensearch_host = opensearch_host
        self.opensearch_port = opensearch_port
        self.opensearch_ssl_enabled = opensearch_ssl_enabled

        if auth_method in ["http", "user"]:
            self.auth_method = "http"
            logging.info(
                "Using auth_method 'http' and '%s:%s'",
                opensearch_host,
                opensearch_port,
            )

            os_scheme = "https" if opensearch_ssl_enabled else "http"
            if not opensearch_user:
                self.host_url = (
                    f"{os_scheme}://{opensearch_host}:{opensearch_port}"
                )
                return

            assert opensearch_secret
            os_creds_user = urllib.parse.quote_plus(f"{opensearch_user}")
            os_creds_pass = urllib.parse.quote_plus(f"{opensearch_secret}")

            self.host_url = (
                f"{os_scheme}://{os_creds_user}:{os_creds_pass}"
                f"@{opensearch_host}:{opensearch_port}"
            )

            self.opensearch_user = opensearch_user
            self.opensearch_secret = opensearch_secret
            return

        # AWS auth method
        self.auth_method = "awsauth"
        logging.info(
            "Using auth_method 'awsauth' and '%s:%s'",
            opensearch_host,
            opensearch_port,
        )
        self.host_url = ""

        assert aws_access_key_id
        assert aws_secret_access_key
        assert aws_region
        assert aws_service

        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region
        self.aws_service = aws_service
        return

    def _reload_defaults_from_env(self):
        """
        Reload default values from environment values, used for testing purposes
        """
        logging.info("Reloading OsmanConfig from the environment")
        for variable in OSMAN_ENVIRONMENT_VARS:
            if variable in ["OPENSEARCH_PORT", "OPENSEARCH_SSL_ENABLED"]:
                continue
            self.__dict__[variable] = os.environ.get(
                variable, self.__class__.__dict__[variable]
            )

        self.OPENSEARCH_PORT = int(os.environ.get("OPENSEARCH_PORT", 443))
        self.OPENSEARCH_SSL_ENABLED = (
            os.environ.get("OPENSEARCH_SSL_ENABLED", "True") == "True"
        )

        # For backward compatibility we allow AWS_USER and AWS_SECRET variables
        self.OPENSEARCH_USER = os.environ.get(
            "OPENSEARCH_USER", os.environ.get("AWS_USER", self.OPENSEARCH_USER)
        )
        self.OPENSEARCH_SECRET = os.environ.get(
            "OPENSEARCH_SECRET",
            os.environ.get("AWS_SECRET", self.OPENSEARCH_SECRET),
        )

        init_params = {
            variable.lower(): self.__dict__[variable]
            for variable in OSMAN_ENVIRONMENT_VARS
        }

        self.__init__(**init_params)
