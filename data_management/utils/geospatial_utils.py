import math
from django.db.models import Q
from companies.models import Postcode, Store

# Radius of Earth in kilometers
EARTH_RADIUS_KM = 6371

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on Earth using the Haversine formula.
    Latitudes and longitudes are given in decimal degrees.
    Returns distance in kilometers.
    """
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = EARTH_RADIUS_KM * c
    return distance

def get_nearby_postcodes(ref_postcode_obj: Postcode, radius_km: float) -> list[Postcode]:
    """
    Finds all Postcode objects within a given radius of a reference Postcode.
    """
    nearby_postcodes = []
    all_postcodes = Postcode.objects.all()

    for postcode in all_postcodes:
        if postcode.postcode == ref_postcode_obj.postcode:
            nearby_postcodes.append(postcode)
            continue

        distance = haversine_distance(
            ref_postcode_obj.latitude, ref_postcode_obj.longitude,
            postcode.latitude, postcode.longitude
        )
        if distance <= radius_km:
            nearby_postcodes.append(postcode)
    return nearby_postcodes

def get_nearby_stores(ref_postcode_obj: Postcode, radius_km: float, companies: list[str] | None = None) -> list[Store]:
    """
    Finds all Store objects within a given radius of a reference Postcode.
    Optionally filters by a list of company names.
    """
    nearby_stores = []
    # Exclude specific divisions
    excluded_division_ids = [2, 3, 5, 7]
    all_stores = Store.objects.exclude(division_id__in=excluded_division_ids)

    # Only include IGA stores that have been scraped at least once
    all_stores = all_stores.filter(
        Q(company__name__iexact='IGA', last_scraped__isnull=False) | 
        ~Q(company__name__iexact='IGA')
    )

    # Filter by company if a list of company names is provided
    if companies:
        all_stores = all_stores.filter(company__name__in=companies)

    for store in all_stores:
        if store.latitude is None or store.longitude is None:
            continue # Skip stores with missing coordinates

        distance = haversine_distance(
            ref_postcode_obj.latitude, ref_postcode_obj.longitude,
            store.latitude, store.longitude
        )
        if distance <= radius_km:
            nearby_stores.append(store)
    return nearby_stores
