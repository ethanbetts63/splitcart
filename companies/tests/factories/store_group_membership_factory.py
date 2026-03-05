import factory
from factory.django import DjangoModelFactory
from companies.models import StoreGroupMembership
from .store_factory import StoreFactory
from .store_group_factory import StoreGroupFactory


class StoreGroupMembershipFactory(DjangoModelFactory):
    class Meta:
        model = StoreGroupMembership

    store = factory.SubFactory(StoreFactory)
    group = factory.SubFactory(StoreGroupFactory, company=factory.SelfAttribute('..store.company'))
