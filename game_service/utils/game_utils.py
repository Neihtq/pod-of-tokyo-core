from pod_of_tokyo_commons.model import Location

WINNING_CONDITION = 20


def is_in_tokyo(location_data: dict, location_key=None, location=None):
    tokyo_locations = {Location.CITY, Location.BAY}
    if location_key:
        return location_data[location_key] in tokyo_locations

    return location in tokyo_locations
