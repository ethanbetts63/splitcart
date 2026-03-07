from unittest.mock import MagicMock
from data_management.utils.analysis_utils.store_grouping_utils.grouping import find_store_groups


def _store(name):
    s = MagicMock()
    s.store_name = name
    return s


class TestFindStoreGroups:
    def test_single_store_is_an_island(self):
        store = _store('A')
        store_map = {1: store}
        graph = {1: []}
        groups, islands = find_store_groups(store_map, graph)
        assert groups == []
        assert store in islands

    def test_two_connected_stores_form_one_group(self):
        a, b = _store('A'), _store('B')
        store_map = {1: a, 2: b}
        graph = {1: [2], 2: [1]}
        groups, islands = find_store_groups(store_map, graph)
        assert len(groups) == 1
        assert set(groups[0]) == {a, b}
        assert islands == []

    def test_two_disconnected_stores_are_both_islands(self):
        a, b = _store('A'), _store('B')
        store_map = {1: a, 2: b}
        graph = {1: [], 2: []}
        groups, islands = find_store_groups(store_map, graph)
        assert groups == []
        assert set(islands) == {a, b}

    def test_two_separate_groups(self):
        a, b, c, d = _store('A'), _store('B'), _store('C'), _store('D')
        store_map = {1: a, 2: b, 3: c, 4: d}
        graph = {1: [2], 2: [1], 3: [4], 4: [3]}
        groups, islands = find_store_groups(store_map, graph)
        assert len(groups) == 2
        assert islands == []

    def test_three_stores_fully_connected(self):
        a, b, c = _store('A'), _store('B'), _store('C')
        store_map = {1: a, 2: b, 3: c}
        graph = {1: [2, 3], 2: [1, 3], 3: [1, 2]}
        groups, islands = find_store_groups(store_map, graph)
        assert len(groups) == 1
        assert set(groups[0]) == {a, b, c}
        assert islands == []

    def test_mixed_group_and_island(self):
        a, b, c = _store('A'), _store('B'), _store('C')
        store_map = {1: a, 2: b, 3: c}
        # A and B are connected; C is isolated
        graph = {1: [2], 2: [1], 3: []}
        groups, islands = find_store_groups(store_map, graph)
        assert len(groups) == 1
        assert set(groups[0]) == {a, b}
        assert c in islands

    def test_empty_store_map(self):
        groups, islands = find_store_groups({}, {})
        assert groups == []
        assert islands == []
