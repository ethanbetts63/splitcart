def get_graphql_query(latitude, longitude):
    """Returns the GraphQL query payload."""
    return {
        "operationName": "GetStores",
        "variables": {
            "brandIds": ["COL", "LQR", "VIN"],
            "latitude": latitude,
            "longitude": longitude
        },
        "query": "query GetStores($brandIds: [BrandId!], $latitude: Float!, $longitude: Float!) {\n  stores(brandIds: $brandIds, latitude: $latitude, longitude: $longitude) {\n    results {\n      store {\n        id\n        name\n        address {\n          state\n          suburb\n          addressLine\n          postcode\n        }\n        position {\n          latitude\n          longitude\n        }\n        brand {\n          name\n          storeFinderId\n          id\n        }\n        phone\n        isTrading\n        services {\n          name\n        }\n      }\n    }\n  }\n}"
    }