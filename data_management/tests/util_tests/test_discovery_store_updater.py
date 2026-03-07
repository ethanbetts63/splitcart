import json
import pytest
from companies.models import Company, Store
from data_management.database_updating_classes.discovery_store_updater import DiscoveryStoreUpdater


def _write_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f)


@pytest.mark.django_db
class TestDiscoveryStoreUpdaterRun:
    def test_missing_file_returns_none_zero(self, mock_command):
        updater = DiscoveryStoreUpdater(mock_command, '/nonexistent/path.json')
        assert updater.run() == (None, 0)

    def test_invalid_json_returns_none_zero(self, mock_command, tmp_path):
        path = str(tmp_path / 'bad.json')
        open(path, 'w').write('not json')
        updater = DiscoveryStoreUpdater(mock_command, path)
        assert updater.run() == (None, 0)

    def test_nested_structure_creates_company_and_store(self, mock_command, tmp_path):
        """Coles-style: metadata + store_data wrapper."""
        path = str(tmp_path / 'coles.json')
        _write_json(path, {
            'metadata': {'company': 'Coles'},
            'store_data': {
                'store_id': 'coles-001',
                'store_name': 'Coles Fitzroy',
                'state': 'VIC',
                'suburb': 'Fitzroy',
                'postcode': '3065',
            }
        })
        updater = DiscoveryStoreUpdater(mock_command, path)
        company_name, count = updater.run()

        assert company_name == 'Coles'
        assert count == 1
        assert Company.objects.filter(name='Coles').exists()
        assert Store.objects.filter(store_id='coles-001').exists()

    def test_flat_structure_creates_company_and_store(self, mock_command, tmp_path):
        """Woolworths-style: flat dict with company key at root."""
        path = str(tmp_path / 'woolworths.json')
        _write_json(path, {
            'company': 'Woolworths',
            'store_id': 'ww-001',
            'name': 'WW CBD',
            'state': 'NSW',
            'suburb': 'Sydney',
            'postcode': '2000',
        })
        updater = DiscoveryStoreUpdater(mock_command, path)
        company_name, count = updater.run()

        assert company_name == 'Woolworths'
        assert count == 1
        assert Store.objects.filter(store_id='ww-001').exists()

    def test_missing_company_name_returns_none_zero(self, mock_command, tmp_path):
        path = str(tmp_path / 'data.json')
        _write_json(path, {'store_id': 'x-001', 'name': 'Some Store'})
        updater = DiscoveryStoreUpdater(mock_command, path)
        assert updater.run() == (None, 0)

    def test_missing_store_id_creates_no_store(self, mock_command, tmp_path):
        path = str(tmp_path / 'data.json')
        _write_json(path, {
            'company': 'TestCo',
            'name': 'No ID Store',
            'state': 'QLD',
        })
        updater = DiscoveryStoreUpdater(mock_command, path)
        company_name, count = updater.run()

        assert company_name == 'TestCo'
        assert count == 1
        assert not Store.objects.exists()

    def test_updates_existing_store_fields(self, mock_command, tmp_path):
        from companies.tests.factories import CompanyFactory, StoreFactory
        company = CompanyFactory(name='Aldi')
        StoreFactory(company=company, store_id='aldi-001', store_name='Old Name')

        path = str(tmp_path / 'data.json')
        _write_json(path, {
            'company': 'Aldi',
            'store_id': 'aldi-001',
            'name': 'New Name',
            'state': 'VIC',
        })
        updater = DiscoveryStoreUpdater(mock_command, path)
        updater.run()

        store = Store.objects.get(store_id='aldi-001')
        assert store.store_name == 'New Name'

    def test_flat_structure_maps_address_field(self, mock_command, tmp_path):
        """Flat format may use 'address' instead of 'address_line_1'."""
        path = str(tmp_path / 'data.json')
        _write_json(path, {
            'company': 'IGA',
            'store_id': 'iga-001',
            'name': 'IGA Local',
            'address': '123 Main St',
            'state': 'WA',
        })
        updater = DiscoveryStoreUpdater(mock_command, path)
        updater.run()

        store = Store.objects.get(store_id='iga-001')
        assert store.address_line_1 == '123 Main St'

    def test_none_values_not_overwritten_on_update(self, mock_command, tmp_path):
        """Existing non-null data should not be overwritten with None."""
        from companies.tests.factories import CompanyFactory, StoreFactory
        company = CompanyFactory(name='Coles')
        StoreFactory(company=company, store_id='coles-002', suburb='Collingwood')

        path = str(tmp_path / 'data.json')
        # New data has no suburb field
        _write_json(path, {
            'metadata': {'company': 'Coles'},
            'store_data': {'store_id': 'coles-002', 'store_name': 'Coles Updated'}
        })
        updater = DiscoveryStoreUpdater(mock_command, path)
        updater.run()

        store = Store.objects.get(store_id='coles-002')
        assert store.suburb == 'Collingwood'
