import re
from typing import Dict, List, Tuple



KEYWORDS: Dict[str, List[Tuple[str, int]]] = {
    'receipt': [
        (r'\breceipt\b', 3), (r'\bcashier\b', 3), (r'\bchange due\b', 3),
        (r'\bchange\b', 1), (r'\bqty\b', 2), (r'\bunit price\b', 2),
        (r'\bsubtotal\b', 1), (r'\bgrand total\b', 2), (r'\bvat\b', 1),
        (r'\bthank you for (your|shopping)\b', 3), (r'\bstore #?\d+\b', 2),
        (r'\bterminal\b', 2), (r'\bapproved\b', 1), (r'\bcard ending\b', 3),
        (r'\btotal\b', 1), (r'\bamount due\b', 1), (r'\bdate\b', 1),
    ],
    'invoice': [
        (r'\binvoice\s*(no\.?|number|#)\b', 3), (r'\binvoice\b', 2),
        (r'\bbill to\b', 3), (r'\bship to\b', 3), (r'\bpurchase order\b', 3),
        (r'\bpo\s*(no\.?|number|#)\b', 3), (r'\bpayment terms\b', 2),
        (r'\bdue date\b', 2), (r'\bnet\s*30\b', 3), (r'\bremit to\b', 3),
        (r'\bsubtotal\b', 1), (r'\btax\b', 1), (r'\bdiscount\b', 1),
        (r'\btotal amount due\b', 2), (r'\baccount number\b', 2),
    ],
    'id_card': [
        (r'\bnational identity\b', 3), (r'\bcitizenship\b', 3),
        (r'\bpassport\b', 3), (r'\bdriving licen[sc]e\b', 3),
        (r'\bpan card\b', 3), (r'\bvoter\b', 2),
        (r'\bregistration number\b', 2), (r'\bdate of birth\b', 3),
        (r'\bplace of birth\b', 3), (r'\bblood group\b', 3),
        (r'\bsex\b', 1), (r'\bgender\b', 1), (r'\bnationality\b', 2),
        (r"\bfather'?s? name\b", 2), (r"\bmother'?s? name\b", 2),
        (r"\bspouse'?s? name\b", 2), (r'\bissued by\b', 2),
        (r'\bexpiry date\b', 2), (r'\baddress\b', 1),
    ],
    'contract': [
        (r'\bthis agreement\b', 3), (r'\bcontract\b', 2),
        (r'\bterms and conditions\b', 2), (r'\bthe parties\b', 2),
        (r'\bwhereas\b', 3), (r'\bhereby\b', 3), (r'\bshall\b', 1),
        (r'\bindemnif(y|ication)\b', 3), (r'\bliability\b', 2),
        (r'\bconfidential(ity)?\b', 2), (r'\btermination\b', 2),
        (r'\bgoverning law\b', 3), (r'\barbitration\b', 3),
        (r'\bin witness whereof\b', 3), (r'\beffective date\b', 2),
        (r'\bsignature\b', 1), (r'\bwitness\b', 1),
    ],
    'book': [
        (r'\bchapter\s+\d+\b', 3), (r'\btable of contents\b', 3),
        (r'\ball rights reserved\b', 3), (r'\bcopyright\s*©?\s*\d{4}\b', 2),
        (r'\bisbn\b', 3), (r'\bedition\b', 2), (r'\bpublisher\b', 2),
        (r'\bpreface\b', 3), (r'\bforeword\b', 3), (r'\backnowledg(e)?ments\b', 2),
        (r'\bbibliography\b', 3), (r'\bepilogue\b', 3), (r'\bprologue\b', 3),
        (r'\bpage\b', 1), (r'\bindex\b', 1),
    ],
    'resume': [
        (r'\bcurriculum vitae\b', 3), (r'\bresume\b', 2),
        (r'\bwork experience\b', 3), (r'\bemployment history\b', 3),
        (r'\beducation\b', 1), (r'\bskills\b', 1), (r'\breferences\b', 1),
        (r'\bobjective\b', 1), (r'\bcertifications?\b', 2),
        (r'\blinkedin\.com\b', 2), (r'\bgpa\b', 2), (r'\bportfolio\b', 1),
    ],
    'bank_statement': [
        (r'\baccount statement\b', 3), (r'\bstatement period\b', 3),
        (r'\bopening balance\b', 3), (r'\bclosing balance\b', 3),
        (r'\btransaction (history|date)\b', 2), (r'\bwithdrawal\b', 2),
        (r'\bdeposit\b', 1), (r'\biban\b', 3), (r'\bswift\b', 2),
        (r'\baccount number\b', 1), (r'\bbranch\b', 1), (r'\bbalance\b', 1),
    ],
    'prescription': [
        (r'\bprescription\b', 3), (r'\brx\b', 3), (r'\bdosage\b', 2),
        (r'\bmg\b', 1), (r'\btablet(s)?\b', 2), (r'\bcapsule(s)?\b', 2),
        (r'\btake\s+\d+\s+times\b', 3), (r'\bphysician\b', 2),
        (r'\bpharmacy\b', 2), (r'\brefill\b', 2), (r'\bdiagnosis\b', 2),
        (r'\bsig\b', 2),
    ],
    'business_card': [
        (r'\bceo\b', 2), (r'\bfounder\b', 2), (r'\bmanager\b', 1),
        (r'\bphone\b', 1), (r'\bmobile\b', 1), (r'\bemail\b', 1),
        (r'\bwww\.\S+\b', 2), (r'\b@\w+\.\w+\b', 1),
    ],
}

