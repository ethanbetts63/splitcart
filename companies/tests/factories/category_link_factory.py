import factory
from factory.django import DjangoModelFactory
from companies.models import CategoryLink
from .category_factory import CategoryFactory


class CategoryLinkFactory(DjangoModelFactory):
    class Meta:
        model = CategoryLink

    category_a = factory.SubFactory(CategoryFactory)
    category_b = factory.SubFactory(CategoryFactory)
    link_type = CategoryLink.LinkType.MATCH
