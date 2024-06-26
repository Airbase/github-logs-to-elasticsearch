import os
import requests
import json
import base64
import zipfile
import io

def get_workflow_logs(github_token, repo, run_id):
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    logs_url = f'https://api.github.com/repos/{repo}/actions/runs/{run_id}/logs'
    response = requests.get(logs_url, headers=headers)
    response.raise_for_status()
    return response.content

def extract_logs(logs):
    log_text = ""
    with zipfile.ZipFile(io.BytesIO(logs)) as z:
        for log_file in z.namelist():
            with z.open(log_file) as f:
                log_text += f.read().decode('utf-8', errors='ignore') + "\n"
    return log_text

def push_to_elasticsearch(elasticsearch_url, index, logs, api_key_id, api_key):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'ApiKey {base64.b64encode(f"{api_key_id}:{api_key}".encode()).decode()}'
    }
    data = {
        "logs": logs
    }
    response = requests.post(f'{elasticsearch_url}/{index}/_doc', headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    elasticsearch_url = os.getenv('ELASTICSEARCH_URL')
    elasticsearch_index = os.getenv('ELASTICSEARCH_INDEX')
    elasticsearch_api_key_id = os.getenv('ELASTICSEARCH_API_KEY_ID')
    elasticsearch_api_key = os.getenv('ELASTICSEARCH_API_KEY')
    github_token = os.getenv('GITHUB_TOKEN')
    github_repository = os.getenv('GITHUB_REPOSITORY')
    github_run_id = os.getenv('GITHUB_RUN_ID')
    github_pr_number = os.getenv('GITHUB_PR_NUMBER')

    print(f"Elasticsearch URL: {elasticsearch_url}")
    print(f"Elasticsearch Index: {elasticsearch_index}")
    print(f"GitHub Repository: {github_repository}")
    print(f"GitHub Run ID: {github_run_id}")

    try:
        logs = get_workflow_logs(github_token, github_repository, github_run_id)
        logs_text = extract_logs(logs)
        response = push_to_elasticsearch(elasticsearch_url, elasticsearch_index, logs_text, elasticsearch_api_key_id, elasticsearch_api_key)
        print(f'Successfully pushed logs to Elasticsearch: {response}')
    except Exception as e:
        print(f'Error: {e}')
        exit(1)
