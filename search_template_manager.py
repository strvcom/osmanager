import click
from dotenv import load_dotenv
import json
import os
import sys
import yaml

from opensearchpy import OpenSearch

# load env variables
load_dotenv()

# add python path to main repo folder: https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # get current file path and it's folder
SCRIPT_DIR_ABOVE = os.path.dirname(SCRIPT_DIR) # get folder above
SCRIPT_DIR_TWO_ABOVE = os.path.dirname(SCRIPT_DIR_ABOVE) # get folder above
sys.path.append(SCRIPT_DIR_TWO_ABOVE) # append to paths with scripts repo folder

# import module testing from newly python path added above
from utils import get_opensearch_helper
from configuration import Configuration

def convert_template_source(source_path):
    """Load source file, convert to string.

    Args:
        source_path (os.path): path to json with source for template

    Returns:
        str: source without newlines and with escaped quotechars
    """
    with open(source_path) as file:
        return ''.join([
            line.strip().replace(' ', '') for line in file.readlines()
        ])

def create_template_query(search_template_source_path, search_params):
    """ Creates json with full query for template

    Args:
        search_template_source (_type_): source as defined for the templae
        search_params (_type_): parameters to be used in query

    Returns:
        json: full template query
    """
    # compile full template
    template_query = {
        "source": convert_template_source(search_template_source_path),
        "params": search_params
    }
    template_query_json = json.dumps(template_query)
    return template_query_json

def create_template_script(search_template_source_path):
    """ Creates json with full script for template

    Args:
        search_template_source (_type_): source as defined for the templae

    Returns:
        json: full template query
    """
    # compile full template
    template_script = {
        "script": {
            "lang": "mustache",
            "source": convert_template_source(search_template_source_path)
        }
    }
    template_script_json = json.dumps(template_script)
    return template_script #_json

def run_search_with_template(index_name, search_template_source_path, search_params, config=Configuration):
    """Runs template against given index and return search results

    Args:
        index_name (_type_): name of the index to run against
        search_template_source (_type_): string with source of the template
        search_params: dict of parameters to use
        config: config object with specified aws connection

    Returns:
        json: search results
    """
    # Get template query
    template_query_json = create_template_query(search_template_source_path, search_params)
    # Get instance of OpenSearchHelper connected to OpenSearch
    os_helper = get_opensearch_helper(config)
    # Check that template is in OpenSearch without errors
    result = os_helper.search_template(index_name, template_query_json)
    return result

def get_current_search_templates(config=Configuration):
    """_summary_

    Args:
        config (_type_, optional): _description_. Defaults to Configuration.
    """
    # Get instance of OpenSearchHelper connected to OpenSearch
    os_helper = get_opensearch_helper(config)
    return os_helper.get_scripts()

def upload_template(template_name, search_template_source_path, config=Configuration):
    """ Uploads template to the opensearch engine

    Args:
        template_name (_type_): _description_
        search_template_source_path (_type_): _description_
        search_params (_type_): _description_
        config (_type_, optional): _description_. Defaults to Configuration.

    Returns:
        _type_: _description_
    """
    # Get template query
    template_query_json = create_template_script(search_template_source_path)
    # Create connction and upload template
    os_helper = get_opensearch_helper(config)
    upload_response = os_helper.add_new_template(template_query_json, template_name)
    return upload_response

def get_env_var_values(env: str) -> tuple:
    """ Provide names for env vars for local or aws env

    Args:
        env (str): env for which os is going to be created

    Returns:
        tuple: environment variable values
    """
    dbt_schema = os.environ.get('DBT_SNOWFLAKE_SCHEMA', None)

    if dbt_schema.split('_')[-1] == 'aws':
        os_host_env = 'OPENSEARCH_HOST'
        os_user_env = 'OPENSEARCH_USERNAME'
        os_pass_env = 'OPENSEARCH_PASSWORD'
    else:
        env = env.upper()
        os_host_env = f'{env}_OPENSEARCH_HOST'
        os_user_env = f'{env}_OPENSEARCH_USERNAME'
        os_pass_env = f'{env}_OPENSEARCH_PASSWORD'


    return (
        os.environ.get(os_host_env, None),
        os.environ.get(os_user_env, None),
        os.environ.get(os_pass_env, None),
    )
def prepare_env_config(env):
    """ Prepares specific env and loads credentials from env vars

    Args:
        env (string): name of the destination env

    Returns:
        config: configuration object
    """
    curr_config = Configuration
    # set up config for opensearch
    curr_config.AUTH_METHOD = 'user'
    (
        curr_config.OPENSEARCH_HOST, 
        curr_config.AWS_USER,
        curr_config.AWS_SECRET
    ) = get_env_var_values(env)
    return curr_config

def load_templates(template_filename):
    """ Load templates from given yaml file in the current folder

    Args:
        template_filename (_type_): _description_
    """
    YAML_TEMPLATES_PATH = os.path.join(
        os.path.dirname(__file__), 
        template_filename
    )
    with open(YAML_TEMPLATES_PATH, 'r') as file:
        defined_tempates = yaml.safe_load(file).get('templates')
    return defined_tempates

def use_template_to_search(search_env, search_template, search_params, search_config):
    """ Searches against index in env using tempalate with provided parameters

    Args:
        search_env (_type_): _description_
        search_template (_type_): json from yaml loaded
        search_params (_type_): _description_
        search_config (_type_): _description_
    """
    return run_search_with_template(
        search_env + '-' + search_template['index'],
        './' + search_template['filepath'],
        search_params,
        search_config
    )


