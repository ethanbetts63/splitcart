import json
from unittest.mock import MagicMock, patch

from scraping.scrapers.barcode_scraper_coles_v2 import ColesBarcodeScraperV2


def test_barcode_scraper_does_not_load_translation_tables(tmp_path):
    source_file = tmp_path / "coles.jsonl"
    source_file.write_text(
        json.dumps({
            "product": {"sku": 123, "normalized_name_brand_size": "test"},
            "metadata": {"company": "coles", "scraped_date": "2026-06-29"},
        }) + "\n",
        encoding="utf-8",
    )

    with patch("scraping.scrapers.base_product_scraper.BaseDataCleaner._load_translation_tables") as load_tables:
        scraper = ColesBarcodeScraperV2(
            command=MagicMock(),
            source_file_path=str(source_file),
            session_manager=MagicMock(),
        )

    load_tables.assert_not_called()
    assert scraper.brand_translations == {}
    assert scraper.product_translations == {}