DEFAULT_TYPE = 'document'
MIN_TEXT_LENGTH = 20
MIN_SCORE_THRESHOLD = 3.0
CLOSE_CALL_MARGIN = 1.5  

 
_COMPILED: Dict[str, List[Tuple[re.Pattern, int]]] = {
    doc_type: [(re.compile(p, re.IGNORECASE), w) for p, w in patterns]
    for doc_type, patterns in KEYWORDS.items()
}

 
FUZZY_TERMS: Dict[str, List[Tuple[str, int]]] = {
    'receipt': [('receipt', 3), ('cashier', 3), ('subtotal', 1)],
    'invoice': [('invoice', 2), ('subtotal', 1)],
    'id_card': [('citizenship', 3), ('passport', 3), ('nationality', 2)],
    'contract': [('whereas', 3), ('hereby', 3), ('indemnification', 3),
                 ('arbitration', 3), ('confidentiality', 2)],
    'book': [('isbn', 3), ('bibliography', 3), ('preface', 3),
             ('foreword', 3), ('epilogue', 3), ('prologue', 3), ('publisher', 2)],
    'resume': [('resume', 2), ('curriculum', 3), ('references', 1), ('certifications', 2)],
    'bank_statement': [('statement', 1), ('withdrawal', 2), ('iban', 3),
                        ('swift', 2), ('balance', 1)],
    'prescription': [('prescription', 3), ('dosage', 2), ('pharmacy', 2),
                      ('physician', 2), ('tablet', 2), ('capsule', 2), ('refill', 2)],
    'business_card': [('founder', 2), ('mobile', 1)],
}

FUZZY_WEIGHT_DISCOUNT = 0.6   

 
_TOKEN_RE = re.compile(r'[a-zA-Z0-9]+')
_OCR_DIGIT_MAP = str.maketrans({'0': 'o', '1': 'l', '5': 's', '3': 'e', '8': 'b'})


def _max_edit_distance(word_len: int) -> int:
   
    if word_len <= 5:
        return 1
    if word_len <= 9:
        return 2
    return 3


def _levenshtein(a: str, b: str, max_dist: int) -> int:
    
    if abs(len(a) - len(b)) > max_dist:
        return max_dist + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * len(b)
        row_min = curr[0]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
            row_min = min(row_min, curr[j])
        if row_min > max_dist:
            return max_dist + 1
        prev = curr
    return prev[-1]


def _fuzzy_score(text: str) -> Dict[str, float]:
    
    raw_tokens = set(t.lower() for t in _TOKEN_RE.findall(text))
    
    normalized_tokens = {
        t.translate(_OCR_DIGIT_MAP) for t in raw_tokens if not t.isdigit()
    }
    candidate_tokens = raw_tokens | normalized_tokens

    scores: Dict[str, float] = {doc_type: 0.0 for doc_type in FUZZY_TERMS}
    for doc_type, terms in FUZZY_TERMS.items():
        for term, weight in terms:
            if term in candidate_tokens:
                
                if term in raw_tokens:
                    continue
                scores[doc_type] += weight * FUZZY_WEIGHT_DISCOUNT
                continue
            max_dist = _max_edit_distance(len(term))
            best_hit = False
            for token in candidate_tokens:
                if abs(len(token) - len(term)) > max_dist:
                    continue
                if _levenshtein(token, term, max_dist) <= max_dist:
                    best_hit = True
                    break   
            if best_hit:
                scores[doc_type] += weight * FUZZY_WEIGHT_DISCOUNT
    return scores


