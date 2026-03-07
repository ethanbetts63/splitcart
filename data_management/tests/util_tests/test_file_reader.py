import json
import pytest
import tempfile
import os
from data_management.database_updating_classes.product_updating.file_reader import FileReader


def _write_jsonl(path, lines):
    with open(path, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(json.dumps(line) + '\n')


class TestFileReader:
    def test_missing_file_returns_none_and_empty_list(self):
        reader = FileReader('/nonexistent/path/file.jsonl')
        meta, data = reader.read_and_consolidate()
        assert meta is None
        assert data == []

    def test_reads_metadata_from_first_valid_line(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            path = f.name
        try:
            _write_jsonl(path, [
                {'metadata': {'store': 'Test Store', 'company': 'Coles'}, 'product': {'normalized_name_brand_size': 'milk 1l'}},
            ])
            reader = FileReader(path)
            meta, data = reader.read_and_consolidate()
            assert meta == {'store': 'Test Store', 'company': 'Coles'}
        finally:
            os.unlink(path)

    def test_reads_all_unique_products(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            path = f.name
        try:
            _write_jsonl(path, [
                {'metadata': {}, 'product': {'normalized_name_brand_size': 'milk 1l'}},
                {'metadata': {}, 'product': {'normalized_name_brand_size': 'bread 700g'}},
            ])
            reader = FileReader(path)
            _, data = reader.read_and_consolidate()
            assert len(data) == 2
        finally:
            os.unlink(path)

    def test_deduplicates_by_normalized_name_brand_size(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            path = f.name
        try:
            _write_jsonl(path, [
                {'metadata': {}, 'product': {'normalized_name_brand_size': 'milk 1l', 'price': 2.00}},
                {'metadata': {}, 'product': {'normalized_name_brand_size': 'milk 1l', 'price': 2.50}},
            ])
            reader = FileReader(path)
            _, data = reader.read_and_consolidate()
            assert len(data) == 1
            # First occurrence is kept
            assert data[0]['product']['price'] == 2.00
        finally:
            os.unlink(path)

    def test_skips_lines_without_product_key(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            path = f.name
        try:
            _write_jsonl(path, [
                {'metadata': {'store': 'X'}},  # no 'product' key
                {'metadata': {}, 'product': {'normalized_name_brand_size': 'butter 500g'}},
            ])
            reader = FileReader(path)
            _, data = reader.read_and_consolidate()
            assert len(data) == 1
        finally:
            os.unlink(path)

    def test_skips_malformed_json_lines(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            path = f.name
            f.write('not valid json\n')
            f.write(json.dumps({'metadata': {}, 'product': {'normalized_name_brand_size': 'eggs 12pk'}}) + '\n')
        try:
            reader = FileReader(path)
            _, data = reader.read_and_consolidate()
            assert len(data) == 1
        finally:
            os.unlink(path)

    def test_skips_products_without_normalized_name_brand_size(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            path = f.name
        try:
            _write_jsonl(path, [
                {'metadata': {}, 'product': {'name': 'No key here'}},
                {'metadata': {}, 'product': {'normalized_name_brand_size': 'yoghurt 1kg'}},
            ])
            reader = FileReader(path)
            _, data = reader.read_and_consolidate()
            assert len(data) == 1

        finally:
            os.unlink(path)

    def test_empty_file_returns_none_meta_and_empty_list(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            path = f.name
        try:
            reader = FileReader(path)
            meta, data = reader.read_and_consolidate()
            assert meta is None
            assert data == []
        finally:
            os.unlink(path)
