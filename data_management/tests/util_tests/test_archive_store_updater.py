import json
import pytest
from companies.models import Company, Store, Division
from data_management.database_updating_classes.archive_store_updater import ArchiveStoreUpdater


def _write_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f)


@pytest.mark.django_db
class TestArchiveStoreUpdaterRun:
    def test_missing_file_returns_none_zero(self, mock_command):
        updater = ArchiveStoreUpdater(mock_command, '/nonexistent/path.json')
        result = updater.run()
        assert result == (None, 0)

    def test_invalid_json_returns_none_zero(self, mock_command, tmp_path):
        path = str(tmp_path / 'bad.json')
        open(path, 'w').write('not json')
        updater = ArchiveStoreUpdater(mock_command, path)
        assert updater.run() == (None, 0)

    def test_missing_company_name_returns_none_zero(self, mock_command, tmp_path):
        path = str(tmp_path / 'data.json')
        _write_json(path, {'metadata': {}, 'stores_by_state': {}})
        updater = ArchiveStoreUpdater(mock_command, path)
        assert updater.run() == (None, 0)

    def test_stores_by_state_creates_company_and_stores(self, mock_command, tmp_path):
        path = str(tmp_path / 'data.json')
        _write_json(path, {
            'metadata': {'company_name': 'Aldi'},
            'stores_by_state': {
                'vic': {'stores': [
                    {'store_id': 'aldi-001', 'store_name': 'Aldi Fitzroy', 'state': 'VIC'},
                ]}
            }
        })
        updater = ArchiveStoreUpdater(mock_command, path)
        company_name, count = updater.run()

        assert company_name == 'Aldi'
        assert count == 1
        assert Company.objects.filter(name='Aldi').exists()
        assert Store.objects.filter(store_id='aldi-001').exists()

    def test_stores_by_division_creates_division_and_stores(self, mock_command, tmp_path):
        path = str(tmp_path / 'data.json')
        _write_json(path, {
            'metadata': {'company_name': 'Woolworths'},
            'stores_by_division': {
                'metro': {
                    'division_name': 'Woolworths Metro',
                    'stores_by_state': {
                        'nsw': {'stores': [
                            {'store_id': 'ww-001', 'store_name': 'WW CBD', 'state': 'NSW'},
                        ]}
                    }
                }
            }
        })
        updater = ArchiveStoreUpdater(mock_command, path)
        company_name, count = updater.run()

        assert company_name == 'Woolworths'
        assert count == 1
        assert Division.objects.filter(name='Woolworths Metro').exists()
        assert Store.objects.filter(store_id='ww-001').exists()

    def test_updates_existing_store_fields(self, mock_command, tmp_path):
        from companies.tests.factories import CompanyFactory, StoreFactory
        company = CompanyFactory(name='Coles')
        store = StoreFactory(company=company, store_id='coles-001', store_name='Old Name')

        path = str(tmp_path / 'data.json')
        _write_json(path, {
            'metadata': {'company_name': 'Coles'},
            'stores_by_state': {
                'vic': {'stores': [
                    {'store_id': 'coles-001', 'store_name': 'New Name', 'state': 'VIC'},
                ]}
            }
        })
        updater = ArchiveStoreUpdater(mock_command, path)
        updater.run()

        store.refresh_from_db()
        assert store.store_name == 'New Name'

    def test_skips_stores_without_store_id(self, mock_command, tmp_path):
        path = str(tmp_path / 'data.json')
        _write_json(path, {
            'metadata': {'company_name': 'TestCo'},
            'stores_by_state': {
                'vic': {'stores': [{'store_name': 'No ID Store'}]}
            }
        })
        updater = ArchiveStoreUpdater(mock_command, path)
        _, count = updater.run()
        assert count == 1  # counted but store not created
        assert not Store.objects.exists()

    def test_division_without_name_is_skipped(self, mock_command, tmp_path):
        path = str(tmp_path / 'data.json')
        _write_json(path, {
            'metadata': {'company_name': 'TestCo'},
            'stores_by_division': {
                'unknown': {
                    'division_name': None,
                    'stores_by_state': {'nsw': {'stores': [{'store_id': 's-1', 'store_name': 'X'}]}}
                }
            }
        })
        updater = ArchiveStoreUpdater(mock_command, path)
        _, count = updater.run()
        assert count == 0
        assert not Division.objects.exists()
