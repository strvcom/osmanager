from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import requests
import json
import urllib.parse

class OpenSearchTestHelper:
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
            self.client = OpenSearch(
                hosts=[os_url],
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection
            )
        else:
            self.awsauth = AWS4Auth(aws_access_key_id, aws_secret_access_key, aws_region, aws_service)
            self.client = OpenSearch(
                hosts = [{'host': host, 'port': 443}],
                http_auth = self.awsauth,
                use_ssl = True,
                verify_certs = True,
                connection_class = RequestsHttpConnection
            )
    
    def search_all(self, index, search_string, max_size=10):
        """
        Search the index for any field that contains search_string
        :param index: The name of the index
        :param search_string: Search query
        :param max_size: Maximal number of items to return, defaults to 10
        :return: Dictionary with response
        """
        query = {
            'size': max_size,
            'query': {
                'multi_match': {
                'query': search_string
                }
            }
        }

        response = self.client.search(
            body = query,
            index = index
        )
        return response
    
    def search(self, index, search_query):
        """
        Search the index with provided search query
        :param index: The name of the index
        :param search_string: Search query as dictionary {'query': {....}}
        :return: Dictionary with response
        """
        response = self.client.search(
            body = search_query,
            index = index
        )
        return response
    
    def get_document_by_id(self, index, document_id):
        """
        Returns document by provided ID or None if ID does not exist
        :param index: The name of the index
        :param document_id: ID of document
        :return: Dictionary with response
        """
        if self.client.exists(id = document_id, index = index):
            response = self.client.get(
                id = document_id,
                index = index
            )
            return response
        else:
            return None
    
    def create_document(self, index, document, id=None):
        return self.client.index(index=index, body=document, id=id)

    def create_index(self, index, mapping=None):
        return self.client.indices.create(index, body=mapping)

    def get_index(self, index):
        return self.client.indices.get(index=index)

    def delete_index(self, index):
        return self.client.indices.delete(index=index)

    def search_template(self, index, template):
        return self.client.search_template(template, index)

    def get_scripts(self):
        temp_state = self.client.cluster.state()
        return (
            temp_state
            .get('metadata', {})
            .get('stored_scripts', None)
        )
    
    def bulk(self, bulk_data):
        return self.client.bulk(bulk_data)
    
    def search_using_template(self, index_name, search_query):
        """
        Search in the index using existing template. Search quary should have 
        following sttructure:
        {
            "id": template_name,
            "params": {
                "param": value
            }
        }
        :param index_name: Name of the index in OpenSearch
        :param search_query: Search query for template containing the id of template
        :return: JSON with response
        """
        endpoint = f'https://{self.host}/{index_name}/_search/template'
        response = requests.get(endpoint, auth=self.awsauth, json=search_query)
        return response.json()

    def add_new_template(self, template, template_name):
        """
        Add new template to index
        :param template: JSON with new template
        :param template_name: Name of the template
        :return: JSON with response
        """
        return self.client.put_script(template_name, body=template)

    def update_post_with_view(self, index_name, post_id, user_id):
        """
        Add `user_id` to `penalty_consumed_item` and `seen_by` field in the OpenSearch document.
        :param index_name: Name of the index with documents
        :param post_id: Id of post that will receive new view
        :param user_id: Id of user that viewed the post
        :return: json with the response
        """
        query = {
            "query": {
                "term": {
                    "post_id": post_id
                }
            },
            "script" : {
                "source": """
                    ctx._source.penalty_consumed_item.addAll(params.penalty_consumed_item);
                    ctx._source.seen_by.addAll(params.seen_by);
                """,
                "lang": "painless",
                "params" : {
                    "penalty_consumed_item" : [user_id],
                    "seen_by" : [user_id]
                }
            }
        }

        response = self.client.update_by_query(index=index_name, body=query)
        return response
    
    def update_user_with_follower(self, index_name, user_id, follower_id):
        """
        Add follower with id `follower_id` to all posts from user with id `user_id`
        :param index_name: Name of the index with documents
        :param user_id: Id of user that will receive new follower
        :param follower_id: Id of new folower
        :return: Response JSON
        """

        query = {
            "query": {
                "term": {
                    "user_id": user_id
                }
            },
            "script" : {
                "source": "ctx._source.booster_following_profile.addAll(params.follower_id)",
                "lang": "painless",
                "params" : {
                    "follower_id" : [follower_id]
                }
            }
        }

        response = self.client.update_by_query(index=index_name, body=query)
        return response

    def change_post_to_competition(self, index_name, post_id):
        """
        Change `booster_competition` to True for post with id `post_id`
        :param index_name: Name of the index with documents
        :param post_id: Id of post to make competition
        :return: Response JSON
        """

        query = {
            "query": {
                "term": {
                    "post_id": post_id
                }
            },
            "script" : {
                "source": "ctx._source.booster_competition = params.booster_competition",
                "lang": "painless",
                "params" : {
                    "booster_competition" : True
                }
            }
        }

        response = self.client.update_by_query(index=index_name, body=query)
        return response

    def change_user_to_pro(self, index_name, user_id):
        """
        Change `booster_subscription` to True for all posts from user with id `user_id`
        :param index_name: Name of the index with documents
        :param user_id: Id of user that will be promoted to PRO
        :return: Response JSON
        """

        query = {
            "query": {
                "term": {
                    "user_id": user_id
                }
            },
            "script" : {
                "source": "ctx._source.booster_subscription = params.booster_subscription",
                "lang": "painless",
                "params" : {
                    "booster_subscription" : True
                }
            }
        }

        response = self.client.update_by_query(index=index_name, body=query)
        return response

    def change_post_negative_trending(self, index_name, post_id, new_negative_trending):
        """
        Change `penalty_negative_trending` to `new_negative_trending` for post with id `post_id`
        :param index_name: Name of the index with documents
        :param post_id: Id of post that will have penalty_negative_trending changed
        :param new_negative_trending: New value for penalty_negative_trending
        :return: Response JSON
        """

        query = {
            "query": {
                "term": {
                    "post_id": post_id
                }
            },
            "script" : {
                "source": "ctx._source.penalty_negative_trending = params.penalty_negative_trending",
                "lang": "painless",
                "params" : {
                    "penalty_negative_trending" : new_negative_trending
                }
            }
        }

        response = self.client.update_by_query(index=index_name, body=query)
        return response

    def change_post_old_trend_penalty(self, index_name, post_id, new_old_trend_penalty):
        """
        Change `penalty_old_trend` to `new_old_trend_penalty` for post with id `post_id`
        :param index_name: Name of the index with documents
        :param post_id: Id of post that will have penalty_old_trend changed
        :param new_old_trend_penalty: New value for penalty_old_trend
        :return: Response JSON
        """

        query = {
            "query": {
                "term": {
                    "post_id": post_id
                }
            },
            "script" : {
                "source": "ctx._source.penalty_old_trend = params.penalty_old_trend",
                "lang": "painless",
                "params" : {
                    "penalty_old_trend" : new_old_trend_penalty
                }
            }
        }

        response = self.client.update_by_query(index=index_name, body=query)
        return response

    def change_profile_attractivity_alltime_for_user(self, index_name, user_id, new_attractivity):
        """
        Change `booster_category_attractivity_alltime` to `new_attractivity` for user with id `user_id`
        :param index_name: Name of the index with documents
        :param user_id: Id of user that will have booster_category_attractivity_alltime changed
        :param new_attractivity: New value for booster_category_attractivity_alltime
        :return: Response JSON
        """

        query = {
            "query": {
                "term": {
                    "user_id": user_id
                }
            },
            "script" : {
                "source": "ctx._source.booster_category_attractivity_alltime = params.booster_category_attractivity_alltime",
                "lang": "painless",
                "params" : {
                    "booster_category_attractivity_alltime" : new_attractivity
                }
            }
        }

        response = self.client.update_by_query(index=index_name, body=query)
        return response

    def change_profile_attractivity_last_month_for_user(self, index_name, user_id, new_attractivity):
        """
        Change `booster_category_attractivity_last_month` to `new_attractivity` for user with id `user_id`
        :param index_name: Name of the index with documents
        :param user_id: Id of user that will have booster_category_attractivity_last_month changed
        :param new_attractivity: New value for booster_category_attractivity_last_month
        :return: Response JSON
        """

        query = {
            "query": {
                "term": {
                    "user_id": user_id
                }
            },
            "script" : {
                "source": "ctx._source.booster_category_attractivity_last_month = params.booster_category_attractivity_last_month",
                "lang": "painless",
                "params" : {
                    "booster_category_attractivity_last_month" : new_attractivity
                }
            }
        }

        response = self.client.update_by_query(index=index_name, body=query)
        return response

    def change_category_attractivity_alltime_for_post(self, index_name, post_id, new_attractivity):
        """
        Change `booster_category_attractivity_alltime` to `new_attractivity` for post with id `post_id`
        :param index_name: Name of the index with documents
        :param post_id: Id of post that will have booster_category_attractivity_alltime changed
        :param new_attractivity: New value for booster_category_attractivity_alltime
        :return: Response JSON
        """

        query = {
            "query": {
                "term": {
                    "post_id": post_id
                }
            },
            "script" : {
                "source": "ctx._source.booster_category_attractivity_alltime = params.booster_category_attractivity_alltime",
                "lang": "painless",
                "params" : {
                    "booster_category_attractivity_alltime" : new_attractivity
                }
            }
        }

        response = self.client.update_by_query(index=index_name, body=query)
        return response
    
    def change_category_attractivity_last_month_for_post(self, index_name, post_id, new_attractivity):
        """
        Change `booster_category_attractivity_last_month` to `new_attractivity` for post with id `post_id`
        :param index_name: Name of the index with documents
        :param post_id: Id of post that will have booster_category_attractivity_last_month changed
        :param new_attractivity: New value for booster_category_attractivity_last_month
        :return: Response JSON
        """

        query = {
            "query": {
                "term": {
                    "post_id": post_id
                }
            },
            "script" : {
                "source": "ctx._source.booster_category_attractivity_last_month = params.booster_category_attractivity_last_month",
                "lang": "painless",
                "params" : {
                    "booster_category_attractivity_last_month" : new_attractivity
                }
            }
        }

        response = self.client.update_by_query(index=index_name, body=query)
        return response

    def change_profile_arrogance_alltime_for_user(self, index_name, user_id, new_arrogance):
        """
        Change `penalty_profile_arrogance_alltime` to `new_arrogance` for user with id `user_id`
        :param index_name: Name of the index with documents
        :param user_id: Id of user that will have penalty_profile_arrogance_alltime changed
        :param new_arrogance: New value for penalty_profile_arrogance_alltime
        :return: Response JSON
        """

        query = {
            "query": {
                "term": {
                    "user_id": user_id
                }
            },
            "script" : {
                "source": "ctx._source.penalty_profile_arrogance_alltime = params.penalty_profile_arrogance_alltime",
                "lang": "painless",
                "params" : {
                    "penalty_profile_arrogance_alltime" : new_arrogance
                }
            }
        }

        response = self.client.update_by_query(index=index_name, body=query)
        return response

    def change_profile_arrogance_last_month_for_user(self, index_name, user_id, new_arrogance):
        """
        Change `penalty_profile_arrogance_last_month` to `new_arrogance` for user with id `user_id`
        :param index_name: Name of the index with documents
        :param user_id: Id of user that will have penalty_profile_arrogance_last_month changed
        :param new_arrogance: New value for penalty_profile_arrogance_last_month
        :return: Response JSON
        """

        query = {
            "query": {
                "term": {
                    "user_id": user_id
                }
            },
            "script" : {
                "source": "ctx._source.penalty_profile_arrogance_last_month = params.penalty_profile_arrogance_last_month",
                "lang": "painless",
                "params" : {
                    "penalty_profile_arrogance_last_month" : new_arrogance
                }
            }
        }

        response = self.client.update_by_query(index=index_name, body=query)
        return response

    def change_category_arrogance_alltime_for_post(self, index_name, post_id, new_arrogance):
        """
        Change `penalty_category_arrogance_alltime` to `new_arrogance` for post with id `post_id`
        :param index_name: Name of the index with documents
        :param post_id: Id of post that will have penalty_category_arrogance_alltime changed
        :param new_arrogance: New value for penalty_category_arrogance_alltime
        :return: Response JSON
        """

        query = {
            "query": {
                "term": {
                    "post_id": post_id
                }
            },
            "script" : {
                "source": "ctx._source.penalty_category_arrogance_alltime = params.penalty_category_arrogance_alltime",
                "lang": "painless",
                "params" : {
                    "penalty_category_arrogance_alltime" : new_arrogance
                }
            }
        }

        response = self.client.update_by_query(index=index_name, body=query)
        return response
    
    def change_category_arrogance_last_month_for_post(self, index_name, post_id, new_arrogance):
        """
        Change `penalty_category_arrogance_last_month` to `new_arrogance` for post with id `post_id`
        :param index_name: Name of the index with documents
        :param post_id: Id of post that will have penalty_category_arrogance_last_month changed
        :param new_arrogance: New value for penalty_category_arrogance_last_month
        :return: Response JSON
        """

        query = {
            "query": {
                "term": {
                    "post_id": post_id
                }
            },
            "script" : {
                "source": "ctx._source.penalty_category_arrogance_last_month = params.penalty_category_arrogance_last_month",
                "lang": "painless",
                "params" : {
                    "penalty_category_arrogance_last_month" : new_arrogance
                }
            }
        }

        response = self.client.update_by_query(index=index_name, body=query)
        return response

    def change_post_trending(self, index_name, post_id, new_trendiness):
        """
        Change `booster_trending` to `new_trendiness` for post with id `post_id`
        :param index_name: Name of the index with documents
        :param post_id: Id of post that will have booster_trending changed
        :param new_trendiness: New value for booster_trending
        :return: Response JSON
        """

        query = {
            "query": {
                "term": {
                    "post_id": post_id
                }
            },
            "script" : {
                "source": "ctx._source.booster_trending = params.booster_trending",
                "lang": "painless",
                "params" : {
                    "booster_trending" : new_trendiness
                }
            }
        }

        response = self.client.update_by_query(index=index_name, body=query)
        return response
