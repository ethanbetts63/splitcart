"""The root URLconf after the Vite-era routes came out.

The catch-all that used to sit at the bottom of `config/urls.py` rendered a
template out of `frontend/dist`, a directory the Next migration deleted. It
matched every path Django did not route earlier, so every typo'd URL and every
crawler probe raised `TemplateDoesNotExist` and answered 500. This file exists
so that cannot come back quietly.
"""

import pytest
from django.conf import settings
from django.urls import NoReverseMatch, reverse


class TestUnroutedPaths:
    def test_an_unrouted_path_is_a_404(self, client):
        response = client.get('/definitely-not-a-route/')
        assert response.status_code == 404

    def test_an_unrouted_api_path_is_a_404(self, client):
        response = client.get('/api/definitely-not-a-route/')
        assert response.status_code == 404

    def test_the_django_sitemap_is_gone(self, client):
        """The live sitemap is the frontend's `app/sitemap.ts`."""
        response = client.get('/sitemap.xml')
        assert response.status_code == 404


class TestDevelopmentOnlyRoutes:
    """Under `DEBUG=False` -- which the test runner forces -- neither is routed."""

    def test_debug_is_off_for_this_suite(self):
        assert settings.DEBUG is False

    def test_admin_is_not_routed(self, client):
        assert client.get('/admin/').status_code == 404
        with pytest.raises(NoReverseMatch):
            reverse('admin:index')

    def test_the_debug_toolbar_is_not_routed(self, client):
        assert client.get('/__debug__/').status_code == 404


class TestPillarPageRedirect:
    """A 301 that may still have referrers. Kept deliberately -- see
    `_docs/convergence/dead-code.md` DC-3."""

    def test_an_unmapped_slug_redirects_to_the_matching_category(self, client):
        response = client.get('/pillar-pages/pantry/')
        assert response.status_code == 301
        assert response['Location'] == '/categories/pantry/'

    def test_a_renamed_slug_is_translated(self, client):
        response = client.get('/pillar-pages/eggs-and-dairy/')
        assert response.status_code == 301
        assert response['Location'] == '/categories/dairy-and-eggs/'
