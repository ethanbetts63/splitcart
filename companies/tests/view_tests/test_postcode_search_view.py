import pytest
from django.urls import reverse
from companies.tests.factories import PostcodeFactory


@pytest.fixture(autouse=True)
def disable_cache(settings):
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}


@pytest.mark.django_db
class TestPostcodeSearchView:
    def test_returns_postcode_data_when_found(self, client):
        PostcodeFactory(postcode='6000', state='WA')
        response = client.get(reverse('postcode-search'), {'postcode': '6000'})
        assert response.status_code == 200
        data = response.json()
        assert data['postcode'] == '6000'
        assert data['state'] == 'WA'

    def test_response_contains_expected_fields(self, client):
        PostcodeFactory(postcode='2000')
        response = client.get(reverse('postcode-search'), {'postcode': '2000'})
        assert response.status_code == 200
        assert set(response.json().keys()) == {'postcode', 'latitude', 'longitude', 'state'}

    def test_returns_404_when_postcode_not_found(self, client):
        response = client.get(reverse('postcode-search'), {'postcode': '9999'})
        assert response.status_code == 404

    def test_returns_404_when_no_postcode_param_provided(self, client):
        response = client.get(reverse('postcode-search'))
        assert response.status_code == 404

    def test_exact_match_only(self, client):
        PostcodeFactory(postcode='6000')
        PostcodeFactory(postcode='6001')
        response = client.get(reverse('postcode-search'), {'postcode': '600'})
        assert response.status_code == 404
