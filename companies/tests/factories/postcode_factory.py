import factory
from factory.django import DjangoModelFactory
from companies.models import Postcode


class PostcodeFactory(DjangoModelFactory):
    class Meta:
        model = Postcode
        django_get_or_create = ('postcode',)

    postcode = factory.Sequence(lambda n: f"{6000 + n:04d}")
    state = 'WA'
    latitude = factory.Faker('latitude')
    longitude = factory.Faker('longitude')
