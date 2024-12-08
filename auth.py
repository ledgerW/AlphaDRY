import os

def check_api_key(api_key: str):
    return api_key == os.environ.get("API_KEY")
