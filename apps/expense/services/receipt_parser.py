import re
from datetime import datetime

def parse_receipt(text: str) -> dict:
 
    vendor = re.search(r'(?:Vendor|Shop|Store|From):\s*(.+)', text, re.I)
    vendor = vendor.group(1).strip() if vendor else None

    
    date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
    expense_date = date_match.group(1) if date_match else None
    if expense_date:
        try:
            expense_date = datetime.strptime(expense_date, '%d/%m/%Y').date()
        except:
            try:
                expense_date = datetime.strptime(expense_date, '%m/%d/%Y').date()
            except:
                expense_date = None

     
    amount_match = re.search(r'(?:Rs\.?|NPR)\s*([\d,]+\.\d{2})', text, re.I)
    amount = float(amount_match.group(1).replace(',', '')) if amount_match else None

    
    category = None
    categories = {'groceries': ['grocery', 'supermarket', 'bhat-bhateni'],
                  'transport': ['taxi', 'bus', 'fuel', 'petrol'],
                  'utilities': ['electricity', 'water', 'internet']}
    for cat, keywords in categories.items():
        if any(kw in text.lower() for kw in keywords):
            category = cat
            break

    return {
        'vendor': vendor or 'Unknown',
        'expense_date': expense_date,
        'category': category or 'Other',
        'amount': amount or 0.0,
    }