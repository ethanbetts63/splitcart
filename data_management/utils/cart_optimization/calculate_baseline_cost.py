def calculate_baseline_cost(slots):
    """Calculates the baseline cost by summing the average price of each item across all stores."""
    if not slots:
        return 0

    total_baseline_cost = 0
    for slot in slots:
        if slot:  # Ensure the slot is not empty
            prices = [opt['price'] for opt in slot]
            average_price = sum(prices) / len(prices)
            total_baseline_cost += average_price
            
    return total_baseline_cost