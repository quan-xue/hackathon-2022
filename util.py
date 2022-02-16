from typing import Tuple
import re

from geopy.geocoders import Nominatim
import requests

def is_valid_postal(postal_code: str) -> bool:
    pattern = re.compile("^\d{6}$")
    match_pattern = bool(pattern.match(postal_code))
    if not match_pattern:
        return False
    else:
        return True

def search_postal(postal_code: str) -> Tuple[str, float, float]:
    """
    :param postal_code:
    :return: addr, lat, lng
    """
    query = {'searchVal': postal_code, 'returnGeom': 'Y', 'getAddrDetails':'Y'}
    api = 'https://developers.onemap.sg/commonapi/search'
    response = requests.get(api, params=query)
    results = response.json()['results']
    if not results:
        return None
    
    result = results[0]
    return {
        'address': result['ADDRESS'].title(),
        'latitude': result['LATITUDE'],
        'longitude': result['LONGITUDE']
    }

def reverse_geocode(lat, lon):
    locator = Nominatim(user_agent="kaypohBotGeocoder")
    location = locator.reverse([lat, lon])
    postcode = location.raw['address']['postcode']
    return search_postal(postcode)
