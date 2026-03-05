import factory
from factory.django import DjangoModelFactory
from companies.models import StoreGroup
from .company_factory import CompanyFactory


class StoreGroupFactory(DjangoModelFactory):
    class Meta:
        model = StoreGroup

    company = factory.SubFactory(CompanyFactory)
    anchor = None
