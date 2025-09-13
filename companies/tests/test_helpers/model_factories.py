import factory
from factory.django import DjangoModelFactory
from companies.models import Company, Division, Store, Category

class CompanyFactory(DjangoModelFactory):
    class Meta:
        model = Company
    
    name = factory.Faker('company')

class DivisionFactory(DjangoModelFactory):
    class Meta:
        model = Division

    external_id = factory.Faker('uuid4')
    name = factory.Faker('bs')
    company = factory.SubFactory(CompanyFactory)
    store_finder_id = factory.Faker('word')

class StoreFactory(DjangoModelFactory):
    class Meta:
        model = Store

    store_name = factory.Faker('company')
    company = factory.SubFactory(CompanyFactory)
    division = factory.SubFactory(DivisionFactory)
    store_id = factory.Faker('random_int', min=1000, max=9999)
    is_active = True
    is_online_shopable = False
    phone_number = factory.Faker('phone_number')
    address_line_1 = factory.Faker('street_address')
    address_line_2 = factory.Faker('secondary_address')
    suburb = factory.Faker('city')
    state = factory.Faker('state_abbr')
    postcode = factory.Faker('postcode')
    latitude = factory.Faker('latitude')
    longitude = factory.Faker('longitude')
    trading_hours = {}
    facilities = {}
    is_trading = factory.Faker('boolean')
    retailer_store_id = factory.Faker('random_int', min=1000, max=9999)
    email = factory.Faker('email')
    online_shop_url = factory.Faker('url')
    store_url = factory.Faker('url')
    ecommerce_url = factory.Faker('url')
    record_id = factory.Faker('uuid4')
    status = 'Active'
    store_type = 'Regular'
    site_id = factory.Faker('random_int', min=1, max=100)
    
    shopping_modes = {}
    available_customer_service_types = {}
    alcohol_availability = {}

class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Faker('word')
    slug = factory.LazyAttribute(lambda obj: f"{obj.name.lower()}-slug")
    company = factory.SubFactory(CompanyFactory)
    category_id = factory.Faker('uuid4')
    # parents will be handled post-generation for ManyToMany