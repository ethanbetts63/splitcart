from unittest.mock import patch
from django.core.management import call_command


BASE = 'data_management.management.commands.upload'


class TestUploadCommandDispatch:
    @patch(f'{BASE}.ProductUploader')
    def test_products_flag_runs_product_uploader(self, MockUp):
        call_command('upload', products=True)
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
    @patch(f'{BASE}.CategoryLinksUploader')
    @patch(f'{BASE}.SubstitutionsUploader')
    def test_no_flags_runs_nothing(self, MockSubs, MockCats, MockProds):
        call_command('upload')
        for MockUp in [MockProds, MockCats, MockSubs]:
            MockUp.return_value.run.assert_not_called()

    @patch(f'{BASE}.ProductUploader')
    def test_dev_flag_passed_to_uploader(self, MockProds):
        call_command('upload', products=True, dev=True)
        _, kwargs = MockProds.call_args
        assert kwargs.get('dev') is True