def _score_text(text: str) -> Dict[str, float]:
     
    length_factor = max(len(text) / 500.0, 1.0)   
    exact_scores: Dict[str, float] = {}
    for doc_type, patterns in _COMPILED.items():
        raw = sum(w * len(p.findall(text)) for p, w in patterns)
        exact_scores[doc_type] = raw / length_factor

    fuzzy_scores = _fuzzy_score(text)
    for doc_type, fscore in fuzzy_scores.items():
        exact_scores[doc_type] = exact_scores.get(doc_type, 0.0) + fscore / length_factor

    return exact_scores


def _disambiguate_receipt_invoice(text: str, scores: Dict[str, float]) -> str:
    
    receipt_signals = len(re.findall(r'(?i)\bcashier\b|\bchange due\b|\bstore #?\d+\b', text))
    invoice_signals = len(re.findall(r'(?i)\bbill to\b|\bship to\b|\binvoice\s*(no\.?|number|#)\b|\bpurchase order\b', text))
    if invoice_signals > receipt_signals:
        return 'invoice'
    if receipt_signals > invoice_signals:
        return 'receipt'
     
    return 'invoice' if scores['invoice'] >= scores['receipt'] else 'receipt'


def classify_document(text: str) -> str:
     
    if not text or len(text.strip()) < MIN_TEXT_LENGTH:
        return DEFAULT_TYPE

    scores = _score_text(text)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    best_type, best_score = ranked[0]
    second_type, second_score = ranked[1] if len(ranked) > 1 else (None, 0.0)

    if best_score < MIN_SCORE_THRESHOLD:
        return DEFAULT_TYPE

     
    if {best_type, second_type} == {'receipt', 'invoice'} and \
       abs(best_score - second_score) < CLOSE_CALL_MARGIN:
        return _disambiguate_receipt_invoice(text, scores)

    return best_type


if __name__ == '__main__':
    samples = {
        'receipt': "STORE #4521\nCashier: Maria\n2x Milk  $3.50\nSubtotal $3.50\nVAT $0.35\nTotal $3.85\nChange due $0.15\nThank you for shopping!",
        'invoice': "INVOICE NO: INV-2024-0091\nBill To: Acme Corp\nShip To: 123 Main St\nPayment Terms: Net 30\nDue Date: 2024-09-01\nSubtotal: $1,200.00\nTax: $96.00\nTotal Amount Due: $1,296.00",
        'contract': "THIS AGREEMENT is entered into by and between the Parties. WHEREAS the parties wish to collaborate, the Parties hereby agree as follows... Governing Law: State of Delaware. In witness whereof the parties have signed below.",
        'resume': "John Doe\nCurriculum Vitae\nWork Experience: Software Engineer at TechCo (2020-2023)\nEducation: BSc Computer Science\nSkills: Python, Flutter\nReferences available on request.",
        'id_card': "NATIONAL IDENTITY CARD\nDate of Birth: 1998-04-12\nSex: M\nNationality: Nepali\nFather's Name: Ram Bahadur\nExpiry Date: 2030-04-12",
        'gibberish': "asdkj alksdj laksjd laksjdlk ajsdlkaj sldkj",
        
        'ocr_receipt': "5T0RE #4521\nCash1er: Maria\n2x Milk  $3.50\nSubt0tal $3.50\nVAT $0.35\nT0tal $3.85\nChan9e due $0.15",
        'ocr_contract': "THIS AGREEMENT is entered into by the Partles. Wherea5 the parties wish to collaborate, the parties hereby agree. Arb1tration shall apply. C0nfidentiality is required.",
        'ocr_id_card': "NATI0NAL IDENTITY CARD\nCitizen5hip Certificate\nNationa1ity: Nepali\nPa55port No: 04521",
    }
    for label, sample in samples.items():
        print(f"{label:14s} -> {classify_document(sample)}")