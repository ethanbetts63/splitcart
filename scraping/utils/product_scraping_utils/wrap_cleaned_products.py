from datetime import datetime

def wrap_cleaned_products(products: list, company: str, store_name: str, store_id: str, state: str, timestamp: datetime) -> dict:
    """
    Wraps a list of cleaned product dictionaries with metadata.
    """
    return {
        "metadata": {
            "company": company.lower().strip(),
            "store_name": store_name.lower().strip(),
            "store_id": store_id.strip(),
            "state": state.lower().strip(),
            "scraped_date": timestamp.date().isoformat()
        },
        "products": products
    }