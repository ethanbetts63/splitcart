import factory
from factory.django import DjangoModelFactory
from companies.models import Store
from .company_factory import CompanyFactory
from .division_factory import DivisionFactory

class StoreFactory(DjangoModelFactory):
    class Meta:
        model = Store
        django_get_or_create = ('company', 'store_id',)

    store_name = factory.Faker('company')
    company = factory.SubFactory(CompanyFactory)
    division = factory.SubFactory(DivisionFactory, company=factory.SelfAttribute('..company'))
    store_id = factory.Sequence(lambda n: str(n))
    
    address_line_1 = factory.Faker('street_address')
    suburb = factory.Faker('city')
    state = factory.Faker('state_abbr')
    postcode = factory.Faker('postcode')
    latitude = factory.Faker('latitude')
    longitude = factory.Faker('longitude')

    last_scraped = None
    needs_rescraping = False
    scheduled_at = None
    
    retailer_store_id = factory.Sequence(lambda n: f"retailer_{n}")

