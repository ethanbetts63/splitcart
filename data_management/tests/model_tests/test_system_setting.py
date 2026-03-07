import pytest
from data_management.models.system_setting import SystemSetting


@pytest.mark.django_db
class TestSystemSetting:
    def test_str_returns_key(self):
        setting = SystemSetting(key='my_key', value='hello')
        assert str(setting) == 'my_key'

    def test_create_with_string_value(self):
        SystemSetting.objects.create(key='site_name', value='Splitcart')
        assert SystemSetting.objects.filter(key='site_name').exists()

    def test_create_with_dict_value(self):
        SystemSetting.objects.create(key='config', value={'feature': True, 'limit': 10})
        obj = SystemSetting.objects.get(key='config')
        assert obj.value == {'feature': True, 'limit': 10}

    def test_create_with_list_value(self):
        SystemSetting.objects.create(key='allowed_ids', value=[1, 2, 3])
        obj = SystemSetting.objects.get(key='allowed_ids')
        assert obj.value == [1, 2, 3]

    def test_key_is_primary_key(self):
        SystemSetting.objects.create(key='pk_test', value=1)
        obj = SystemSetting.objects.get(pk='pk_test')
        assert obj.key == 'pk_test'

    def test_update_value(self):
        SystemSetting.objects.create(key='counter', value=0)
        SystemSetting.objects.filter(key='counter').update(value=42)
        assert SystemSetting.objects.get(key='counter').value == 42

    def test_duplicate_key_raises(self):
        from django.db import IntegrityError
        SystemSetting.objects.create(key='unique_key', value='first')
        with pytest.raises(IntegrityError):
            SystemSetting.objects.create(key='unique_key', value='second')
