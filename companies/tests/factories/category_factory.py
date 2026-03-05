import factory
from factory.django import DjangoModelFactory
from companies.models import Category
from .company_factory import CompanyFactory


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ('slug', 'company')

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(' ', '-'))
    company = factory.SubFactory(CompanyFactory)
    category_id = factory.Sequence(lambda n: f"cat-{n}")
