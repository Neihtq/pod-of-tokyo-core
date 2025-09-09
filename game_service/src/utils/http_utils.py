import requests


def join(base_url, endpoint):
    return f"{base_url}/{endpoint}"


def get(url, resource_id):
    return requests.get(join(url, resource_id))


def post(url, payload):
    return requests.post(url, json=payload)


def put(url, payload):
    return requests.put(url, json=payload)


def delete(url):
    return requests.delete(url)
