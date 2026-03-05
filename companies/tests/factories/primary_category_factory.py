import factory
from factory.django import DjangoModelFactory
from companies.models import PrimaryCategory


class PrimaryCategoryFactory(DjangoModelFactory):
    class Meta:
        model = PrimaryCategory
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f"Primary Category {n}")
