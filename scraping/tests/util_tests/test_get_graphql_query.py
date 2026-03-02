import pytest
from scraping.utils.shop_scraping_utils.get_graphql_query import get_graphql_query


class TestGetGraphqlQuery:
    def test_returns_dict(self):
        result = get_graphql_query(-33.87, 151.21)
        assert isinstance(result, dict)

    def test_operation_name(self):
        result = get_graphql_query(-33.87, 151.21)
        assert result['operationName'] == 'GetStores'

    def test_variables_contain_latitude(self):
        result = get_graphql_query(-33.87, 151.21)
        assert result['variables']['latitude'] == -33.87

    def test_variables_contain_longitude(self):
        result = get_graphql_query(-33.87, 151.21)
        assert result['variables']['longitude'] == 151.21

    def test_variables_contain_brand_ids(self):
        result = get_graphql_query(-33.87, 151.21)
        assert 'COL' in result['variables']['brandIds']
        assert 'LQR' in result['variables']['brandIds']
        assert 'VIN' in result['variables']['brandIds']

    def test_query_string_present(self):
        result = get_graphql_query(-33.87, 151.21)
        assert 'query' in result
        assert 'GetStores' in result['query']
