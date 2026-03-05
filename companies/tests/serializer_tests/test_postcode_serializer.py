import pytest
from companies.serializers.postcode_serializer import PostcodeSerializer
from companies.tests.factories import PostcodeFactory


@pytest.mark.django_db
class TestPostcodeSerializer:
    def test_contains_expected_fields(self):
        postcode = PostcodeFactory()
        serializer = PostcodeSerializer(postcode)
        assert set(serializer.data.keys()) == {'postcode', 'latitude', 'longitude', 'state'}

    def test_postcode_field_value(self):
        postcode = PostcodeFactory(postcode='6000', state='WA')
        serializer = PostcodeSerializer(postcode)
        assert serializer.data['postcode'] == '6000'
        assert serializer.data['state'] == 'WA'
