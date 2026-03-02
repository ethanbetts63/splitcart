import pytest
import json
import os
from unittest.mock import patch
from scraping.utils.product_scraping_utils.jsonl_writer import JsonlWriter


@pytest.fixture
def writer(tmp_path):
    outbox = tmp_path / 'outbox'
    outbox.mkdir()
    with patch('scraping.utils.product_scraping_utils.jsonl_writer.settings') as mock_settings:
        mock_settings.BASE_DIR = str(tmp_path)
        w = JsonlWriter('test', 'test-store', 'nsw', final_outbox_path=str(outbox))
    return w


class TestJsonlWriterWriteProduct:
    def test_returns_false_when_not_open(self, tmp_path):
        outbox = tmp_path / 'outbox'
        outbox.mkdir()
        with patch('scraping.utils.product_scraping_utils.jsonl_writer.settings') as mock_settings:
            mock_settings.BASE_DIR = str(tmp_path)
            writer = JsonlWriter('test', 'test-store', 'nsw', final_outbox_path=str(outbox))
        result = writer.write_product({'normalized_name_brand_size': 'milk'}, {})
        assert result is False

    def test_returns_true_on_first_write(self, writer, tmp_path):
        with patch('scraping.utils.product_scraping_utils.jsonl_writer.settings') as mock_settings:
            mock_settings.BASE_DIR = str(tmp_path)
            writer.open()
        try:
            result = writer.write_product({'normalized_name_brand_size': 'milk whole 2000ml'}, {})
            assert result is True
        finally:
            writer.close()

    def test_returns_false_on_duplicate_key(self, writer, tmp_path):
        with patch('scraping.utils.product_scraping_utils.jsonl_writer.settings') as mock_settings:
            mock_settings.BASE_DIR = str(tmp_path)
            writer.open()
        try:
            writer.write_product({'normalized_name_brand_size': 'milk whole 2000ml'}, {})
            result = writer.write_product({'normalized_name_brand_size': 'milk whole 2000ml'}, {})
            assert result is False
        finally:
            writer.close()

    def test_returns_false_when_no_key(self, writer, tmp_path):
        with patch('scraping.utils.product_scraping_utils.jsonl_writer.settings') as mock_settings:
            mock_settings.BASE_DIR = str(tmp_path)
            writer.open()
        try:
            result = writer.write_product({'name': 'Milk'}, {})  # no normalized_name_brand_size
            assert result is False
        finally:
            writer.close()

    def test_written_line_is_valid_json(self, tmp_path):
        outbox = tmp_path / 'outbox'
        outbox.mkdir()
        with patch('scraping.utils.product_scraping_utils.jsonl_writer.settings') as mock_settings:
            mock_settings.BASE_DIR = str(tmp_path)
            writer = JsonlWriter('test', 'test-store', 'nsw', final_outbox_path=str(outbox))
            writer.open()
        try:
            writer.write_product({'normalized_name_brand_size': 'milk', 'price_current': 2.50}, {'store_id': 'S001'})
        finally:
            writer.close()

        with open(writer.temp_file_path, 'r') as f:
            line = f.readline()
        data = json.loads(line)
        assert data['product']['normalized_name_brand_size'] == 'milk'
        assert data['metadata']['store_id'] == 'S001'


class TestJsonlWriterCommit:
    def test_commit_moves_file_to_outbox(self, tmp_path):
        outbox = tmp_path / 'outbox'
        outbox.mkdir()
        with patch('scraping.utils.product_scraping_utils.jsonl_writer.settings') as mock_settings:
            mock_settings.BASE_DIR = str(tmp_path)
            writer = JsonlWriter('coles', 'store-001', 'nsw', final_outbox_path=str(outbox))
            writer.open()
        writer.write_product({'normalized_name_brand_size': 'milk'}, {})
        temp_path = writer.temp_file_path
        writer.commit()
        assert not os.path.exists(temp_path)
        assert len(list(outbox.iterdir())) == 1


class TestJsonlWriterCleanup:
    def test_cleanup_removes_temp_file(self, tmp_path):
        outbox = tmp_path / 'outbox'
        outbox.mkdir()
        with patch('scraping.utils.product_scraping_utils.jsonl_writer.settings') as mock_settings:
            mock_settings.BASE_DIR = str(tmp_path)
            writer = JsonlWriter('coles', 'store-001', 'nsw', final_outbox_path=str(outbox))
            writer.open()
        writer.cleanup()
        assert not os.path.exists(writer.temp_file_path)
