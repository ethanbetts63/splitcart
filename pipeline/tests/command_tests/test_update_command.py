from unittest.mock import patch
from django.core.management import call_command


BASE = 'pipeline.management.commands.update'


class TestUpdateCommandDispatch:
    @patch(f'{BASE}.SubstitutionUpdateOrchestrator')
    def test_subs_flag_runs_substitution_orchestrator(self, MockOrch):
        call_command('update', subs=True)
        MockOrch.return_value.run.assert_called_once()

    @patch(f'{BASE}.CategoryLinkUpdateOrchestrator')
    def test_cat_links_flag_runs_category_link_orchestrator(self, MockOrch):
        call_command('update', cat_links=True)
        MockOrch.return_value.run.assert_called_once()

    @patch(f'{BASE}.UpdateOrchestrator')
    def test_post_process_only_flag_skips_inbox_loop(self, MockOrch):
        call_command('update', products=True, post_process_only=True)
        MockOrch.assert_called_once()
        _, kwargs = MockOrch.call_args
        assert kwargs.get('post_process_only') is True
        MockOrch.return_value.run.assert_called_once()

    @patch(f'{BASE}.UpdateOrchestrator')
    @patch(f'{BASE}.os.path.exists', return_value=False)
    def test_products_with_empty_inbox_does_not_run_orchestrator(self, mock_exists, MockOrch):
        call_command('update', products=True)
        MockOrch.assert_not_called()

    @patch(f'{BASE}.time.sleep')
    @patch(f'{BASE}.UpdateOrchestrator')
    @patch(f'{BASE}.os.walk')
    @patch(f'{BASE}.os.path.exists', return_value=True)
    def test_products_with_files_runs_orchestrator_then_exits(self, mock_exists, mock_walk, MockOrch, mock_sleep):
        # First call: inbox has a .jsonl file; second call: empty (loop exits)
        mock_walk.side_effect = [
            [('root', [], ['data.jsonl'])],  # first check: files present
            [('root', [], [])],              # second check: empty after run
        ]
        call_command('update', products=True)
        MockOrch.return_value.run.assert_called_once()
        _, kwargs = MockOrch.call_args
        assert kwargs.get('preserve_source_files') is False

    @patch(f'{BASE}.time.sleep')
    @patch(f'{BASE}.UpdateOrchestrator')
    @patch(f'{BASE}.os.walk')
    @patch(f'{BASE}.os.path.exists', return_value=True)
    def test_products_archive_reads_private_archive_and_preserves_files(self, mock_exists, mock_walk, MockOrch, mock_sleep):
        mock_walk.return_value = [('root', [], ['data.jsonl'])]
        call_command('update', products=True, archive=True)
        MockOrch.return_value.run.assert_called_once()
        _, kwargs = MockOrch.call_args
        assert kwargs.get('preserve_source_files') is True
        assert str(kwargs.get('source_path')).endswith('pipeline\\private_data\\product_archive')

    @patch(f'{BASE}.UpdateOrchestrator')
    def test_no_flags_runs_nothing(self, MockUpdate):
        call_command('update')
        MockUpdate.assert_not_called()
