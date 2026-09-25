"""`--dev` must be pointable, not hardcoded to port 8000.

The local half of this pipeline talks to "the server" over HTTP, and `--dev`
selects a local one. That address used to be the literal string
`http://127.0.0.1:8000` written out in five separate modules.

That is fine right up until another project in this family is already holding
port 8000 -- which happened on 2026-09-25, when allbikes had it. `--dev` then
does not fail. It uploads one site's scraped catalogue into another site's
inbox, over an API key the other end accepts, and reports success.

So the address is a setting with the old literal as its default: existing
workflows are unchanged, and a second local server is reachable by setting
DEV_API_SERVER_URL.
"""

from unittest.mock import MagicMock, patch

from django.test import override_settings

from scraping.utils.command_utils.base_uploader import BaseUploader


class TestDevServerUrl:
    def test_dev_uses_the_configured_local_server(self):
        with override_settings(DEV_API_SERVER_URL='http://127.0.0.1:8021'):
            uploader = BaseUploader(MagicMock(), dev=True)
            assert uploader.get_server_url() == 'http://127.0.0.1:8021'

    def test_the_default_is_the_address_this_replaced(self):
        """Nobody who already runs on 8000 has to change anything."""
        from django.conf import settings

        assert settings.DEV_API_SERVER_URL == 'http://127.0.0.1:8000' or (
            'DEV_API_SERVER_URL' in __import__('os').environ
        ), 'The default must stay 8000 unless the environment overrides it.'

    def test_without_dev_it_still_uses_the_real_server(self):
        with override_settings(
            API_SERVER_URL='https://api.example.com/',
            DEV_API_SERVER_URL='http://127.0.0.1:8021',
        ):
            uploader = BaseUploader(MagicMock(), dev=False)
            assert uploader.get_server_url() == 'https://api.example.com/'

    def test_no_module_hardcodes_the_dev_address_any_more(self):
        """The point of the setting is that there is one of it.

        Five copies of a magic string is five places to forget, and the failure
        is silent in every one of them.
        """
        import pathlib

        root = pathlib.Path(__file__).resolve().parents[2].parent
        offenders = []
        for path in root.rglob('*.py'):
            parts = set(path.parts)
            if parts & {'venv', '__pycache__', 'tests', 'migrations'}:
                continue
            text = path.read_text(encoding='utf-8', errors='ignore')
            for lineno, line in enumerate(text.splitlines(), 1):
                if '127.0.0.1:8000' not in line:
                    continue
                # settings.py declares the default and explains it; the CSRF
                # trusted-origins list is a different concern entirely.
                if path.name == 'settings.py':
                    continue
                offenders.append(f'{path.relative_to(root)}:{lineno}')

        assert not offenders, (
            'These modules hardcode the dev server address instead of reading '
            f'settings.DEV_API_SERVER_URL: {offenders}'
        )
