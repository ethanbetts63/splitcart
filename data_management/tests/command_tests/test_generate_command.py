from unittest.mock import patch
from django.core.management import call_command

GEN = 'data_management.utils.generation_utils'


class TestGenerateCommandDispatch:
    @patch(f'{GEN}.substitutions_generator.SubstitutionsGenerator')
    def test_subs_flag_runs_substitutions_generator(self, MockGen):
        call_command('generate', subs=True)
        MockGen.assert_called_once()
        MockGen.return_value.run.assert_called_once()

    @patch(f'{GEN}.category_links_generator.CategoryLinksGenerator')
    def test_cat_links_flag_runs_category_links_generator(self, MockGen):
        call_command('generate', cat_links=True)
        MockGen.return_value.run.assert_called_once()

    @patch(f'{GEN}.map_generator.MapGenerator')
    def test_map_flag_runs_map_generator(self, MockGen):
        call_command('generate', map=True)
        MockGen.return_value.run.assert_called_once()

    @patch(f'{GEN}.map_generator.MapGenerator')
    def test_map_flag_passes_company_name(self, MockGen):
        call_command('generate', map=True, company='Coles')
        _, kwargs = MockGen.call_args
        assert kwargs.get('company_name') == 'Coles'

    @patch(f'{GEN}.primary_categories_generator.PrimaryCategoriesGenerator')
    def test_primary_cats_flag(self, MockGen):
        call_command('generate', primary_cats=True)
        MockGen.return_value.run.assert_called_once()

    @patch(f'{GEN}.price_summaries_generator.PriceSummariesGenerator')
    def test_price_summaries_flag(self, MockGen):
        call_command('generate', price_summaries=True)
        MockGen.return_value.run.assert_called_once()

    @patch(f'{GEN}.default_stores_generator.DefaultStoresGenerator')
    def test_default_stores_flag(self, MockGen):
        call_command('generate', default_stores=True)
        MockGen.return_value.run.assert_called_once()

    @patch(f'{GEN}.store_groups_generator.StoreGroupsGenerator')
    def test_store_groups_flag(self, MockGen):
        call_command('generate', store_groups=True)
        MockGen.return_value.run.assert_called_once()

    @patch(f'{GEN}.price_comparisons_generator.PriceComparisonsGenerator')
    def test_price_comps_flag(self, MockGen):
        call_command('generate', price_comps=True)
        MockGen.return_value.run.assert_called_once()

    @patch(f'{GEN}.bargain_stats_generator.BargainStatsGenerator')
    def test_bargain_stats_flag(self, MockGen):
        call_command('generate', bargain_stats=True)
        MockGen.return_value.run.assert_called_once()

    @patch(f'{GEN}.pillars_generator.PillarsGenerator')
    def test_pillars_flag(self, MockGen):
        call_command('generate', pillars=True)
        MockGen.return_value.run.assert_called_once()

    @patch(f'{GEN}.archive_generator.ArchiveGenerator')
    def test_archive_flag(self, MockGen):
        call_command('generate', archive=True)
        MockGen.return_value.run.assert_called_once()

    @patch(f'{GEN}.store_stats_generator.StoreStatsGenerator')
    def test_store_stats_flag(self, MockGen):
        call_command('generate', store_stats=True)
        MockGen.return_value.run.assert_called_once()

    @patch(f'{GEN}.substitutions_generator.SubstitutionsGenerator')
    @patch(f'{GEN}.bargain_stats_generator.BargainStatsGenerator')
    def test_multiple_flags_run_multiple_generators(self, MockBargain, MockSubs):
        call_command('generate', subs=True, bargain_stats=True)
        MockSubs.return_value.run.assert_called_once()
        MockBargain.return_value.run.assert_called_once()

    @patch(f'{GEN}.substitutions_generator.SubstitutionsGenerator')
    def test_dev_flag_passed_to_generator(self, MockGen):
        call_command('generate', subs=True, dev=True)
        _, kwargs = MockGen.call_args
        assert kwargs.get('dev') is True

    @patch(f'{GEN}.substitutions_generator.SubstitutionsGenerator')
    def test_no_flags_runs_nothing(self, MockGen):
        call_command('generate')
        MockGen.assert_not_called()
