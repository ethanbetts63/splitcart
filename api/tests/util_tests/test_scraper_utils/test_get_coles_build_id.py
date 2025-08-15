
from django.test import TestCase
from unittest.mock import patch, Mock
from api.utils.scraper_utils.get_coles_build_id import get_coles_build_id

class GetColesBuildIdTest(TestCase):

    @patch('api.utils.scraper_utils.get_coles_build_id.webdriver.Chrome')
    @patch('api.utils.scraper_utils.get_coles_build_id.time.sleep')
    def test_get_build_id_success(self, mock_sleep, mock_chrome):
        """Test that the build ID is successfully extracted from the page source."""
        mock_driver = Mock()
        mock_driver.page_source = '<html><body><script src="/_next/static/BUILD_ID_123/_buildManifest.js"></script></body></html>'
        mock_chrome.return_value = mock_driver

        build_id = get_coles_build_id()

        self.assertEqual(build_id, 'BUILD_ID_123')
        mock_driver.get.assert_called_once_with("https://www.coles.com.au/browse/fruit-vegetables")
        mock_driver.quit.assert_called_once()

    @patch('api.utils.scraper_utils.get_coles_build_id.webdriver.Chrome')
    @patch('api.utils.scraper_utils.get_coles_build_id.time.sleep')
    def test_get_build_id_not_found(self, mock_sleep, mock_chrome):
        """Test that None is returned when the build ID is not found in the page source."""
        mock_driver = Mock()
        mock_driver.page_source = '<html><body><p>No build ID here.</p></body></html>'
        mock_chrome.return_value = mock_driver

        build_id = get_coles_build_id()

        self.assertIsNone(build_id)
        mock_driver.quit.assert_called_once()

    @patch('api.utils.scraper_utils.get_coles_build_id.webdriver.Chrome')
    @patch('api.utils.scraper_utils.get_coles_build_id.time.sleep')
    def test_selenium_exception(self, mock_sleep, mock_chrome):
        """Test that None is returned and the driver is quit when a Selenium exception occurs."""
        mock_driver = Mock()
        mock_driver.get.side_effect = Exception("Selenium error")
        mock_chrome.return_value = mock_driver

        build_id = get_coles_build_id()

        self.assertIsNone(build_id)
        mock_driver.quit.assert_called_once()
