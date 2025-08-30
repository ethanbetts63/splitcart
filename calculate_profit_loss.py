import csv
from datetime import datetime, timedelta
from collections import deque
import copy

def calculate_profit_loss(file_path):
    trades = {}
    report_lines = []
    total_profit_loss_aud = 0.0

    exchange_rates = {
        # 2024
        (2024, 1): 1.503326, (2024, 2): 1.531660, (2024, 3): 1.525368,
        (2024, 4): 1.536743, (2024, 5): 1.509867, (2024, 6): 1.505732,
        (2024, 7): 1.497142, (2024, 8): 1.504728, (2024, 9): 1.477913,
        (2024, 10): 1.489537, (2024, 11): 1.530639, (2024, 12): 1.578714,
        # 2025
        (2025, 1): 1.606886, (2025, 2): 1.587388, (2025, 3): 1.588621,
        (2025, 4): 1.592313, (2025, 5): 1.553789, (2025, 6): 1.539542,
        (2025, 7): 1.527592, (2025, 8): 1.539875,
    }
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [name.strip() for name in reader.fieldnames]

        for row in reader:
            trade_date_str = row.get('Trade Date')
            instrument = row.get('Instrument Code')
            market = row.get('Market Code', 'N/A').upper()
            if not trade_date_str or not instrument:
                continue

            try:
                trade_date = datetime.strptime(trade_date_str, '%Y-%m-%d')
                stock_key = (instrument, market)

                if stock_key not in trades:
                    trades[stock_key] = {'buys': deque(), 'sells': []}
                
                transaction = {
                    'date': trade_date,
                    'quantity': float(row['Quantity']),
                    'price': float(row['Price']),
                    'brokerage': float(row.get('Brokerage', 0)),
                    'currency': row.get('Brokerage Currency', 'N/A').upper()
                }

                if row['Transaction Type'].upper() == 'BUY':
                    trades[stock_key]['buys'].append(transaction)
                elif row['Transaction Type'].upper() == 'SELL':
                    trades[stock_key]['sells'].append(transaction)

            except (ValueError, KeyError) as e:
                report_lines.append(f"Skipping row due to error: {row} - {e}")
                continue

    # Updated to 2025 Financial Year
    start_date = datetime(2024, 7, 1)
    end_date = datetime(2025, 6, 30)

    sorted_stock_keys = sorted(trades.keys())

    for stock_key in sorted_stock_keys:
        instrument, market = stock_key
        data = trades[stock_key]
        sells_in_range = [s for s in data['sells'] if start_date <= s['date'] <= end_date]
        
        if not sells_in_range:
            continue

        report_lines.append(f"\n\n========================================")
        report_lines.append(f"Stock: {instrument} ({market})")
        report_lines.append(f"========================================")

        buys_for_processing = copy.deepcopy(data['buys'])

        report_lines.append(f"\n--- Full Purchase History ---")
        if not buys_for_processing:
            report_lines.append("  No purchase transactions found.")
        else:
            for buy in buys_for_processing:
                report_lines.append(f"  - BOUGHT {buy['quantity']:.4f} on {buy['date'].date()} at {buy['price']:.2f} {buy['currency']}")

        for sell in sorted(sells_in_range, key=lambda x: x['date']):
            sell_quantity = sell['quantity']
            sell_price = sell['price']
            sell_brokerage = sell['brokerage']
            sell_currency = sell['currency']
            
            proceeds = (sell_quantity * sell_price) - sell_brokerage
            cost_basis_principal = 0
            cost_basis_brokerage = 0
            
            report_lines.append(f"\n--- Analyzing Sale of {sell_quantity} on {sell['date'].date()} ---")

            quantity_to_sell = sell_quantity
            
            while quantity_to_sell > 0 and buys_for_processing:
                buy = buys_for_processing[0]
                
                if buy['date'] > sell['date']:
                    break

                holding_period = sell['date'] - buy['date']
                term_status = "(Long-term)" if holding_period > timedelta(days=365) else "(Short-term)"

                if quantity_to_sell >= buy['quantity']:
                    buy_lot_quantity = buy['quantity']
                    cost_basis_principal += buy_lot_quantity * buy['price']
                    cost_basis_brokerage += buy['brokerage']
                    quantity_to_sell -= buy_lot_quantity
                    buys_for_processing.popleft()
                    report_lines.append(f"  - Sold {buy_lot_quantity:.4f} shares from {buy['date'].date()} {term_status}")
                else:
                    brokerage_for_partial = buy['brokerage'] * (quantity_to_sell / buy['quantity'])
                    cost_basis_principal += quantity_to_sell * buy['price']
                    cost_basis_brokerage += brokerage_for_partial
                    buy['quantity'] -= quantity_to_sell
                    report_lines.append(f"  - Sold {quantity_to_sell:.4f} shares from {buy['date'].date()} {term_status}")
                    quantity_to_sell = 0

            if quantity_to_sell > 0:
                report_lines.append(f"  Warning: Not enough buy history for this sale. {quantity_to_sell} shares unaccounted for.")

            total_cost_basis = cost_basis_principal + cost_basis_brokerage
            profit_loss = proceeds - total_cost_basis
            
            rate_key = (sell['date'].year, sell['date'].month)
            usd_to_aud_rate = exchange_rates.get(rate_key, 1.0)

            profit_loss_aud = profit_loss * usd_to_aud_rate if sell_currency == 'USD' else profit_loss
            total_profit_loss_aud += profit_loss_aud

            aud_conversion_str = f" ({proceeds * usd_to_aud_rate:.2f} AUD)" if sell_currency == 'USD' else ""
            report_lines.append(f"  Total Proceeds: {proceeds:.2f} {sell_currency}{aud_conversion_str}")
            
            cost_breakdown_str = f"({cost_basis_principal:.2f} principal + {cost_basis_brokerage:.2f} brokerage)"
            aud_conversion_str = f" ({total_cost_basis * usd_to_aud_rate:.2f} AUD)" if sell_currency == 'USD' else ""
            report_lines.append(f"  Total Cost Basis: {total_cost_basis:.2f} {sell_currency} {cost_breakdown_str}{aud_conversion_str}")

            aud_conversion_str = f" ({profit_loss_aud:.2f} AUD)" if sell_currency == 'USD' else ""
            report_lines.append(f"  Profit/Loss: {profit_loss:.2f} {sell_currency}{aud_conversion_str}")

    report_lines.append(f"\n\n========================================")
    report_lines.append(f"         Overall Summary for FY 2025")
    report_lines.append(f"       (1 July 2024 - 30 June 2025)")
    report_lines.append(f"========================================")
    report_lines.append(f"Total Profit/Loss for Period: {total_profit_loss_aud:.2f} AUD")

    report_lines.append(f"\n\n========================================")
    report_lines.append(f"        USD to AUD Rates Used")
    report_lines.append(f"========================================")
    for (year, month), rate in sorted(exchange_rates.items()):
        report_lines.append(f"  {year}-{month:02d}: {rate}")

    with open('profit_loss_report.txt', 'w') as f:
        for line in report_lines:
            f.write(line + '\n')

if __name__ == "__main__":
    calculate_profit_loss('C:\\Users\\ethan\\coding\\splitcart\\TradeHistory_2706934239_6_20230830-20250830_20250830161332 (1).csv')