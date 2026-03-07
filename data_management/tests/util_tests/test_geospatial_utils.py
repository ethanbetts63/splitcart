import pytest
from data_management.utils.geospatial_utils import haversine_distance, get_nearby_postcodes, get_nearby_stores
from companies.tests.factories import PostcodeFactory, StoreFactory, CompanyFactory


class TestHaversineDistance:
    def test_same_point_is_zero(self):
        assert haversine_distance(0, 0, 0, 0) == 0

    def test_sydney_to_melbourne_approx_714km(self):
        # Sydney: -33.8688, 151.2093  Melbourne: -37.8136, 144.9631
        distance = haversine_distance(-33.8688, 151.2093, -37.8136, 144.9631)
        assert 710 < distance < 720

    def test_is_symmetric(self):
        d1 = haversine_distance(-33.8688, 151.2093, -37.8136, 144.9631)
        d2 = haversine_distance(-37.8136, 144.9631, -33.8688, 151.2093)
        assert abs(d1 - d2) < 0.001

    def test_short_distance(self):
        # Two points ~1km apart
        distance = haversine_distance(-33.8688, 151.2093, -33.8778, 151.2093)
        assert 0.5 < distance < 2.0

    def test_returns_kilometers(self):
        # ~1 degree of latitude is ~111km
        distance = haversine_distance(0, 0, 1, 0)
        assert 110 < distance < 112


@pytest.mark.django_db
class TestGetNearbyPostcodes:
    def test_always_includes_reference_postcode(self):
        ref = PostcodeFactory(postcode='2000', latitude=-33.8688, longitude=151.2093)
        result = get_nearby_postcodes(ref, radius_km=1)
        assert ref in result

    def test_includes_close_postcode(self):
        ref = PostcodeFactory(postcode='2000', latitude=-33.8688, longitude=151.2093)
        close = PostcodeFactory(postcode='2001', latitude=-33.8690, longitude=151.2090)
        result = get_nearby_postcodes(ref, radius_km=5)
        assert close in result

    def test_excludes_distant_postcode(self):
        ref = PostcodeFactory(postcode='2000', latitude=-33.8688, longitude=151.2093)
        far = PostcodeFactory(postcode='3000', latitude=-37.8136, longitude=144.9631)
        result = get_nearby_postcodes(ref, radius_km=10)
        assert far not in result

    def test_returns_list(self):
        ref = PostcodeFactory(postcode='2100', latitude=-33.8688, longitude=151.2093)
        result = get_nearby_postcodes(ref, radius_km=5)
        assert isinstance(result, list)


@pytest.mark.django_db
class TestGetNearbyStores:
    def test_includes_store_within_radius(self):
        ref = PostcodeFactory(postcode='2200', latitude=-33.8688, longitude=151.2093)
        store = StoreFactory(latitude=-33.8700, longitude=151.2090)
        result = get_nearby_stores(ref, radius_km=5)
        assert store in result

    def test_excludes_store_outside_radius(self):
        ref = PostcodeFactory(postcode='2300', latitude=-33.8688, longitude=151.2093)
        far_store = StoreFactory(latitude=-37.8136, longitude=144.9631)
        result = get_nearby_stores(ref, radius_km=10)
        assert far_store not in result

    def test_excludes_stores_with_no_coordinates(self):
        ref = PostcodeFactory(postcode='2400', latitude=-33.8688, longitude=151.2093)
        store = StoreFactory(latitude=None, longitude=None)
        result = get_nearby_stores(ref, radius_km=1000)
        assert store not in result

    def test_filters_by_company_name(self):
        ref = PostcodeFactory(postcode='2500', latitude=-33.8688, longitude=151.2093)
        coles = CompanyFactory(name='Coles')
        woolies = CompanyFactory(name='Woolworths')
        coles_store = StoreFactory(company=coles, latitude=-33.8700, longitude=151.2090)
        woolies_store = StoreFactory(company=woolies, latitude=-33.8700, longitude=151.2090)
        result = get_nearby_stores(ref, radius_km=5, companies=['Coles'])
        assert coles_store in result
        assert woolies_store not in result

    def test_excludes_iga_store_never_scraped(self):
        ref = PostcodeFactory(postcode='2600', latitude=-33.8688, longitude=151.2093)
        iga = CompanyFactory(name='IGA')
        iga_store = StoreFactory(company=iga, latitude=-33.8700, longitude=151.2090, last_scraped=None)
        result = get_nearby_stores(ref, radius_km=5)
        assert iga_store not in result
