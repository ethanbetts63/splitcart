import pytest
from unittest.mock import patch, MagicMock
from django.core.management import call_command


BASE = 'data_management.management.commands.update'


class TestUpdateCommandDispatch:
    @patch(f'{BASE}.load_db_from_latest_archive')
    def test_archive_flag_calls_load_and_returns(self, mock_load):
        with patch(f'{BASE}.DiscoveryUpdateOrchestrator') as MockDisc:
            call_command('update', archive=True)
        mock_load.assert_called_once()
        # --archive exits early; discovery orchestrator should not run
        MockDisc.assert_not_called()

    @patch(f'{BASE}.SubstitutionUpdateOrchestrator')
    def test_subs_flag_runs_substitution_orchestrator(self, MockOrch):
        call_command('update', subs=True)
        MockOrch.return_value.run.assert_called_once()

    @patch(f'{BASE}.CategoryLinkUpdateOrchestrator')
    def test_cat_links_flag_runs_category_link_orchestrator(self, MockOrch):
        call_command('update', cat_links=True)
        MockOrch.return_value.run.assert_called_once()

    @patch(f'{BASE}.GS1UpdateOrchestrator')
    def test_gs1_flag_runs_gs1_orchestrator(self, MockOrch):
        call_command('update', gs1=True)
        MockOrch.return_value.run.assert_called_once()

    @patch(f'{BASE}.DiscoveryUpdateOrchestrator')
    def test_stores_flag_runs_discovery_orchestrator(self, MockOrch):
        call_command('update', stores=True)
        MockOrch.return_value.run.assert_called_once()

    @patch(f'{BASE}.UpdateOrchestrator')
    def test_post_process_only_flag_skips_inbox_loop(self, MockOrch):
        call_command('update', products=True, post_process_only=True)
        MockOrch.assert_called_once()
        _, kwargs = MockOrch.call_args
        assert kwargs.get('post_process_only') is True
        MockOrch.return_value.run.assert_called_once()

    @patch(f'{BASE}.UpdateOrchestrator')
    def test_relaxed_staleness_flag_passed_to_orchestrator(self, MockOrch):
        call_command('update', products=True, post_process_only=True, relaxed_staleness=True)
        _, kwargs = MockOrch.call_args
        assert kwargs.get('relaxed_staleness') is True

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

    @patch(f'{BASE}.DiscoveryUpdateOrchestrator')
    @patch(f'{BASE}.UpdateOrchestrator')
    def test_no_flags_runs_nothing(self, MockUpdate, MockDisc):
        call_command('update')
        MockDisc.assert_not_called()
        MockUpdate.assert_not_called()
