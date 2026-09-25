"""`POST /api/import/semantic_data/` -- routed, gated, and unable to import.

Two facts about this endpoint, both established here:

1. **It cannot create a substitution.** The view builds
   `ProductSubstitution(..., source=sub_data['source'])`, and `source` has been
   commented out of `products/models/substitution.py`. Every call carrying
   substitutions raises `TypeError`, is swallowed by the view's blanket
   `except Exception`, and comes back as a 400 saying so. The
   `substitutions_created` count it advertises can only ever be zero.
2. **Nothing calls it.** Substitutions reach the server through
   `/api/upload/substitutions/` -- see
   `scraping/utils/command_utils/substitutions_uploader.py`, which names that
   path. A repository-wide search for `semantic_data` finds only `pipeline/urls.py`
   and the view itself. No documentation mentions it either.

That makes this a superseded endpoint, and the recommendation is to delete it
along with its route. It is left in place here because removing a URL is a
compatibility decision rather than a testing one. The import test below asserts
what the endpoint claims to do and is marked `xfail(strict=True)`, so it fails
loudly if the behaviour is ever repaired -- or is deleted with the view.
"""

import pytest
from django.urls import reverse

from products.models import ProductSubstitution
from products.tests.factories import ProductFactory

INTERNAL_KEY = 'test-internal-key'


@pytest.fixture(autouse=True)
def internal_api_key(monkeypatch):
    monkeypatch.setenv('INTERNAL_API_KEY', INTERNAL_KEY)


def _substitution(product_a, product_b):
    return {
        'product_a': product_a.id,
        'product_b': product_b.id,
        'level': 'LVL3',
        'score': 0.9,
        'source': 'heuristic_v1',
    }


@pytest.mark.django_db
class TestTheInternalGate:
    def test_without_the_internal_key_nothing_is_imported(self, api_client):
        response = api_client.post(
            reverse('import-semantic-data'), {'substitutions': []}, format='json'
        )

        assert response.status_code in (401, 403)
        assert ProductSubstitution.objects.count() == 0

    def test_the_wrong_internal_key_is_refused(self, api_client):
        response = api_client.post(
            reverse('import-semantic-data'),
            {'substitutions': []},
            format='json',
            HTTP_X_INTERNAL_API_KEY='not-the-key',
        )

        assert response.status_code in (401, 403)

    def test_a_payload_with_nothing_in_it_reports_nothing_created(self, api_client):
        response = api_client.post(
            reverse('import-semantic-data'),
            {'substitutions': []},
            format='json',
            HTTP_X_INTERNAL_API_KEY=INTERNAL_KEY,
        )

        assert response.status_code == 201, response.content
        assert response.json()['substitutions_created'] == 0


@pytest.mark.django_db
@pytest.mark.xfail(
    strict=True,
    reason=(
        "The view passes `source=` to `ProductSubstitution`, whose `source` "
        "field is commented out. Every import raises and is reported as a 400. "
        "See this module's docstring."
    ),
)
def test_posted_substitutions_are_created(api_client):
    payload = _substitution(ProductFactory(), ProductFactory())

    response = api_client.post(
        reverse('import-semantic-data'),
        {'substitutions': [payload]},
        format='json',
        HTTP_X_INTERNAL_API_KEY=INTERNAL_KEY,
    )

    assert response.status_code == 201, response.content
    assert response.json()['substitutions_created'] == 1
    assert ProductSubstitution.objects.count() == 1
