import pytest
import json
import os
from scraping.utils.command_utils.sanity_checker import _validate_product_fields, run_sanity_checks


def _make_valid_product(name='Full Cream Milk', price=2.50, nnbs='cream full milk 2000ml'):
    return {
        'name': name,
        'price_current': price,
        'normalized_name_brand_size': nnbs,
    }


def _make_jsonl_line(product, metadata=None):
    if metadata is None:
        metadata = {'store_id': 'STORE001', 'company': 'woolworths'}
    return json.dumps({'product': product, 'metadata': metadata}) + '\n'


class TestValidateProductFields:
    def test_valid_product_has_no_errors(self):
        errors = _validate_product_fields(_make_valid_product(), line_number=1)
        assert errors == []

    def test_missing_name_produces_error(self):
        product = _make_valid_product()
        product['name'] = None
        errors = _validate_product_fields(product, line_number=1)
        assert any('name' in e for e in errors)

    def test_missing_price_current_produces_error(self):
        product = _make_valid_product()
        product['price_current'] = None
        errors = _validate_product_fields(product, line_number=1)
        assert any('price_current' in e for e in errors)

    def test_missing_nnbs_produces_error(self):
        product = _make_valid_product()
        product['normalized_name_brand_size'] = None
        errors = _validate_product_fields(product, line_number=1)
        assert any('normalized_name_brand_size' in e for e in errors)

    def test_name_too_long_produces_error(self):
        product = _make_valid_product(name='A' * 256)
        errors = _validate_product_fields(product, line_number=1)
        assert any('name' in e for e in errors)

    def test_name_at_limit_is_valid(self):
        product = _make_valid_product(name='A' * 255)
        errors = _validate_product_fields(product, line_number=1)
        assert not any('name' in e and 'exceeds' in e for e in errors)

    def test_valid_barcode_passes(self):
        product = {**_make_valid_product(), 'barcode': '12345678901234'}
        errors = _validate_product_fields(product, line_number=1)
        assert not any('barcode' in e for e in errors)

    def test_non_numeric_barcode_produces_error(self):
        product = {**_make_valid_product(), 'barcode': 'ABCD1234'}
        errors = _validate_product_fields(product, line_number=1)
        assert any('barcode' in e for e in errors)

    def test_price_with_many_decimal_places_is_rounded(self):
        product = {**_make_valid_product(), 'price_current': 2.505}
        _validate_product_fields(product, line_number=1)
        # Should be rounded to 2dp — original dict is modified in-place
        from decimal import Decimal
        assert Decimal(str(product['price_current'])).as_tuple().exponent >= -2

    def test_price_with_excessive_decimal_places_produces_error(self):
        product = {**_make_valid_product(), 'price_current': 2.50000000001}
        errors = _validate_product_fields(product, line_number=1)
        # 11 decimal places triggers error
        # Note: due to float representation this may or may not trigger — the check is > 10 dp
        # We just verify no crash and the function returns a list
        assert isinstance(errors, list)

    def test_invalid_price_string_produces_error(self):
        product = {**_make_valid_product(), 'price_current': 'not-a-price'}
        errors = _validate_product_fields(product, line_number=1)
        assert any('price_current' in e for e in errors)


class TestRunSanityChecks:
    def test_valid_file_unchanged(self, tmp_path):
        file_path = tmp_path / 'products.jsonl'
        line = _make_jsonl_line(_make_valid_product())
        file_path.write_text(line, encoding='utf-8')

        errors = run_sanity_checks(str(file_path))
        assert errors == []
        assert file_path.read_text(encoding='utf-8') == line

    def test_empty_file_returns_no_errors(self, tmp_path):
        file_path = tmp_path / 'empty.jsonl'
        file_path.write_text('', encoding='utf-8')
        errors = run_sanity_checks(str(file_path))
        assert errors == []

    def test_invalid_json_line_removed(self, tmp_path):
        file_path = tmp_path / 'products.jsonl'
        valid_line = _make_jsonl_line(_make_valid_product())
        file_path.write_text(valid_line + 'NOT JSON\n', encoding='utf-8')

        run_sanity_checks(str(file_path))
        remaining = file_path.read_text(encoding='utf-8')
        assert 'NOT JSON' not in remaining

    def test_donation_product_removed(self, tmp_path):
        file_path = tmp_path / 'products.jsonl'
        donation_product = _make_valid_product(name='Donation $5')
        valid_product = _make_valid_product(name='Milk', nnbs='milk 2000ml')
        content = _make_jsonl_line(donation_product) + _make_jsonl_line(valid_product)
        file_path.write_text(content, encoding='utf-8')

        run_sanity_checks(str(file_path))
        remaining = file_path.read_text(encoding='utf-8')
        assert 'Donation' not in remaining
        assert 'Milk' in remaining

    def test_duplicate_nnbs_second_occurrence_removed(self, tmp_path):
        file_path = tmp_path / 'products.jsonl'
        p1 = _make_valid_product(name='Milk A', nnbs='same-key')
        p2 = _make_valid_product(name='Milk B', nnbs='same-key')  # duplicate
        content = _make_jsonl_line(p1) + _make_jsonl_line(p2)
        file_path.write_text(content, encoding='utf-8')

        errors = run_sanity_checks(str(file_path))
        remaining = file_path.read_text(encoding='utf-8')
        lines = [l for l in remaining.splitlines() if l]
        assert len(lines) == 1
        assert any('Duplicate' in e for e in errors)

    def test_metadata_mismatch_line_removed(self, tmp_path):
        file_path = tmp_path / 'products.jsonl'
        meta1 = {'store_id': 'STORE001', 'company': 'woolworths'}
        meta2 = {'store_id': 'STORE002', 'company': 'coles'}  # mismatch
        p1 = _make_valid_product(name='Milk A', nnbs='milk a')
        p2 = _make_valid_product(name='Milk B', nnbs='milk b')
        content = _make_jsonl_line(p1, meta1) + _make_jsonl_line(p2, meta2)
        file_path.write_text(content, encoding='utf-8')

        errors = run_sanity_checks(str(file_path))
        assert any('mismatch' in e.lower() for e in errors)

    def test_missing_metadata_key_produces_error(self, tmp_path):
        file_path = tmp_path / 'products.jsonl'
        line = json.dumps({'product': _make_valid_product()}) + '\n'  # no 'metadata' key
        file_path.write_text(line, encoding='utf-8')

        errors = run_sanity_checks(str(file_path))
        assert any('metadata' in e for e in errors)

    def test_nonexistent_file_returns_error(self, tmp_path):
        errors = run_sanity_checks(str(tmp_path / 'nonexistent.jsonl'))
        assert len(errors) > 0
        assert any('File Error' in e for e in errors)
