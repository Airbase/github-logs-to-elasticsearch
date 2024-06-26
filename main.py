import os
import requests
import json

def get_workflow_logs(github_token, repo, run_id):
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    logs_url = f'https://api.github.com/repos/{repo}/actions/runs/{run_id}/logs'
    response = requests.get(logs_url, headers=headers)
    response.raise_for_status()
    return response.content

def push_to_elasticsearch(elasticsearch_url, index, logs, api_key_id, api_key):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'ApiKey {base64.b64encode(f"{api_key_id}:{api_key}".encode()).decode()}'
    }
    # Decode logs from Base64 to plain text
    decoded_logs = logs.decode('utf-8', errors='ignore')
    data = {
        "logs": decoded_logs
    }
    response = requests.post(f'{elasticsearch_url}/{index}/_doc', headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    elasticsearch_url = os.getenv('INPUT_ELASTICSEARCH_URL')
    elasticsearch_index = os.getenv('INPUT_ELASTICSEARCH_INDEX')
    elasticsearch_api_key_id = os.getenv('INPUT_ELASTICSEARCH_API_KEY_ID')
    elasticsearch_api_key = os.getenv('INPUT_ELASTICSEARCH_API_KEY')
    github_token = os.getenv('INPUT_GITHUB_TOKEN')
    github_repository = os.getenv('GITHUB_REPOSITORY')
    github_run_id = os.getenv('GITHUB_RUN_ID')

    try:
        logs = get_workflow_logs(github_token, github_repository, github_run_id)
        response = push_to_elasticsearch(elasticsearch_url, elasticsearch_index, logs, elasticsearch_api_key_id, elasticsearch_api_key)
        print(f'Successfully pushed logs to Elasticsearch: {response}')
    except Exception as e:
        print(f'Error: {e}')
        exit(1)
