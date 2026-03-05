import pytest
from django.db import IntegrityError
from companies.models import Company
from companies.tests.factories import CompanyFactory


@pytest.mark.django_db
class TestCompanyModel:
    def test_str_returns_name(self):
        company = CompanyFactory(name='Coles')
        assert str(company) == 'Coles'

    def test_name_uniqueness_enforced(self):
        Company.objects.create(name='Woolworths')
        with pytest.raises(IntegrityError):
            Company.objects.create(name='Woolworths')

    def test_image_url_template_nullable(self):
        company = Company.objects.create(name='No Image Co')
        assert company.image_url_template is None

    def test_image_url_template_can_be_set(self):
        company = CompanyFactory(image_url_template='https://cdn.example.com/{sku}.jpg')
        assert company.image_url_template == 'https://cdn.example.com/{sku}.jpg'
