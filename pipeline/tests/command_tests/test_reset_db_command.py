from django.core.management import call_command

from pipeline.management.commands.reset_db import Command


BASE = 'pipeline.management.commands.reset_db'


class FakeCursor:
    def __init__(self):
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query):
        self.queries.append(query)


class FakeIntrospection:
    def table_names(self, cursor):
        return ['example_table']


class FakeConnection:
    introspection = FakeIntrospection()

    def __init__(self):
        self.cursor_instance = FakeCursor()

    def cursor(self):
        return self.cursor_instance


class TestResetDbCommand:
    def test_reset_replays_companies_before_products(self, monkeypatch):
        calls = []
        fake_connection = FakeConnection()

        monkeypatch.setattr(f'{BASE}.connection', fake_connection)
        monkeypatch.setattr(f'{BASE}.call_command', lambda *args, **kwargs: calls.append((args, kwargs)))
        monkeypatch.setattr(Command, '_clear_pycache', lambda self: calls.append((('clear_pycache',), {})))
        monkeypatch.setattr(Command, '_reset_scraping_data', lambda self: calls.append((('reset_scraping_data',), {})))
        monkeypatch.setattr(Command, '_run_git_pull', lambda self: calls.append((('git_pull',), {})))

        call_command('reset_db')

        assert fake_connection.cursor_instance.queries == [
            'SET FOREIGN_KEY_CHECKS = 0',
            'DROP TABLE IF EXISTS `example_table`',
            'SET FOREIGN_KEY_CHECKS = 1',
        ]
        assert calls == [
            (('clear_pycache',), {}),
            (('migrate',), {}),
            (('reset_scraping_data',), {}),
            (('update',), {'companies': True, 'archive': True}),
            (('update',), {'products': True, 'archive': True}),
            (('generate',), {'primary_cats': True}),
            (('generate',), {'pillars': True}),
            (('generate',), {'bargain_stats': True}),
            (('generate',), {'price_comps': True}),
            (('generate',), {'price_summaries': True}),
            (('generate',), {'default_companies': True}),
        ]

    def test_server_reset_pulls_and_skips_local_cleanup(self, monkeypatch):
        calls = []

        monkeypatch.setattr(f'{BASE}.connection', FakeConnection())
        monkeypatch.setattr(f'{BASE}.call_command', lambda *args, **kwargs: calls.append((args, kwargs)))
        monkeypatch.setattr(Command, '_clear_pycache', lambda self: calls.append((('clear_pycache',), {})))
        monkeypatch.setattr(Command, '_reset_scraping_data', lambda self: calls.append((('reset_scraping_data',), {})))
        monkeypatch.setattr(Command, '_run_git_pull', lambda self: calls.append((('git_pull',), {})))

        call_command('reset_db', server=True)

        assert (('git_pull',), {}) in calls
        assert (('clear_pycache',), {}) not in calls
        assert (('reset_scraping_data',), {}) not in calls
        assert calls.index((('update',), {'companies': True, 'archive': True})) < calls.index((('update',), {'products': True, 'archive': True}))
