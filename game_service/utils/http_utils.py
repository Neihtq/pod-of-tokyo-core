import requests


def join(base_url, endpoint):
    return f"{base_url.rstrip('/')}/{endpoint}"


def get(url, resource_id):
    return requests.get(join(url, resource_id))


def post(base_url, endpoint, payload=None):
    if payload is None:
        payload = {}
    return requests.post(join(base_url, endpoint), json=payload).json()


def put(url, payload):
    return requests.put(url, json=payload)


def delete(url):
    return requests.delete(url)
