import re
import json
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

 
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def extract_receipt_regex(text: str) -> Dict[str, Any]:
    
    result = {}
 
    vendor_match = re.search(r'(?:Vendor|Shop|Store|From|Seller):\s*(.+)', text, re.I)
    result['vendor'] = vendor_match.group(1).strip() if vendor_match else None

 
    date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
    if date_match:
        result['date'] = date_match.group(1)
    else:
        result['date'] = None

 
    amount_match = re.search(r'(?:Total|Grand Total|Amount|Due):\s*[$€£]?([\d,]+\.\d{2})', text, re.I)
    if amount_match:
        result['total'] = float(amount_match.group(1).replace(',', ''))
    else:
        result['total'] = None

 
    tax_match = re.search(r'(?:Tax|VAT|GST):\s*[$€£]?([\d,]+\.\d{2})', text, re.I)
    if tax_match:
        result['tax'] = float(tax_match.group(1).replace(',', ''))
    else:
        result['tax'] = None

    return result

def extract_invoice_regex(text: str) -> Dict[str, Any]:
 
    result = {}
 
    inv_match = re.search(r'(?:Invoice|INV)[\s#:]*([A-Za-z0-9\-]+)', text, re.I)
    result['invoice_number'] = inv_match.group(1) if inv_match else None

 
    date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
    result['date'] = date_match.group(1) if date_match else None

 
    total_match = re.search(r'(?:Total|Amount Due):\s*[$€£]?([\d,]+\.\d{2})', text, re.I)
    result['total'] = float(total_match.group(1).replace(',', '')) if total_match else None

 
    vendor_match = re.search(r'(?:Vendor|From|Bill From):\s*(.+)', text, re.I)
    result['vendor'] = vendor_match.group(1).strip() if vendor_match else None

    return result

def extract_id_card_regex(text: str) -> Dict[str, Any]:
    
    result = {}
   
    name_match = re.search(r'(?:Name|Full Name):\s*(.+)', text, re.I)
    result['name'] = name_match.group(1).strip() if name_match else None

     
    dob_match = re.search(r'(?:DOB|Date of Birth|Birth Date):\s*([\d/]+)', text, re.I)
    result['dob'] = dob_match.group(1) if dob_match else None

     
    id_match = re.search(r'(?:ID|Citizenship|Passport|PAN)[\s#:]*([A-Za-z0-9\-]+)', text, re.I)
    result['id_number'] = id_match.group(1) if id_match else None

    
    nat_match = re.search(r'Nationality:\s*(.+)', text, re.I)
    result['nationality'] = nat_match.group(1).strip() if nat_match else None

    return result

 
REGEX_EXTRACTORS = {
    'receipt': extract_receipt_regex,
    'invoice': extract_invoice_regex,
    'id_card': extract_id_card_regex,
 
}
 
def extract_with_ai(text: str, doc_type: str) -> Dict[str, Any]:
     
    schemas = {
        'receipt': {
            'vendor': 'string',
            'date': 'string (YYYY-MM-DD)',
            'total': 'number',
            'tax': 'number',
            'items': 'list of objects with name, quantity, price'
        },
        'invoice': {
            'invoice_number': 'string',
            'date': 'string (YYYY-MM-DD)',
            'vendor': 'string',
            'total': 'number',
            'tax': 'number',
            'due_date': 'string (YYYY-MM-DD)'
        },
        'id_card': {
            'name': 'string',
            'dob': 'string (YYYY-MM-DD)',
            'id_number': 'string',
            'nationality': 'string',
            'address': 'string'
        },
        'bank_statement': {
            'account_number': 'string',
            'period_start': 'string',
            'period_end': 'string',
            'opening_balance': 'number',
            'closing_balance': 'number',
            'transactions': 'list of objects'
        },
        # Add more types
    }

    schema = schemas.get(doc_type, {})
    if not schema:
        # Fallback: try to extract any key-value pairs
        return {}

    # Build prompt
    fields_desc = '\n'.join([f"- {k}: {v}" for k, v in schema.items()])
    prompt = f"""Extract the following fields from the document text below.
Return ONLY valid JSON with the extracted data.

Document type: {doc_type}
Fields to extract:
{fields_desc}

Document text:
{text[:8000]}

JSON:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data extraction assistant. Extract structured data from OCR text and return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        raw = response.choices[0].message.content
        # Clean up: remove markdown code blocks
        raw = re.sub(r'```json\s*', '', raw)
        raw = re.sub(r'```\s*', '', raw)
        return json.loads(raw)
    except Exception as e:
        logger.error(f"AI extraction failed: {e}")
        return {}

 
def extract_structured_data(text: str, doc_type: str, use_ai: bool = True) -> Dict[str, Any]:
    
     
    if use_ai and settings.OPENAI_API_KEY:
        try:
            data = extract_with_ai(text, doc_type)
            if data:
                logger.info(f"AI extraction successful for doc_type={doc_type}")
                return data
        except Exception as e:
            logger.warning(f"AI extraction failed, falling back to regex: {e}")

 
    extractor = REGEX_EXTRACTORS.get(doc_type)
    if extractor:
        return extractor(text)
    return {}