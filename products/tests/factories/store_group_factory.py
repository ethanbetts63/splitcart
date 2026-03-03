import factory
from factory.django import DjangoModelFactory
from companies.models import StoreGroup, StoreGroupMembership
from companies.tests.factories import CompanyFactory, StoreFactory


class StoreGroupFactory(DjangoModelFactory):
    class Meta:
        model = StoreGroup

    company = factory.SubFactory(CompanyFactory)
    anchor = None


class StoreGroupMembershipFactory(DjangoModelFactory):
    class Meta:
        model = StoreGroupMembership

    store = factory.SubFactory(StoreFactory)
    group = factory.SubFactory(StoreGroupFactory)
