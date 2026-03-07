from unittest.mock import patch
from django.core.management import call_command


BASE = 'data_management.management.commands.upload'


class TestUploadCommandDispatch:
    @patch(f'{BASE}.ProductUploader')
    def test_products_flag_runs_product_uploader(self, MockUp):
        call_command('upload', products=True)
        MockUp.return_value.run.assert_called_once()

    @patch(f'{BASE}.Gs1Uploader')
    def test_gs1_flag_runs_gs1_uploader(self, MockUp):
        call_command('upload', gs1=True)
        MockUp.return_value.run.assert_called_once()

    @patch(f'{BASE}.StoreUploader')
    def test_stores_flag_runs_store_uploader(self, MockUp):
        call_command('upload', stores=True)
        MockUp.return_value.run.assert_called_once()

    @patch(f'{BASE}.CategoryLinksUploader')
    def test_cat_links_flag_runs_category_links_uploader(self, MockUp):
        call_command('upload', cat_links=True)
        MockUp.return_value.run.assert_called_once()

    @patch(f'{BASE}.SubstitutionsUploader')
    def test_subs_flag_runs_substitutions_uploader(self, MockUp):
        call_command('upload', subs=True)
        MockUp.return_value.run.assert_called_once()

    @patch(f'{BASE}.ProductUploader')
    @patch(f'{BASE}.Gs1Uploader')
    @patch(f'{BASE}.StoreUploader')
    @patch(f'{BASE}.CategoryLinksUploader')
    @patch(f'{BASE}.SubstitutionsUploader')
    def test_no_flags_runs_nothing(self, MockSubs, MockCats, MockStores, MockGs1, MockProds):
        call_command('upload')
        for MockUp in [MockProds, MockGs1, MockStores, MockCats, MockSubs]:
            MockUp.return_value.run.assert_not_called()

    @patch(f'{BASE}.ProductUploader')
    def test_dev_flag_passed_to_uploader(self, MockProds):
        call_command('upload', products=True, dev=True)
        _, kwargs = MockProds.call_args
        assert kwargs.get('dev') is True
