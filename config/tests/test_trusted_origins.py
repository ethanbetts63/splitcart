"""Dev origins must reach the dev frontend, and must not reach production.

Two failures live here, and neither announces itself.

The first is a dev frontend on a port nobody listed. Server-rendered pages keep
working, because those fetch from Django process-to-process and never involve a
browser origin; only client-side writes are refused, so the symptom is a toast
saying the cart could not be created. That points at the cart. It happened on
2026-09-25, when the local frontend moved to 3021 because another project in
this family holds 3000.

The list was CORS's then. Since the browser reaches Django only through the
frontend's `/api/*` rewrite there is no CORS, but a write still arrives naming
the frontend in `Origin`, and Django's CSRF check refuses an origin it does not
trust -- the same failure, behind a different setting.

The second is the opposite mistake: the dev origins used to be in the list
unconditionally, so the live API trusted `http://localhost:3000` -- any page on
any machine, writing to production.
"""

import importlib

import pytest


def _settings_with(monkeypatch, debug, ports=None):
    """Import `config.settings` under a chosen DEBUG, and hand back the module.

    The origin lists are built once at import from `DEBUG`, so `override_settings`
    would prove nothing -- it would be inspecting lists that were already decided.
    The suite itself runs under `settings_test`, whose DEBUG is off, so both
    states have to be reached this way rather than read off the active settings.
    """
    monkeypatch.setenv('DEBUG', 'True' if debug else 'False')
    if ports is not None:
        monkeypatch.setenv('DEV_FRONTEND_PORTS', ports)
    import config.settings as module

    return importlib.reload(module)


@pytest.fixture(autouse=True)
def _restore_settings_module():
    """Leave `config.settings` as the suite found it.

    Reloading it is fine while a test holds it, but a module left reloaded under
    a different DEBUG is a booby trap for whatever runs next.
    """
    yield
    import config.settings as module

    importlib.reload(module)


class TestDevOriginsReachTheDevFrontend:
    def test_every_configured_port_gets_both_host_spellings(self, monkeypatch):
        """A browser treats localhost and 127.0.0.1 as different origins.

        Listing one and not the other is the same silent half-failure as
        listing neither, for whichever spelling the developer happens to type.
        """
        dev = _settings_with(monkeypatch, debug=True)
        for port in dev.DEV_FRONTEND_PORTS:
            for host in ('localhost', '127.0.0.1'):
                assert f'http://{host}:{port}' in dev.DEV_FRONTEND_ORIGINS

    def test_the_port_this_repo_actually_runs_on_is_listed(self, monkeypatch):
        dev = _settings_with(monkeypatch, debug=True)
        assert '3021' in dev.DEV_FRONTEND_PORTS, (
            'Another project in this family holds 3000, so splitcart runs its '
            'frontend on 3021. Dropping it silently breaks every client-side write.'
        )

    def test_dev_origins_are_trusted_while_debugging(self, monkeypatch):
        dev = _settings_with(monkeypatch, debug=True)
        assert dev.DEV_FRONTEND_ORIGINS
        for origin in dev.DEV_FRONTEND_ORIGINS:
            assert origin in dev.CSRF_TRUSTED_ORIGINS

    def test_a_new_port_needs_no_code_change(self, monkeypatch):
        """The next port collision should not require editing settings.py.

        The failure this prevents is quiet enough that nobody thinks to look
        here, so reaching for an env var has to be the easier path.
        """
        dev = _settings_with(monkeypatch, debug=True, ports='3000,4173')
        assert 'http://localhost:4173' in dev.CSRF_TRUSTED_ORIGINS
        assert 'http://127.0.0.1:4173' in dev.CSRF_TRUSTED_ORIGINS
        assert 'http://localhost:3001' not in dev.CSRF_TRUSTED_ORIGINS


class TestProductionDoesNotTrustLocalhost:
    def test_no_local_origin_survives_with_debug_off(self, monkeypatch):
        prod = _settings_with(monkeypatch, debug=False)
        trusted = prod.CSRF_TRUSTED_ORIGINS
        offenders = [o for o in trusted if 'localhost' in o or '127.0.0.1' in o]
        assert not offenders, (
            f'Production trusts these local origins: {offenders}. A localhost '
            'origin on the live API is a page on any machine calling production.'
        )

    def test_the_deployed_origins_are_still_there(self, monkeypatch):
        """Gating the dev origins must not gate the real ones out with them."""
        prod = _settings_with(monkeypatch, debug=False)
        assert 'https://www.splitcart.com.au' in prod.CSRF_TRUSTED_ORIGINS


class TestThereIsNoCors:
    def test_no_cross_origin_policy_is_configured(self, monkeypatch):
        """A correctly shaped frontend needs none, and a list that exists is a
        list somebody adds an origin to."""
        for debug in (True, False):
            module = _settings_with(monkeypatch, debug=debug)
            assert not [name for name in dir(module) if name.startswith('CORS_')]
            assert not [m for m in module.MIDDLEWARE if 'corsheaders' in m]