def compare_search_templates(template_name, defined_templates, opensearch_templates):
    """ Compares template source definition between file and what is uploaded to opensearch

    Args:
        template_name (_type_): name of the current template
        defined_templates (_type_): json with all templates from yaml file
        opensearch_templates (_type_): json with all templates available on opensearch service
    """
    template_compare_result = False

    if opensearch_templates is None:
        # print('OpenSearch %s: Template %s is missing.' % (env, search_template['name']))
        return {
            'message': 'No opensearch templates available', 
            'is_up_to_date': template_compare_result,
            'os_source': '',
            'local_source': ''
        }
    
    if defined_templates is None:
        return {
            'message': 'No defined templates available', 
            'is_up_to_date': template_compare_result,
            'os_source': '',
            'local_source': ''
        }

    opensearch_templates_names = list(opensearch_templates.keys())
    defined_templates_names = [template['name'] for template in defined_templates]

    if template_name not in opensearch_templates_names:
        return {
            'message': f'Template {template_name} is not in opensearch', 
            'is_up_to_date': template_compare_result,
            'os_source': '',
            'local_source': ''
        }

    if template_name not in defined_templates_names:
        return {
            'message': f'Template {template_name} is not in yaml definitions', 
            'is_up_to_date': template_compare_result,
            'os_source': '',
            'local_source': ''
        }

    # prepare template sources to compare
    opensearch_template_source = opensearch_templates.get(template_name, None).get('source').replace(' ','')
    defined_template = [defined_template for defined_template in defined_templates if defined_template['name'] == template_name][0]
    defined_template_source = convert_template_source('./' + defined_template['filepath'])

    if defined_template_source == opensearch_template_source:
        template_compare_result = True
        return {
            'message': f'Template {template_name} is up to date.', 
            'is_up_to_date': template_compare_result,
            'os_source': opensearch_template_source,
            'local_source': defined_template_source
        }
    else:
        return {
            'message': f'Template {template_name} is different.', 
            'is_up_to_date': template_compare_result,
            'os_source': opensearch_template_source,
            'local_source': defined_template_source
        }
    
    return {
        'message': f'Template {template_name} was not compared.', 
        'is_up_to_date': template_compare_result
    }

def get_template_search_result(defined_template, use_params, search_env, current_env_config):
    """ Get search results and provide result json

    Args:
        defined_template (_type_): _description_
        use_params (_type_): _description_
        search_env (_type_): _description_
        current_env_config (_type_): _description_

    Returns:
        _type_: _description_
    """
    current_params = defined_template['parameters'][search_env] if use_params else {}
    search_results = use_template_to_search(search_env, defined_template, current_params, current_env_config)
    search_results_hits = search_results['hits']['total']['value']

    return {
        'template_definition': defined_template,
        'hits': search_results_hits
    }

@click.command()
@click.option('--env', type=click.Choice(['dev', 'staging', 'beta', 'prod'], case_sensitive=False), required=True, help='AWS Environment in which to manage templates.')
@click.option('--write/--read', default=False, help='Template upload mode.')
@click.option('--search-params/--search-all', default=True, help='Ignore search parameters.')
@click.option('--template', default='all', help='Select speficic template.')
def manage_templates(env, write, search_params, template):
    """ 
    Manages search templates in opensearch client
    OpenSearch is accessed via user/pass authentication that should be in env vars:

    {env}_OPENSEARCH_HOST - url without protocol and post
    {env}_OPENSEARCH_USERNAME - admin user
    {env}_OPENSEARCH_PASSWORD - admin user password

    """
    # set cli options
    template_override = write
    current_env_config = prepare_env_config(env)
    # load template yaml config
    defined_templates = load_templates('shwdwn_templates.yml')
    # get current scripts
    search_scripts = get_current_search_templates(current_env_config)

    # limit templates
    if template == 'all':
        selected_templates = defined_templates
    else:
        selected_templates = [defined_template for defined_template in defined_templates if defined_template['name'] == template]
    
    if len(selected_templates) > 0:
        defined_templates = selected_templates
    else:
        print('Wrong template name provided.')
        return

    # run for loop to get results
    template_search_results = {}
    for defined_template in defined_templates:
        template_search_results[defined_template['name']] = get_template_search_result(defined_template, search_params, env, current_env_config)
    
    # run for loop to manage templates
    for template_name, template_result in  template_search_results.items():
        uploaded = False
        # Manage search results
        if template_result['hits'] > 0:
            selected_compare_result = compare_search_templates(template_name, defined_templates, search_scripts)
        if template_result['hits'] == 0:
            print('OpenSearch %s: No results returned for template %s. Check parameters below.' % (env, template_name))
            print('---')
            print(template_result['template_definition']['parameters'][env])
            print('---')
            continue

        # Manage template definition
        if selected_compare_result['is_up_to_date']:
            print('OpenSearch %s: Template %s in opensearch is up to date.' % (env, template_name))
            continue

        # Manage new version
        if template_override:
            upload_result = upload_template(template_name,template_result['template_definition']['filepath'],current_env_config)
            uploaded = True
        if not template_override:
            print('OpenSearch %s: Template %s in opensearch is different. See the differences below.' % (env, template_name))
            print('OpenSearch %s: Template %s source in opensearch:' % (env, template_name))
            print('---')
            print(selected_compare_result['os_source'])
            print('---')
            print('OpenSearch %s: Template %s source in local folder:' % (env, template_name))
            print('---')
            print(selected_compare_result['local_source'])
            print('---')
            continue

        # Manage upload status
        if uploaded and upload_result['acknowledged']:
            print('OpenSearch %s: Template %s uploaded.' % (env, template_name))
        elif uploaded:
            print('OpenSearch %s: Template %s upload failed, check response below.' % (env, template_name))
            print('---')
            print(upload_result)
            print('---')
    return search_scripts

if __name__ == '__main__':
    manage_templates()