from pod_of_tokyo_commons.model import Location

from game_service.utils.game_utils import is_in_tokyo


def test_location_key_is_in_tokyo():
    location_key = "someLocation"
    location_data = {location_key: Location.CITY}

    assert is_in_tokyo(location_data=location_data, location_key=location_key)


def test_location_is_in_tokyo():
    location = Location.CITY
    location_data = {"someLocation": location}

    assert is_in_tokyo(location_data=location_data, location=location)


def test_location_key_is_not_in_tokyo():
    location_key = "someLocation"
    location_data = {location_key: Location.OUTSIDE}

    assert not is_in_tokyo(location_data=location_data, location_key=location_key)


def test_location_is_not_in_tokyo():
    location = Location.OUTSIDE
    location_data = {"someLocation": location}

    assert not is_in_tokyo(location_data=location_data, location=location)


def test_is_not_in_tokyo_for_no_argument():
    assert not is_in_tokyo(location_data={})
