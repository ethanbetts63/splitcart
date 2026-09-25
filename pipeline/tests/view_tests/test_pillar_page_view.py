"""`GET /api/pillar-pages/<slug>/` -- the only public read the pipeline serves.

Everything else under `pipeline/views/` is behind the internal API key. This one
answers a browser, which is why it carries the `public` throttle scope and a
day-long `cache_page`.
"""

import pytest
from django.urls import reverse

from companies.tests.factories import PillarPageFactory, PrimaryCategoryFactory


def _url(slug):
    return reverse('pillar-page-detail', kwargs={'slug': slug})


@pytest.mark.django_db
class TestPillarPageDetail:
    def test_a_page_is_served_by_its_slug(self, api_client):
        page = PillarPageFactory(name='Pantry', slug='pantry', hero_title='Pantry')

        response = api_client.get(_url('pantry'))

        assert response.status_code == 200, response.content
        assert response.json()['name'] == page.name
        assert response.json()['slug'] == 'pantry'

    def test_the_page_carries_its_primary_categories(self, api_client):
        """The frontend renders the category grid straight from this."""
        page = PillarPageFactory(slug='pantry')
        page.primary_categories.add(
            PrimaryCategoryFactory(name='Tinned'), PrimaryCategoryFactory(name='Pasta')
        )

        response = api_client.get(_url('pantry'))

        names = {row['name'] for row in response.json()['primary_categories']}
        assert names == {'Tinned', 'Pasta'}

    def test_a_page_with_no_categories_reports_an_empty_list(self, api_client):
        PillarPageFactory(slug='pantry')

        assert api_client.get(_url('pantry')).json()['primary_categories'] == []

    def test_an_unknown_slug_is_a_404_with_a_readable_body(self, api_client):
        """`RetrieveAPIView` would raise `Http404` into DRF's generic handler;
        this view catches it so the body reads like the rest of the API."""
        response = api_client.get(_url('no-such-page'))

        assert response.status_code == 404
        assert response.json() == {'detail': 'Pillar page not found.'}

    def test_it_is_readable_without_the_internal_api_key(self, api_client):
        """Public: this is the one pipeline route a browser reaches."""
        PillarPageFactory(slug='pantry')

        assert api_client.get(_url('pantry')).status_code == 200

    def test_the_editorial_copy_is_served(self, api_client):
        page = PillarPageFactory(
            slug='pantry',
            hero_title='Everything for the pantry',
            introduction_paragraph='Compare prices across the supermarkets.',
        )

        body = api_client.get(_url('pantry')).json()

        assert body['hero_title'] == page.hero_title
        assert body['introduction_paragraph'] == page.introduction_paragraph
