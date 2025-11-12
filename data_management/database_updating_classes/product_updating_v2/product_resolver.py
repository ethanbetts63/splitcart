class ProductResolver:
    """
    Matches incoming product data against existing database records
    using the provided global caches.
    """
    def __init__(self, global_caches):
        self.global_caches = global_caches
        self.raw_data_for_create = []
        self.raw_data_for_update = []

    def resolve_products(self, product_data_list):
        pass
