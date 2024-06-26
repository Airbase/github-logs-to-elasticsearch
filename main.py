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
    print(f"Fetching logs from URL: {logs_url}")  # Debugging statement
    response = requests.get(logs_url, headers=headers)
    if response.status_code == 401:
        raise Exception("Unauthorized. Please check your GitHub token permissions.")
    if response.status_code == 404:
        raise Exception(f"Logs not found for run_id {run_id}. Please check if the run_id is correct and the workflow run exists.")
    response.raise_for_status()
    return response.content

def extract_logs(logs):
    log_text = ""
    with zipfile.ZipFile(io.BytesIO(logs)) as z:
        for log_file in z.namelist():
            with z.open(log_file) as f:
                log_text += f.read().decode('utf-8', errors='ignore') + "\n"
    return log_text

def push_to_elasticsearch(elasticsearch_url, index, logs, metadata, api_key_id, api_key):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'ApiKey {base64.b64encode(f"{api_key_id}:{api_key}".encode()).decode()}'
    }
    data = {
        "logs": logs,
        "metadata": metadata
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
    github_repository = os.getenv('INPUT_GITHUB_REPOSITORY')
    github_run_id = os.getenv('INPUT_GITHUB_RUN_ID')
    github_pr_number = os.getenv('INPUT_GITHUB_PR_NUMBER')

    print(f"Elasticsearch URL: {elasticsearch_url}")  # Debugging statement
    print(f"Elasticsearch Index: {elasticsearch_index}")  # Debugging statement
    print(f"GitHub Repository: {github_repository}")  # Debugging statement
    print(f"GitHub Run ID: {github_run_id}")  # Debugging statement

    metadata = {
        "pr_number": github_pr_number,
        "run_id": github_run_id,
        "repository": github_repository,
        "workflow": os.getenv('GITHUB_WORKFLOW'),
        "actor": os.getenv('GITHUB_ACTOR'),
        "event_name": os.getenv('GITHUB_EVENT_NAME'),
        "sha": os.getenv('GITHUB_SHA'),
        "ref": os.getenv('GITHUB_REF'),
        "pr_title": os.getenv('GITHUB_PR_TITLE')
    }

    try:
        logs = get_workflow_logs(github_token, github_repository, github_run_id)
        logs_text = extract_logs(logs)
        response = push_to_elasticsearch(elasticsearch_url, elasticsearch_index, logs_text, metadata, elasticsearch_api_key_id, elasticsearch_api_key)
        print(f'Successfully pushed logs to Elasticsearch: {response}')
    except Exception as e:
        print(f'Error: {e}')
        exit(1)
