from osman.osman_connector.configuration import Configuration

from .osman_connector import OsmanConnector

def get_OsmanConnector(config=Configuration):
    """
    Creates instance of OpenSearchHelper with credentials from testing Configuration or from provided one
    """
    return OsmanConnector(
            config.OPENSEARCH_HOST, 
            config.AWS_ACCESS_KEY_ID, 
            config.AWS_SECRET_ACCESS_KEY,
            config.AWS_REGION,
            config.AWS_SERVICE,
            config.AUTH_METHOD,
            config.AWS_USER,
            config.AWS_SECRET
        )