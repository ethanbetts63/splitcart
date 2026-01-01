import factory
from factory.django import DjangoModelFactory
from companies.models import Division
from .company_factory import CompanyFactory

class DivisionFactory(DjangoModelFactory):
    class Meta:
        model = Division
        django_get_or_create = ('name', 'company',)

    name = factory.Faker('bs')
    company = factory.SubFactory(CompanyFactory)
    external_id = factory.Faker('uuid4')
    store_finder_id = factory.Faker('ean8')

