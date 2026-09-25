"""A transient network failure must not cost the whole Woolworths run.

`fetch_data_for_item` is called outside the base scraper loop's try/except, so
an exception from it propagates past the loop into the `finally`, where
`scrape_successful` is still False and `jsonl_writer.cleanup()` deletes the
partial file. On 2026-09-25 one read timeout against woolworths.com.au threw
away a ~23,000-product scrape that way, with nothing written.

Discarding a partial scrape is correct and is not what these tests change:
`update --products` runs an orphan cleaner, so ingesting half a catalogue would
read the absent half as delisted and delete thousands of live products. What
these tests pin is the other half of the fix -- a blip must not count as a
failure in the first place.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from scraping.scrapers.product_scraper_woolworths import ProductScraperWoolworths


def _scraper():
    scraper = ProductScraperWoolworths.__new__(ProductScraperWoolworths)
    scraper.command = MagicMock()
    scraper.session = MagicMock()
    return scraper


def _ok_response(payload=None):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload if payload is not None else {'Bundles': []}
    return response


def _http_error(status):
    response = MagicMock()
    response.status_code = status
    error = requests.exceptions.HTTPError(response=response)
    response.raise_for_status.side_effect = error
    return response


class TestRetriesTransientFailures:
    @pytest.mark.parametrize(
        'failure',
        [
            requests.exceptions.Timeout('read timed out'),
            requests.exceptions.ConnectionError('connection reset'),
        ],
    )
    def test_a_blip_is_retried_and_the_page_still_returns(self, failure):
        scraper = _scraper()
        scraper.session.post.side_effect = [failure, _ok_response({'Bundles': ['ok']})]

        with patch('scraping.scrapers.product_scraper_woolworths.time.sleep'):
            data = scraper._post_with_retry('http://api', {}, 'bakery', 1)

        assert data == {'Bundles': ['ok']}
        assert scraper.session.post.call_count == 2

    def test_a_server_error_is_retried_too(self):
        scraper = _scraper()
        scraper.session.post.side_effect = [_http_error(503), _ok_response()]

        with patch('scraping.scrapers.product_scraper_woolworths.time.sleep'):
            scraper._post_with_retry('http://api', {}, 'bakery', 1)

        assert scraper.session.post.call_count == 2

    def test_the_backoff_grows_rather_than_hammering(self):
        scraper = _scraper()
        scraper.session.post.side_effect = [
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
            _ok_response(),
        ]

        with patch('scraping.scrapers.product_scraper_woolworths.time.sleep') as sleep:
            scraper._post_with_retry('http://api', {}, 'bakery', 1)

        waited = [call.args[0] for call in sleep.call_args_list]
        assert waited == sorted(waited) and len(set(waited)) == len(waited), (
            f'Backoff should increase between attempts, got {waited}'
        )


class TestGivesUpHonestly:
    def test_a_persistent_failure_still_raises(self):
        """Exhausting the retries must re-raise, not return None.

        Returning None here would be worse than the original bug: the base loop
        reads a falsy result as "this category is empty", skips it, and the run
        finishes *successfully* with a catalogue quietly missing that category --
        which the orphan cleaner would then treat as delistings.
        """
        scraper = _scraper()
        scraper.session.post.side_effect = requests.exceptions.Timeout('down')

        with patch('scraping.scrapers.product_scraper_woolworths.time.sleep'):
            with pytest.raises(requests.exceptions.Timeout):
                scraper._post_with_retry('http://api', {}, 'bakery', 1)

        assert scraper.session.post.call_count == ProductScraperWoolworths.RETRY_ATTEMPTS

    def test_a_client_error_is_not_retried(self):
        """A 4xx is this code asking the wrong question.

        Repeating it asks it wrong again, more slowly, against a live retailer.
        """
        scraper = _scraper()
        scraper.session.post.side_effect = [_http_error(404), _ok_response()]

        with patch('scraping.scrapers.product_scraper_woolworths.time.sleep'):
            with pytest.raises(requests.exceptions.HTTPError):
                scraper._post_with_retry('http://api', {}, 'bakery', 1)

        assert scraper.session.post.call_count == 1
