import requests


def get(url):
    response = requests.get(url)
    return response.json()


def post(url, payload):
    return requests.post(url, json=payload)


def put(url, payload):
    return requests.put(url, json=payload)


def delete(url):
    return requests.delete(url)
