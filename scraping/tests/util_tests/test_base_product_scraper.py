"""`BaseProductScraper.run()` -- the order every scraper's output depends on.

Four supermarket scrapers inherit this loop, and it decides one thing that
matters more than the rest: whether a run's `.jsonl` is committed to the outbox
or thrown away. A committed file is uploaded and written to the database, so a
run that failed halfway and committed anyway publishes a partial catalogue --
and a partial catalogue reads as "these products are no longer stocked".

The subclass hooks are stubbed rather than mocked wholesale, so the loop under
test is the real one.
"""

from unittest.mock import MagicMock

import pytest

from scraping.scrapers.base_product_scraper import BaseProductScraper


class StubScraper(BaseProductScraper):
    """A scraper whose four hooks answer from lists the test sets up."""

    def __init__(self, command, work_items=None, pages=None, cleaned=None,
                 setup_succeeds=True):
        super().__init__(
            command=command,
            company='Stub',
            store_id='1',
            store_name='Stub Store',
            state='wa',
            load_translation_tables=False,
        )
        self._work_items = work_items if work_items is not None else ['cat-a']
        self._pages = pages if pages is not None else {}
        self._cleaned = cleaned if cleaned is not None else {}
        self._setup_succeeds = setup_succeeds
        self.enriched = False
        self.jsonl_writer = MagicMock()
        self.jsonl_writer.write_product.return_value = True

    def setup(self):
        return self._setup_succeeds

    def get_work_items(self):
        return self._work_items

    def fetch_data_for_item(self, item):
        return self._pages.get(item, [])

    def clean_raw_data(self, raw_data):
        packet = self._cleaned.get(raw_data[0], {})
        if isinstance(packet, Exception):
            raise packet
        return packet

    def post_scrape_enrichment(self):
        self.enriched = True


@pytest.fixture
def command():
    cmd = MagicMock()
    cmd.style.SUCCESS.side_effect = lambda message: message
    cmd.style.WARNING.side_effect = lambda message: message
    cmd.style.ERROR.side_effect = lambda message: message
    return cmd


def _packet(*names):
    return {
        'metadata': {'company': 'stub'},
        'products': [{'name': name} for name in names],
    }


class TestASuccessfulRun:
    def test_products_are_written_and_the_file_is_committed(self, command):
        scraper = StubScraper(
            command,
            work_items=['cat-a'],
            pages={'cat-a': ['raw-a']},
            cleaned={'raw-a': _packet('Milk', 'Bread')},
        )

        scraper.run()

        assert scraper.jsonl_writer.write_product.call_count == 2
        scraper.jsonl_writer.commit.assert_called_once()
        scraper.jsonl_writer.cleanup.assert_not_called()

    def test_every_work_item_is_visited(self, command):
        scraper = StubScraper(
            command,
            work_items=['cat-a', 'cat-b', 'cat-c'],
            pages={'cat-a': ['raw-a'], 'cat-b': ['raw-b'], 'cat-c': ['raw-c']},
            cleaned={
                'raw-a': _packet('Milk'),
                'raw-b': _packet('Bread'),
                'raw-c': _packet('Eggs'),
            },
        )

        scraper.run()

        assert scraper.output.categories_scraped == 3
        assert scraper.jsonl_writer.write_product.call_count == 3

    def test_enrichment_runs_before_the_commit(self, command):
        """`post_scrape_enrichment` is where the Coles barcode pass hangs, and
        it has to happen while the file is still in the staging area."""
        scraper = StubScraper(
            command,
            pages={'cat-a': ['raw-a']},
            cleaned={'raw-a': _packet('Milk')},
        )

        scraper.run()

        assert scraper.enriched is True

    def test_duplicates_still_count_as_a_successful_run(self, command):
        """A re-scrape of an unchanged store writes no new rows. That is a
        complete scrape, not a failed one, and must not be discarded."""
        scraper = StubScraper(
            command,
            pages={'cat-a': ['raw-a']},
            cleaned={'raw-a': _packet('Milk')},
        )
        scraper.jsonl_writer.write_product.return_value = False

        scraper.run()

        assert scraper.output.duplicate_products == 1
        scraper.jsonl_writer.commit.assert_called_once()


class TestARunThatProducesNothing:
    def test_an_empty_scrape_is_thrown_away_not_committed(self, command):
        """Committing an empty file would tell the pipeline this store now
        stocks nothing."""
        scraper = StubScraper(command, work_items=['cat-a'], pages={'cat-a': []})

        scraper.run()

        scraper.jsonl_writer.cleanup.assert_called_once()
        scraper.jsonl_writer.commit.assert_not_called()

    def test_a_category_with_no_products_is_skipped_not_cleaned(self, command):
        scraper = StubScraper(
            command,
            work_items=['empty', 'cat-a'],
            pages={'empty': [], 'cat-a': ['raw-a']},
            cleaned={'raw-a': _packet('Milk')},
        )

        scraper.run()

        assert scraper.jsonl_writer.write_product.call_count == 1

    def test_a_cleaner_returning_no_products_writes_nothing(self, command):
        scraper = StubScraper(
            command,
            pages={'cat-a': ['raw-a']},
            cleaned={'raw-a': {'metadata': {}, 'products': []}},
        )

        scraper.run()

        scraper.jsonl_writer.write_product.assert_not_called()
        scraper.jsonl_writer.cleanup.assert_called_once()


class TestARunThatFails:
    def test_a_failed_setup_never_opens_the_file(self, command):
        scraper = StubScraper(command, setup_succeeds=False)

        scraper.run()

        scraper.jsonl_writer.open.assert_not_called()
        scraper.jsonl_writer.commit.assert_not_called()
        scraper.jsonl_writer.cleanup.assert_not_called()

    def test_a_cleaning_failure_stops_the_run_rather_than_skipping_the_category(
        self, command
    ):
        """A cleaner that raises is a broken cleaner, not one bad category. The
        remaining categories would all fail the same way and the file would be
        committed short."""
        scraper = StubScraper(
            command,
            work_items=['cat-a', 'cat-b'],
            pages={'cat-a': ['raw-a'], 'cat-b': ['raw-b']},
            cleaned={
                'raw-a': ValueError('cleaner is broken'),
                'raw-b': _packet('Bread'),
            },
        )

        scraper.run()

        scraper.jsonl_writer.write_product.assert_not_called()
        scraper.jsonl_writer.cleanup.assert_called_once()
        scraper.jsonl_writer.commit.assert_not_called()

    def test_a_cleaning_failure_after_products_were_written_still_commits(
        self, command
    ):
        """What was already scraped is real. The run stops, but the rows that
        made it are kept rather than discarded."""
        scraper = StubScraper(
            command,
            work_items=['cat-a', 'cat-b'],
            pages={'cat-a': ['raw-a'], 'cat-b': ['raw-b']},
            cleaned={
                'raw-a': _packet('Milk'),
                'raw-b': ValueError('cleaner is broken'),
            },
        )

        scraper.run()

        scraper.jsonl_writer.commit.assert_called_once()
        assert scraper.output.new_products == 1

    def test_the_file_is_always_closed(self, command):
        scraper = StubScraper(
            command,
            pages={'cat-a': ['raw-a']},
            cleaned={'raw-a': ValueError('cleaner is broken')},
        )

        scraper.run()

        scraper.jsonl_writer.close.assert_called_once()


class TestTranslationTables:
    def test_a_scraper_may_start_without_them(self, command):
        """`load_translation_tables=False` is the switch the tests use, and the
        one a first run on a fresh machine needs."""
        scraper = StubScraper(command)

        assert scraper.brand_translations == {}
        assert scraper.product_translations == {}
