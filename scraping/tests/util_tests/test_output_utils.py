import pytest
from unittest.mock import MagicMock
from scraping.utils.product_scraping_utils.output_utils import ScraperOutput


@pytest.fixture
def command():
    cmd = MagicMock()
    cmd.stdout.write = MagicMock()
    cmd.stdout.flush = MagicMock()
    cmd.stderr.write = MagicMock()
    return cmd


@pytest.fixture
def output(command):
    return ScraperOutput(command, 'Woolworths', 'Woolworths Sydney')


class TestScraperOutputUpdateProgress:
    def test_new_products_accumulate(self, output):
        output.update_progress(new_products=5)
        output.update_progress(new_products=3)
        assert output.new_products == 8

    def test_duplicate_products_accumulate(self, output):
        output.update_progress(duplicate_products=2)
        output.update_progress(duplicate_products=4)
        assert output.duplicate_products == 6

    def test_categories_scraped_takes_max(self, output):
        output.update_progress(categories_scraped=3)
        output.update_progress(categories_scraped=1)  # lower value should not decrease
        assert output.categories_scraped == 3

    def test_total_categories_takes_max(self, output):
        output.update_progress(total_categories=10)
        output.update_progress(total_categories=5)
        assert output.total_categories == 10

    def test_update_calls_stdout_write(self, output, command):
        output.update_progress(new_products=1)
        command.stdout.write.assert_called()

    def test_initial_counts_are_zero(self, output):
        assert output.new_products == 0
        assert output.duplicate_products == 0
        assert output.categories_scraped == 0
        assert output.total_categories == 0


class TestScraperOutputLogError:
    def test_log_error_calls_stderr(self, output, command):
        output.log_error('something went wrong')
        command.stderr.write.assert_called_once()
        call_args = command.stderr.write.call_args[0][0]
        assert 'something went wrong' in call_args


class TestScraperOutputFinalize:
    def test_finalize_writes_newline(self, output, command):
        output.finalize()
        command.stdout.write.assert_called()
