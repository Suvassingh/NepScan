from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0   
def detect_language(text: str) -> str:
    if not text.strip():
        return 'unknown'
    try:
        lang = detect(text)
        if lang in ['ne', 'en']:
            return lang
        else:
            return 'mixed'  
    except:
        return 'unknown'