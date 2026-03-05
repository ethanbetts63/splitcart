import pytest
from django.db import IntegrityError
from companies.models import Postcode
from companies.tests.factories import PostcodeFactory


@pytest.mark.django_db
class TestPostcodeModel:
    def test_str_contains_postcode_and_state(self):
        postcode = PostcodeFactory(postcode='6000', state='WA')
        result = str(postcode)
        assert '6000' in result
        assert 'WA' in result

    def test_str_contains_coordinates(self):
        postcode = Postcode.objects.create(
            postcode='2000', state='NSW', latitude='-33.868800', longitude='151.209300'
        )
        result = str(postcode)
        assert '-33.868800' in result or '-33.8688' in result

    def test_postcode_uniqueness_enforced(self):
        Postcode.objects.create(postcode='3000', state='VIC', latitude='-37.814000', longitude='144.963000')
        with pytest.raises(IntegrityError):
            Postcode.objects.create(postcode='3000', state='VIC', latitude='-37.814000', longitude='144.963000')
