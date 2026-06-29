from datetime import datetime

def wrap_cleaned_products(products: list, company: str, store_name: str, store_id: str, state: str, timestamp: datetime) -> dict:
    """
    Wraps a list of cleaned product dictionaries with metadata.
    """
    return {
        "metadata": {
            "company": company.lower().strip(),
            "scraped_date": timestamp.date().isoformat()
        },
        "products": products
    }
