from unittest.mock import MagicMock
from data_management.utils.analysis_utils.store_grouping_utils.graph_construction import build_correlation_graph


def _store(name):
    s = MagicMock()
    s.store_name = name
    return s


class TestBuildCorrelationGraph:
    def test_single_store_graph_has_no_edges(self):
        store_map = {1: _store('A')}
        price_data = {1: {101: 5.00}}
        graph = build_correlation_graph(store_map, price_data, threshold=98)
        assert graph == {1: []}

    def test_identical_prices_above_threshold_creates_edge(self):
        store_map = {1: _store('A'), 2: _store('B')}
        prices = {i: 5.00 for i in range(10)}
        price_data = {1: prices.copy(), 2: prices.copy()}
        graph = build_correlation_graph(store_map, price_data, threshold=98)
        assert 2 in graph[1]
        assert 1 in graph[2]

    def test_no_common_products_creates_no_edge(self):
        store_map = {1: _store('A'), 2: _store('B')}
        price_data = {1: {1: 5.00}, 2: {2: 5.00}}
        graph = build_correlation_graph(store_map, price_data, threshold=50)
        assert graph[1] == []
        assert graph[2] == []

    def test_low_correlation_below_threshold_no_edge(self):
        store_map = {1: _store('A'), 2: _store('B')}
        # 50% matching prices (5 out of 10 match)
        shared = {i: 5.00 for i in range(5)}
        a_only = {i + 5: 3.00 for i in range(5)}
        b_only = {i + 5: 9.00 for i in range(5)}
        price_data = {1: {**shared, **a_only}, 2: {**shared, **b_only}}
        graph = build_correlation_graph(store_map, price_data, threshold=98)
        assert graph[1] == []
        assert graph[2] == []

    def test_exactly_at_threshold_creates_edge(self):
        # 98 out of 100 products identical = 98% correlation
        store_map = {1: _store('A'), 2: _store('B')}
        prices_a = {i: 5.00 for i in range(100)}
        prices_b = prices_a.copy()
        prices_b[0] = 9.00
        prices_b[1] = 9.00
        price_data = {1: prices_a, 2: prices_b}
        graph = build_correlation_graph(store_map, price_data, threshold=98)
        assert 2 in graph[1]

    def test_graph_has_all_store_ids_as_keys(self):
        store_map = {1: _store('A'), 2: _store('B'), 3: _store('C')}
        price_data = {1: {1: 1.00}, 2: {2: 2.00}, 3: {3: 3.00}}
        graph = build_correlation_graph(store_map, price_data, threshold=98)
        assert set(graph.keys()) == {1, 2, 3}

    def test_edges_are_bidirectional(self):
        store_map = {1: _store('A'), 2: _store('B')}
        prices = {i: 5.00 for i in range(10)}
        price_data = {1: prices.copy(), 2: prices.copy()}
        graph = build_correlation_graph(store_map, price_data, threshold=98)
        assert 2 in graph[1]
        assert 1 in graph[2]
