from data_management.utils.deduplication_utils.substitution_deduplicator import deduplicate_substitutions


class TestDeduplicateSubstitutions:
    def test_empty_input_returns_empty(self):
        assert deduplicate_substitutions([]) == []

    def test_single_entry_is_preserved(self):
        subs = [{'product_a': 1, 'product_b': 2}]
        assert deduplicate_substitutions(subs) == subs

    def test_no_duplicates_are_all_preserved(self):
        subs = [
            {'product_a': 1, 'product_b': 2},
            {'product_a': 3, 'product_b': 4},
        ]
        result = deduplicate_substitutions(subs)
        assert len(result) == 2

    def test_direct_duplicate_is_removed(self):
        subs = [
            {'product_a': 1, 'product_b': 2},
            {'product_a': 1, 'product_b': 2},
        ]
        result = deduplicate_substitutions(subs)
        assert len(result) == 1

    def test_symmetrical_duplicate_is_removed(self):
        subs = [
            {'product_a': 1, 'product_b': 2},
            {'product_a': 2, 'product_b': 1},
        ]
        result = deduplicate_substitutions(subs)
        assert len(result) == 1

    def test_first_occurrence_is_kept(self):
        original = {'product_a': 1, 'product_b': 2, 'extra': 'data'}
        subs = [original, {'product_a': 2, 'product_b': 1}]
        result = deduplicate_substitutions(subs)
        assert result[0] is original

    def test_malformed_entry_missing_key_is_skipped(self):
        subs = [
            {'product_a': 1},  # missing product_b
            {'product_a': 1, 'product_b': 2},
        ]
        result = deduplicate_substitutions(subs)
        assert len(result) == 1
        assert result[0]['product_b'] == 2

    def test_malformed_entry_unhashable_is_skipped(self):
        subs = [
            {'product_a': [1, 2], 'product_b': 3},  # list is unhashable
            {'product_a': 1, 'product_b': 2},
        ]
        result = deduplicate_substitutions(subs)
        assert len(result) == 1

    def test_multiple_symmetrical_pairs(self):
        subs = [
            {'product_a': 1, 'product_b': 2},
            {'product_a': 2, 'product_b': 1},
            {'product_a': 3, 'product_b': 4},
            {'product_a': 4, 'product_b': 3},
        ]
        result = deduplicate_substitutions(subs)
        assert len(result) == 2
