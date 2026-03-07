import pytest
from data_management.models.bargain_stats import BargainStats


@pytest.mark.django_db
class TestBargainStats:
    def test_str_returns_key(self):
        obj = BargainStats(key='bargain_stats')
        assert str(obj) == 'Bargain Stats: bargain_stats'

    def test_create_with_default_data(self):
        obj = BargainStats.objects.create(key='test_stat')
        assert obj.data == {}

    def test_create_with_data(self):
        BargainStats.objects.create(key='price_comps', data={'coles': 1.5, 'woolworths': 1.3})
        obj = BargainStats.objects.get(key='price_comps')
        assert obj.data == {'coles': 1.5, 'woolworths': 1.3}

    def test_key_is_primary_key(self):
        BargainStats.objects.create(key='pk_test', data={})
        obj = BargainStats.objects.get(pk='pk_test')
        assert obj.key == 'pk_test'

    def test_updated_at_is_set_on_create(self):
        obj = BargainStats.objects.create(key='timestamped')
        assert obj.updated_at is not None

    def test_updated_at_changes_on_save(self):
        obj = BargainStats.objects.create(key='update_test', data={})
        first_ts = obj.updated_at
        obj.data = {'new': 'data'}
        obj.save()
        obj.refresh_from_db()
        assert obj.updated_at >= first_ts

    def test_duplicate_key_raises(self):
        from django.db import IntegrityError
        BargainStats.objects.create(key='dup_key', data={})
        with pytest.raises(IntegrityError):
            BargainStats.objects.create(key='dup_key', data={})
