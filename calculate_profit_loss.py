import csv
from datetime import datetime, timedelta
from collections import deque
import copy

def calculate_profit_loss(file_path):
    trades = {}
    report_lines = []
    total_profit_loss_aud = 0.0
    usd_to_aud_rate = 1.53
    
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
                
                # Use a tuple of (instrument, market) as the unique key
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

    start_date = datetime(2024, 8, 30)
    end_date = datetime(2025, 8, 30)

    # Sort by the tuple key (instrument, market)
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
            cost_basis = 0
            
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
                    cost_basis += (buy_lot_quantity * buy['price']) + buy['brokerage']
                    quantity_to_sell -= buy_lot_quantity
                    buys_for_processing.popleft()
                    report_lines.append(f"  - Sold {buy_lot_quantity:.4f} shares from {buy['date'].date()} {term_status}")
                else:
                    brokerage_for_partial = buy['brokerage'] * (quantity_to_sell / buy['quantity'])
                    cost_basis += (quantity_to_sell * buy['price']) + brokerage_for_partial
                    buy['quantity'] -= quantity_to_sell
                    report_lines.append(f"  - Sold {quantity_to_sell:.4f} shares from {buy['date'].date()} {term_status}")
                    quantity_to_sell = 0

            if quantity_to_sell > 0:
                report_lines.append(f"  Warning: Not enough buy history for this sale. {quantity_to_sell} shares unaccounted for.")

            profit_loss = proceeds - cost_basis
            profit_loss_aud = profit_loss * usd_to_aud_rate if sell_currency == 'USD' else profit_loss
            total_profit_loss_aud += profit_loss_aud

            aud_conversion_str = f" ({proceeds * usd_to_aud_rate:.2f} AUD)" if sell_currency == 'USD' else ""
            report_lines.append(f"  Total Proceeds: {proceeds:.2f} {sell_currency}{aud_conversion_str}")
            
            aud_conversion_str = f" ({cost_basis * usd_to_aud_rate:.2f} AUD)" if sell_currency == 'USD' else ""
            report_lines.append(f"  Total Cost Basis: {cost_basis:.2f} {sell_currency}{aud_conversion_str}")

            aud_conversion_str = f" ({profit_loss_aud:.2f} AUD)" if sell_currency == 'USD' else ""
            report_lines.append(f"  Profit/Loss: {profit_loss:.2f} {sell_currency}{aud_conversion_str}")

    report_lines.append(f"\n\n========================================")
    report_lines.append(f"         Overall Summary")
    report_lines.append(f"========================================")
    report_lines.append(f"Total Profit/Loss for Period: {total_profit_loss_aud:.2f} AUD")

    with open('profit_loss_report.txt', 'w') as f:
        for line in report_lines:
            f.write(line + '\n')

if __name__ == "__main__":
    calculate_profit_loss('C:\\Users\\ethan\\coding\\splitcart\\TradeHistory_2706934239_6_20230830-20250830_20250830161332 (1).csv')