from pod_of_tokyo_commons.utils import http_utils as http


def update_monster_location(url, location):
    return http.post(
        base_url=url, endpoint="updateLocation", payload={"location": location}
    )
