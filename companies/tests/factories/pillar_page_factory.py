import factory
from factory.django import DjangoModelFactory
from companies.models import PillarPage


class PillarPageFactory(DjangoModelFactory):
    class Meta:
        model = PillarPage
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f"Pillar Page {n}")
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(' ', '-'))
    hero_title = factory.Faker('sentence')
    introduction_paragraph = factory.Faker('paragraph')
