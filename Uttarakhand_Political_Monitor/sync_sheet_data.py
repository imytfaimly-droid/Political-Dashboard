import subprocess
import csv
import json
import os
import re
import sys
from datetime import datetime, timedelta

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SPREADSHEET_ID = "1GNGN-2dFiDcg59Vxm3Oa9gkzGujW4QiqTbMtyEF6itQ"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if sys.platform == "win32" and os.path.exists(r"D:\Google-Dowanlod"):
    TEMP_DIR = r"D:\Google-Dowanlod\temp_sync"
    OUT_DIR = os.path.join(r"D:\Google-Dowanlod", "Uttarakhand_Political_Monitor")
    RAW_DIR = r"D:\Google-Dowanlod"
else:
    TEMP_DIR = os.path.join(SCRIPT_DIR, "temp_sync")
    OUT_DIR = SCRIPT_DIR
    RAW_DIR = SCRIPT_DIR

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

DATA_JSON_PATH = os.path.join(OUT_DIR, "dashboard_data.json")
DATA_JS_PATH = os.path.join(OUT_DIR, "dashboard_data.js")

# ----------------- NORMALIZATION MAPS -----------------
DISTRICT_MAP = {
    # Uttarakhand
    "dehradun": "देहरादून", "देहरादून": "देहरादून", "rishikesh": "देहरादून", "ऋषिकेश": "देहरादून", "vikasnagar": "देहरादून", "विकासनगर": "देहरादून",
    "haridwar": "हरिद्वार", "हरिद्वार": "हरिद्वार", "roorkee": "हरिद्वार", "रुड़की": "हरिद्वार",
    "nainital": "नैनीताल", "नैनीताल": "नैनीताल", "haldwani": "नैनीताल", "हल्द्वानी": "नैनीताल", "ramnagar": "नैनीताल", "रामनगर": "नैनीताल",
    "udham singh nagar": "ऊधम सिंह नगर", "udham-singh-nagar": "ऊधम सिंह नगर", "ऊधम सिंह नगर": "ऊधम सिंह नगर", "rudrapur": "ऊधम सिंह नगर", "रुद्रपुर": "ऊधम सिंह नगर", "kashipur": "ऊधम सिंह नगर", "काशीपुर": "ऊधम सिंह नगर",
    "pauri": "पौड़ी", "pauri garhwal": "पौड़ी", "पौड़ी": "पौड़ी", "kotdwar": "पौड़ी", "कोटद्वार": "पौड़ी", "श्रीनगर": "पौड़ी", "srinagar": "पौड़ी",
    "tehri": "टिहरी", "tehri garhwal": "टिहरी", "टिहरी": "टिहरी", "नई टिहरी": "टिहरी",
    "chamoli": "चमोली", "चमोली": "चमोली", "gopeshwar": "चमोली", "जोशीमठ": "चमोली", "joshimath": "चमोली", "गैरसैंण": "चमोली", "gairsain": "चमोली", "भराड़ीसैंण": "चमोली",
    "rudraprayag": "रुद्रप्रयाग", "रुद्रप्रयाग": "रुद्रप्रयाग", "kedarnath": "रुद्रप्रयाग", "केदारनाथ": "रुद्रप्रयाग",
    "uttarkashi": "उत्तरकाशी", "उत्तरकाशी": "उत्तरकाशी",
    "almora": "अल्मोड़ा", "अल्मोड़ा": "अल्मोड़ा", "ranikhet": "अल्मोड़ा", "रानीखेत": "अल्मोड़ा",
    "pithoragarh": "पिथौरागढ़", "पिथौरागढ़": "पिथौरागढ़", "dharchula": "पिथौरागढ़", "धारचूला": "पिथौरागढ़",
    "bageshwar": "बागेश्वर", "बागेश्वर": "बागेश्वर",
    "champawat": "चंपावत", "चंपावत": "चंपावत",
    
    # Himachal Pradesh
    "shimla": "शिमला", "शिमला": "शिमला", "rohru": "शिमला", "रोहड़ू": "शिमला", "rampur": "शिमला", "रामपुर": "शिमला", "rampur-bushahar": "शिमला", "sanjauli": "शिमला", "संजौली": "शिमला",
    "kangra": "कांगड़ा", "कांगड़ा": "कांगड़ा", "dharamshala": "कांगड़ा", "धर्मशाला": "कांगड़ा", "palampur": "कांगड़ा", "पालमपुर": "कांगड़ा",
    "mandi": "मंडी", "मंडी": "मंडी",
    "kullu": "कुल्लू", "कुल्लू": "कुल्लू", "manali": "कुल्लू", "मनाली": "कुल्लू",
    "solan": "सोलन", "सोलन": "सोलन", "baddi": "सोलन",
    "sirmaur": "सिरमौर", "सिरमौर": "सिरमौर", "nahan": "सिरमौर", "नाहन": "सिरमौर", "paonta": "सिरमौर",
    "bilaspur": "बिलासपुर", "बिलासपुर": "बिलासपुर",
    "una": "ऊना", "ऊना": "ऊना",
    "hamirpur": "हमीरपुर", "हमीरपुर": "हमीरपुर",
    "chamba": "चंबा", "चंबा": "चंबा",
    "kinnaur": "किन्नौर", "किन्नौर": "किन्नौर",
    "lahaul": "लाहौल-स्पीति", "spiti": "लाहौल-स्पीति", "लाहौल": "लाहौल-स्पीति"
}

DROP_OUT_OF_STATE = [
    "uttar-pradesh", "uttar pradesh", "haryana", "punjab", "delhi", "lucknow", "meerut", "bareilly",
    "chandigarh", "bollywood", "sports", "business", "cricket", "शेयर बाजार", "सोना-चांदी", "horoscope", "राशिफल"
]

TOPIC_PATTERNS = [
    ("अंकिता केस/VIP", r"अंकिता|ankita|वीआईपी|vip|वनंतरा|पुलकित"),
    ("जेनी–हरक प्रकरण", r"जेनी|jenny|हरक सिंह|harak singh"),
    ("भ्रष्टाचार व हस्ताक्षर अभियान", r"भ्रष्टाचार|हस्ताक्षर|घोटाला|कमीशन|scam|corruption"),
    ("रेखा आर्या/210 करोड़", r"रेखा आर्या|rekha arya|210 करोड़"),
    ("महंगाई", r"महंगाई|सिलेंडर|पेट्रोल|डीजल|टैक्स|मूल्य वृद्धि"),
    ("महिला सुरक्षा व अपराध", r"महिला सुरक्षा|दुष्कर्म|छेड़छाड़|अपराध|हत्या|महिला अस्मिता"),
    ("विकास योजनाएं व घोषणाएं", r"विकास|लोकार्पण|शिलान्यास|घोषणा|सड़क निर्माण|पुल|योजना|सौगात"),
    ("रोज़गार, भर्ती व युवा", r"रोजगार|रोज़गार|भर्ती|युवा|बेरोजगार|पेपर लीक|ukpsc|uksssc|नियुक्ति"),
    ("प्रवासी, पलायन व गांव", r"पलायन|प्रवासी|रैबार|गांव|पहाड़ वापसी|मूल निवास|भू-कानून|भू कानून"),
    ("संगठन, चुनाव व जनसंपर्क", r"चुनाव|संगठन|कार्यकर्ता|रैली|जनसभा|बूथ|प्रचार|अध्यक्ष|बैठक"),
    ("किसान, खाद व पशुपालन", r"किसान|खाद|पशुपालन|फसल|एमएसपी|कृषि|मंडी"),
    ("आशा, आंगनबाड़ी व कर्मचारी", r"आंगनबाड़ी|आंगनबाड़ी|आशा कार्यकत्री|कर्मचारी|ओपीएस|ops|वेतन|मानदेय"),
    ("स्वास्थ्य व शिक्षा", r"अस्पताल|डॉक्टर|दवा|स्वास्थ्य|स्कूल|कॉलेज|शिक्षा|यूनिवर्सिटी"),
    ("बदहाल व्यवस्था/सड़क/कचरा", r"सड़क बदहाल|गड्ढा|जाम|कचरा|सीवर|पेयजल संकट|बिजली कटौती"),
    ("धर्म, संस्कृति व धाम", r"केदारनाथ|बद्रीनाथ|चारधाम|मंदिर|संस्कृति|कुंभ|धार्मिक|मस्जिद|संजौली"),
    ("राष्ट्रीय: मोदी–राहुल, SIR, संसद", r"मोदी|राहुल गांधी|संसद|sir|अमित शाह|खरगे|सुप्रीम कोर्ट"),
    ("पड़ोसी राज्य पर तंज", r"उत्तर प्रदेश|पंजाब|दिल्ली सरकार|आप सरकार|पड़ोसी"),
    ("शुभकामना/श्रद्धांजलि", r"शुभकामना|हार्दिक बधाई|श्रद्धांजलि|पुण्यतिथि|जयंती|नमन")
]

LEADER_FIXED_NAMES = {
    "@pushkardhami": "पुष्कर सिंह धामी",
    "@mahendrabhatbjp": "महेंद्र भट्ट",
    "@anil_baluni": "अनिल बलूनी",
    "@tsrawatbjp": "त्रिवेंद्र सिंह रावत",
    "@satpalmaharaj": "सतपाल महाराज",
    "@deeptirawatbjp": "दीप्ति रावत भारद्वाज",
    "@SubodhUniyal1": "सुबोध उनियाल",
    "@drdhansinghbjp": "डॉ. धन सिंह रावत",
    "@ganeshjoshibjp": "गणेश जोशी",
    "@rekhaaryaoffice": "रेखा आर्या",
    "@INCUttarakhand": "उत्तराखंड कांग्रेस",
    "@UKGaneshGodiyal": "गणेश गोदियाल",
    "@harishrawatcmuk": "हरीश रावत",
    "@IamYashpalArya": "यशपाल आर्य",
    "@incpritamsingh": "प्रीतम सिंह",
    "@UKD4Uttarakhand": "यूकेडी (उत्तराखंड क्रांति दल)",
    "@AAPUttarakhand": "आम आदमी पार्टी (उत्तराखंड)",
    "@PanwarBobby": "बॉबी पंवार",
    "@bobbypanwar4uk": "बॉबी पंवार",
    "@AjitSinghRathi": "अजीत सिंह राठी",
    "@Rameshbhimtal": "रमेश चंद्र जोशी",
    "@Anoopnautiyal1": "अनूप नौटियाल",
    "@askbhupi": "भूपी पंवार",
    "@SukhuSukhvinder": "सुखविंदर सिंह सुक्खू",
    "@jairamthakurbjp": "जयराम ठाकुर",
    "@ianuragthakur": "अनुराग ठाकुर"
}

ENTITIES = [
    {"state": "Uttarakhand", "type": "leader", "name": "पुष्कर सिंह धामी", "party": "भाजपा", "role": "मुख्यमंत्री, उत्तराखंड", "keywords": r"धामी|पुष्कर सिंह धामी", "about": "उत्तराखंड के मुख्यमंत्री, कड़े नकल विरोधी कानून व यूसीसी के अगुआ।"},
    {"state": "Uttarakhand", "type": "leader", "name": "महेंद्र भट्ट", "party": "भाजपा", "role": "प्रदेश अध्यक्ष व राज्यसभा सांसद", "keywords": r"महेंद्र भट्ट", "about": "भाजपा प्रदेश संगठन प्रमुख व राज्यसभा सांसद।"},
    {"state": "Uttarakhand", "type": "leader", "name": "अनिल बलूनी", "party": "भाजपा", "role": "लोकसभा सांसद, गढ़वाल", "keywords": r"अनिल बलूनी", "about": "गढ़वाल सांसद व पूर्व राष्ट्रीय मीडिया प्रभारी।"},
    {"state": "Uttarakhand", "type": "leader", "name": "सुबोध उनियाल", "party": "भाजपा", "role": "कैबिनेट मंत्री (वन एवं तकनीकी शिक्षा)", "keywords": r"सुबोध उनियाल", "about": "उत्तराखंड सरकार में वरिष्ठ कैबिनेट मंत्री।"},
    {"state": "Uttarakhand", "type": "leader", "name": "हरीश रावत", "party": "कांग्रेस", "role": "पूर्व मुख्यमंत्री", "keywords": r"हरीश रावत|हरदा", "about": "वरिष्ठ कांग्रेस नेता एवं पूर्व मुख्यमंत्री।"},
    {"state": "Uttarakhand", "type": "leader", "name": "गणेश गोदियाल", "party": "कांग्रेस", "role": "वरिष्ठ नेता / पूर्व प्रदेश अध्यक्ष", "keywords": r"गणेश गोदियाल|गोदियाल", "about": "पूर्व प्रदेश अध्यक्ष व आक्रामक विपक्षी चेहरा।"},
    {"state": "Uttarakhand", "type": "leader", "name": "यशपाल आर्य", "party": "कांग्रेस", "role": "नेता प्रतिपक्ष विधानसभा", "keywords": r"यशपाल आर्य", "about": "नेता प्रतिपक्ष व वरिष्ठ दलित नेता।"},
    {"state": "Uttarakhand", "type": "leader", "name": "प्रीतम सिंह", "party": "कांग्रेस", "role": "विधायक चकराता", "keywords": r"प्रीतम सिंह(?! पंवार)", "about": "चकराता से वरिष्ठ कांग्रेस विधायक।"},
    {"state": "Uttarakhand", "type": "leader", "name": "बॉबी पंवार", "party": "अन्य", "role": "अध्यक्ष, राज्य स्वराज पार्टी / युवा नेता", "keywords": r"बॉबी पंवार", "about": "युवा व बेरोजगार आंदोलन के प्रमुख चेहरा, टिहरी से लोकसभा प्रत्याशी।"},
    {"state": "Himachal Pradesh", "type": "leader", "name": "सुखविंदर सिंह सुक्खू", "party": "कांग्रेस", "role": "मुख्यमंत्री, हिमाचल प्रदेश", "keywords": r"सुक्खू|सुखविंदर", "about": "हिमाचल प्रदेश के मुख्यमंत्री, ओपीएस के समर्थक।"},
    {"state": "Himachal Pradesh", "type": "leader", "name": "जयराम ठाकुर", "party": "भाजपा", "role": "नेता प्रतिपक्ष / पूर्व मुख्यमंत्री", "keywords": r"जयराम ठाकुर", "about": "नेता प्रतिपक्ष, हिमाचल प्रदेश।"},
    {"state": "Himachal Pradesh", "type": "leader", "name": "अनुराग ठाकुर", "party": "भाजपा", "role": "सांसद हमीरपुर / पूर्व केंद्रीय मंत्री", "keywords": r"अनुराग ठाकुर", "about": "हमीरपुर सांसद व वरिष्ठ राष्ट्रीय भाजपा नेता।"}
]

def normalize_district(raw_text):
    if not raw_text:
        return "राज्य स्तर"
    t = raw_text.lower().strip()
    for k, v in DISTRICT_MAP.items():
        if k in t:
            return v
    return "राज्य स्तर"

def get_topics(text):
    if not text:
        return ["अन्य"]
    matched = []
    for topic, pat in TOPIC_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            matched.append(topic)
    return matched if matched else ["अन्य"]

MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    'जन': 1, 'फर': 2, 'मार्च': 3, 'अप्रै': 4, 'मई': 5, 'जून': 6,
    'जुला': 7, 'अग': 8, 'सितं': 9, 'अक्तू': 10, 'नवं': 11, 'दिसं': 12
}

def clean_date_str(d_str):
    if not d_str:
        return ""
    d_str = str(d_str).strip()
    
    # 1. Match word format: "14-Sep-2026", "14 Sep 2026", "14-September-2026"
    m_word = re.search(r'(\d{1,2})[-/\s]+([A-Za-z\u0900-\u097f]+)[-/\s]+(\d{2,4})', d_str)
    if m_word:
        dy = int(m_word.group(1))
        mo_str = m_word.group(2).lower()[:3]
        mo = MONTH_MAP.get(mo_str, 1)
        yr = int(m_word.group(3))
        if yr < 100:
            yr += 2000
        if yr == 2025 and mo < 9:
            yr = 2026
        return f"{yr:04d}-{mo:02d}-{dy:02d}"

    # 2. Match numeric ISO: "YYYY-MM-DD" or "YYYY/MM/DD"
    m_iso = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', d_str)
    if m_iso:
        yr = int(m_iso.group(1))
        mo = int(m_iso.group(2))
        dy = int(m_iso.group(3))
        if yr == 2025 and mo < 9:
            yr = 2026
        return f"{yr:04d}-{mo:02d}-{dy:02d}"

    # 3. Match numeric DMY: "DD-MM-YYYY" or "DD/MM/YYYY"
    m_dmy = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', d_str)
    if m_dmy:
        dy = int(m_dmy.group(1))
        mo = int(m_dmy.group(2))
        yr = int(m_dmy.group(3))
        if yr == 2025 and mo < 9:
            yr = 2026
        return f"{yr:04d}-{mo:02d}-{dy:02d}"

    return ""

def clean_time_str(t_str):
    if not t_str:
        return "12:00 PM"
    t_str = str(t_str).strip()
    m = re.search(r'(\d{1,2}):(\d{2})(?::\d{2})?\s*(AM|PM)?', t_str, re.IGNORECASE)
    if m:
        hr = int(m.group(1))
        mn = m.group(2)
        ampm = m.group(3)
        if ampm:
            h12 = hr if (1 <= hr <= 12) else (hr - 12 if hr > 12 else 12)
            return f"{h12}:{mn} {ampm.upper()}"
        else:
            p = "AM" if hr < 12 else "PM"
            h12 = hr if (1 <= hr <= 12) else (hr - 12 if hr > 12 else 12)
            return f"{h12}:{mn} {p}"
    return "12:00 PM"

# ----------------- PARSE 1: X-UK TAB -----------------
def load_x_uk():
    path = os.path.join(TEMP_DIR, "x_uk.csv")
    if not os.path.exists(path):
        return []
    items = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row_idx, r in enumerate(reader, start=2):
            if len(r) < 10:
                continue
            party_raw = r[1].strip() if len(r) > 1 else ""
            party = "भाजपा" if "BJP" in party_raw else "कांग्रेस" if ("Congress" in party_raw or "INC" in party_raw) else "आप" if "AAP" in party_raw else "यूकेडी" if "UKD" in party_raw else "राज्य स्वराज पार्टी" if "Rajya Swaraj" in party_raw else "अन्य"
            
            name = r[2].strip() if len(r) > 2 else ""
            handle = r[3].strip() if len(r) > 3 else ""
            clean_handle = re.sub(r"^Facebook:\s*", "", handle, flags=re.IGNORECASE).strip()
            hindi_name = LEADER_FIXED_NAMES.get(clean_handle, name or clean_handle)
            role = r[4].strip() if len(r) > 4 else ""
            post_type = r[5].strip() if len(r) > 5 else "Original Post"
            date = clean_date_str(r[6] if len(r) > 6 else "")
            time_val = clean_time_str(r[7] if len(r) > 7 else "")
            text = r[8].strip() if len(r) > 8 else ""
            url = r[9].strip() if len(r) > 9 else ""
            views = int(re.sub(r"[^\d]", "", r[10])) if len(r) > 10 and re.sub(r"[^\d]", "", r[10]) else 0
            likes = int(re.sub(r"[^\d]", "", r[11])) if len(r) > 11 and re.sub(r"[^\d]", "", r[11]) else 0
            reposts = int(re.sub(r"[^\d]", "", r[12])) if len(r) > 12 and re.sub(r"[^\d]", "", r[12]) else 0
            replies = int(re.sub(r"[^\d]", "", r[13])) if len(r) > 13 and re.sub(r"[^\d]", "", r[13]) else 0
            quotes = int(re.sub(r"[^\d]", "", r[14])) if len(r) > 14 and re.sub(r"[^\d]", "", r[14]) else 0
            
            if not text and not url:
                continue
                
            is_rt = bool(re.search(r"^\s*RT\s*@", text, re.IGNORECASE))
            topics = get_topics(text)
            
            items.append({
                "id": f"xuk_{row_idx}",
                "party": party,
                "leader": hindi_name,
                "handle": clean_handle,
                "role": role,
                "post_type": post_type,
                "date": date,
                "time": time_val,
                "text": text,
                "url": url,
                "views": views,
                "likes": likes,
                "reposts": reposts,
                "replies": replies,
                "quotes": quotes,
                "topics": topics,
                "is_rt": is_rt,
                "state": "Uttarakhand",
                "src": "sheet"
            })
    return items

# ----------------- PARSE 2: JOURNALISTS X -----------------
def load_journalists_x():
    path = os.path.join(TEMP_DIR, "journalists_x.csv")
    if not os.path.exists(path):
        return []
    items = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row_idx, r in enumerate(reader, start=2):
            if len(r) < 8:
                continue
            name = r[1].strip() if len(r) > 1 else ""
            handle = r[2].strip() if len(r) > 2 else ""
            post_type = r[3].strip() if len(r) > 3 else ""
            date = clean_date_str(r[4] if len(r) > 4 else "")
            time_val = clean_time_str(r[5] if len(r) > 5 else "")
            text = r[6].strip() if len(r) > 6 else ""
            url = r[7].strip() if len(r) > 7 else ""
            views = int(re.sub(r"[^\d]", "", r[8])) if len(r) > 8 and re.sub(r"[^\d]", "", r[8]) else 0
            likes = int(re.sub(r"[^\d]", "", r[9])) if len(r) > 9 and re.sub(r"[^\d]", "", r[9]) else 0
            reposts = int(re.sub(r"[^\d]", "", r[10])) if len(r) > 10 and re.sub(r"[^\d]", "", r[10]) else 0
            replies = int(re.sub(r"[^\d]", "", r[11])) if len(r) > 11 and re.sub(r"[^\d]", "", r[11]) else 0
            
            if not text and not url:
                continue
                
            topics = get_topics(text)
            items.append({
                "id": f"jx_{row_idx}",
                "journalist": LEADER_FIXED_NAMES.get(handle, name or handle),
                "handle": handle,
                "post_type": post_type,
                "date": date,
                "time": time_val,
                "text": text,
                "url": url,
                "views": views,
                "likes": likes,
                "reposts": reposts,
                "replies": replies,
                "topics": topics,
                "state": "Uttarakhand",
                "medium": "X"
            })
    return items

# ----------------- PARSE 3: ETV NEWS -----------------
def load_etv_news():
    path = os.path.join(TEMP_DIR, "etv_news.csv")
    if not os.path.exists(path):
        return []
    items = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row_idx, r in enumerate(reader, start=2):
            if len(r) < 8:
                continue
            raw_state = r[1].strip() if len(r) > 1 else ""
            state = "Himachal Pradesh" if "हिमाचल" in raw_state or "Himachal" in raw_state else "Uttarakhand"
            
            dt_raw = r[2].strip() if len(r) > 2 else ""
            date = clean_date_str(dt_raw)
            time_val = clean_time_str(dt_raw)
            
            headline = r[3].strip() if len(r) > 3 else ""
            category = r[4].strip() if len(r) > 4 else "राजनीति"
            is_political = "हाँ" in (r[5] if len(r) > 5 else "") or "yes" in (r[5] if len(r) > 5 else "").lower() or "राजनीति" in category
            
            full_text = r[6].strip() if len(r) > 6 else ""
            url = r[7].strip() if len(r) > 7 else ""
            summary = r[8].strip() if len(r) > 8 else ""
            reporter = r[9].strip() if len(r) > 9 else ""
            
            if not headline:
                continue
                
            if any(k in headline.lower() or k in url.lower() for k in DROP_OUT_OF_STATE) and "uttarakhand" not in url.lower() and "himachal" not in url.lower():
                continue
                
            if "etv" in reporter.lower():
                portal = "ETV Bharat"
                medium = "टीवी"
            else:
                portal = reporter if reporter else "ETV Web"
                medium = "वेब"
                
            district = "राज्य स्तर"
            slug_match = re.search(r"/(uttarakhand|himachal-pradesh)/([a-z0-9\-]+)", url.lower())
            if slug_match:
                slug_dist = slug_match.group(2).split("-")[0]
                district = normalize_district(slug_dist)
            if district == "राज्य स्तर":
                district = normalize_district(headline)
                
            topics = get_topics(headline + " " + summary)
            
            items.append({
                "id": f"e{row_idx}",
                "state": state,
                "date": date,
                "time": time_val,
                "headline": headline,
                "category": category,
                "is_political": is_political,
                "full_text": full_text,
                "summary": summary if summary else (full_text[:240] + "..." if len(full_text) > 240 else full_text),
                "portal": portal,
                "medium": medium,
                "district": district,
                "url": url,
                "topics": topics
            })
    return items

# ----------------- PARSE 4: DB & AU NEWS -----------------
def load_db_au_news():
    path = os.path.join(TEMP_DIR, "db_au_news.csv")
    if not os.path.exists(path):
        return []
    items = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row_idx, r in enumerate(reader, start=2):
            if len(r) < 7:
                continue
            dt_raw = r[1].strip() if len(r) > 1 else ""
            date = clean_date_str(dt_raw)
            time_val = clean_time_str(dt_raw)
            
            portal = r[2].strip() if len(r) > 2 else "Amar Ujala"
            state_raw = r[3].strip() if len(r) > 3 else ""
            state = "Himachal Pradesh" if "himachal" in state_raw.lower() or "हिमाचल" in state_raw else "Uttarakhand"
            
            district = normalize_district(r[4] if len(r) > 4 else "")
            headline = r[5].strip() if len(r) > 5 else ""
            full_text = r[6].strip() if len(r) > 6 else ""
            category = r[7].strip() if len(r) > 7 else "राजनीतिक"
            url = r[8].strip() if len(r) > 8 else ""
            
            if not headline:
                continue
                
            if any(k in headline.lower() or k in url.lower() for k in DROP_OUT_OF_STATE) and "uttarakhand" not in url.lower() and "himachal" not in url.lower():
                continue
                
            is_political = "राजनीतिक" in category or "प्रशासनिक" in category or "विपक्ष" in category or "सरकार" in category
            topics = get_topics(headline + " " + full_text[:400])
            
            sentences = [s.strip() for s in re.split(r"[।\.\n]", full_text) if len(s.strip()) > 15]
            summary = "। ".join(sentences[:2]) + ("।" if sentences else "")
            if not summary:
                summary = headline
                
            items.append({
                "id": f"w{row_idx}",
                "state": state,
                "date": date,
                "time": time_val,
                "headline": headline,
                "category": category,
                "is_political": is_political,
                "full_text": full_text,
                "summary": summary,
                "portal": portal,
                "medium": "वेब",
                "district": district,
                "url": url,
                "topics": topics
            })
    return items

# ----------------- PARSE 5: PRINT REPORTS -----------------
def load_print_reports(filename, state_name):
    path = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(path):
        return []
    items = []
    last_date = "2026-11-14"
    last_paper = "Dainik Jagran"
    
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row_idx, r in enumerate(reader, start=2):
            if len(r) < 4:
                continue
            date_raw = r[0].strip() if len(r) > 0 else ""
            if date_raw:
                last_date = clean_date_str(date_raw)
            date = last_date
            
            paper_raw = r[1].strip() if len(r) > 1 else ""
            if paper_raw:
                last_paper = paper_raw
            paper = last_paper
            
            headline = r[2].strip() if len(r) > 2 else ""
            summary = r[3].strip() if len(r) > 3 else ""
            category = r[4].strip() if len(r) > 4 else "State Politics"
            sentiment_raw = r[5].strip() if len(r) > 5 else ""
            link = r[6].strip() if len(r) > 6 else ""
            
            if not headline or len(headline) < 5:
                continue
                
            stance = "तटस्थ"
            sent_lower = sentiment_raw.lower()
            if state_name == "Uttarakhand":
                if "pro-bjp" in sent_lower or "pro bjp" in sent_lower:
                    stance = "सरकार-समर्थक"
                elif "anti-bjp" in sent_lower or "anti bjp" in sent_lower:
                    stance = "सरकार-विरोधी"
                elif "pro-congress" in sent_lower or "pro inc" in sent_lower or "pro congress" in sent_lower:
                    stance = "विपक्ष-समर्थक"
                elif "anti-congress" in sent_lower or "anti inc" in sent_lower or "anti congress" in sent_lower:
                    stance = "विपक्ष-विरोधी"
            else: # Himachal Pradesh
                if "pro-congress" in sent_lower or "pro inc" in sent_lower or "pro congress" in sent_lower:
                    stance = "सरकार-समर्थक"
                elif "anti-congress" in sent_lower or "anti inc" in sent_lower or "anti congress" in sent_lower:
                    stance = "सरकार-विरोधी"
                elif "pro-bjp" in sent_lower or "pro bjp" in sent_lower:
                    stance = "विपक्ष-समर्थक"
                elif "anti-bjp" in sent_lower or "anti bjp" in sent_lower:
                    stance = "विपक्ष-विरोधी"
                    
            items.append({
                "id": f"p_{state_name[:2].lower()}_{row_idx}",
                "state": state_name,
                "date": date,
                "paper": paper,
                "category": category,
                "stance": stance,
                "sentiment_raw": sentiment_raw,
                "headline": headline,
                "summary": summary,
                "link": link
            })
    return items

# ----------------- PARSE 6: INSIGHTS & RALLIES -----------------
INSIGHTS = [
    {
        "state": "Uttarakhand",
        "kind": "मुख्य",
        "entity": "पुष्कर सिंह धामी",
        "date": "2026-11-14",
        "tone": "सकारात्मक",
        "point": "मुख्यमंत्री पुष्कर सिंह धामी ने देहरादून में ट्रेड फेयर और जौनपुर महोत्सव में 52 करोड़ की 26 योजनाओं की घोषणा की तथा 1 दिसंबर से मानदेय वृद्धि लागू करने का आदेश दिया।"
    },
    {
        "state": "Uttarakhand",
        "kind": "मुख्य",
        "entity": "अंकिता केस/VIP",
        "date": "2026-11-14",
        "tone": "गंभीर",
        "point": "अंकिता भंडारी मामले में विपक्ष द्वारा उठाए जा रहे वीआईपी के नाम पर मुख्यमंत्री ने स्पष्ट किया कि 24 घंटे में आरोपी पकड़े गए और मामले को राजनीति की सीढ़ी न बनाया जाए।"
    },
    {
        "state": "Uttarakhand",
        "kind": "X",
        "entity": "भाजपा",
        "date": "2026-11-14",
        "tone": "सकारात्मक",
        "point": "भाजपा नेताओं ने राज्य स्थापना दिवस की घोषणाओं और प्रवासी उत्तराखंडी सम्मेलन को लेकर सोशल मीडिया पर व्यापक पोस्ट किए।"
    },
    {
        "state": "Uttarakhand",
        "kind": "X",
        "entity": "कांग्रेस",
        "date": "2026-11-14",
        "tone": "आक्रामक",
        "point": "कांग्रेस प्रदेश इकाई और हरीश रावत ने केदारनाथ प्रतिष्ठा, बदहाल स्वास्थ्य व्यवस्था और अंकिता न्याय पर सरकार को आड़े हाथों लिया।"
    },
    {
        "state": "Uttarakhand",
        "kind": "पत्रकार",
        "entity": "अजीत सिंह राठी",
        "date": "2026-11-14",
        "tone": "विश्लेषणात्मक",
        "point": "वरिष्ठ पत्रकार अजीत सिंह राठी ने शासन में हालिया आईएएस/पीसीएस फेरबदल और दायित्वधारियों की नियुक्ति पर राजनीतिक विश्लेषण प्रस्तुत किया।"
    },
    {
        "state": "Himachal Pradesh",
        "kind": "मुख्य",
        "entity": "सुखविंदर सिंह सुक्खू",
        "date": "2026-11-14",
        "tone": "सकारात्मक",
        "point": "मुख्यमंत्री सुक्खू ने रामपुर लवी मेले में सदियों पुरानी तिब्बत-भारत व्यापारिक धरोहर का उल्लेख करते हुए पहाड़ी आर्थिकी को मजबूत करने का संकल्प दोहराया।"
    },
    {
        "state": "Himachal Pradesh",
        "kind": "मुख्य",
        "entity": "जयराम ठाकुर",
        "date": "2026-11-14",
        "tone": "आक्रामक",
        "point": "नेता प्रतिपक्ष जयराम ठाकुर ने सुक्खू सरकार की वित्तीय स्थिति और 6 सीपीएस की नियुक्ति पर कानूनी स्थिति को लेकर सरकार को घेरा।"
    }
]

RALLIES_EVENTS = [
    {
        "id": "rel_1",
        "state": "Uttarakhand",
        "date": "2026-11-15",
        "title": "अमित शाह का देहरादून दौरा व विशाल कार्यकर्ता जनसभा",
        "kind": "चुनावी रैली",
        "party": "भाजपा",
        "leaders": "अमित शाह (केंद्रीय गृह मंत्री), पुष्कर सिंह धामी (मुख्यमंत्री), महेंद्र भट्ट (प्रदेश अध्यक्ष)",
        "place": "बन्नू स्कूल ग्राउंड, देहरादून",
        "district": "देहरादून",
        "crowd": "45,000+",
        "about": "2027 के विधानसभा चुनाव अभियान का औपचारिक शंखनाद; बूथ कार्यकर्ताओं को सीधा संदेश।",
        "status": "आगामी",
        "key_speech": ["उत्तराखंड का विकास मोदी सरकार की सर्वोच्च प्राथमिकता", "समान नागरिक संहिता लागू कर धामी सरकार ने इतिहास रचा", "नकल माफिया और अतिक्रमण पर जीरो टॉलरेंस जारी रहेगा"]
    },
    {
        "id": "rel_2",
        "state": "Uttarakhand",
        "date": "2026-11-18",
        "title": "कांग्रेस न्याय यात्रा व अंकिता भंडारी जनाक्रोश रैली",
        "kind": "जनाक्रोश रैली",
        "party": "कांग्रेस",
        "leaders": "करण माहरा (प्रदेश अध्यक्ष), हरीश रावत (पूर्व सीएम), गणेश गोदियाल, यशपाल आर्य",
        "place": "गांधी पार्क से कलेक्ट्रेट, देहरादून",
        "district": "देहरादून",
        "crowd": "25,000+",
        "about": "अंकिता हत्याकांड में वीआईपी के खुलासे, सशक्त भू-कानून व मूल निवास 1950 को लागू करने की मांग।",
        "status": "आगामी",
        "key_speech": ["वीआईपी का नाम उजागर करे सरकार", "पहाड़ की जमीनों की खुली लूट बंद हो", "युवाओं पर लाठियां बरसाने वाली सरकार को जनता सबक सिखाएगी"]
    },
    {
        "id": "rel_3",
        "state": "Himachal Pradesh",
        "date": "2026-11-14",
        "title": "अंतरराष्ट्रीय लवी मेला सांस्कृतिक व व्यापारिक महाकुंभ",
        "kind": "राजकीय मेला व जनसभा",
        "party": "सरकार",
        "leaders": "सुखविंदर सिंह सुक्खू (मुख्यमंत्री), कुलदीप राठौर (विधायक)",
        "place": "पदम स्कूल मैदान, रामपुर बुशहर",
        "district": "शिमला",
        "crowd": "30,000+",
        "about": "सदियों पुराने भारत-तिब्बत व्यापारिक उत्सव व हस्तशिल्प प्रदर्शनी का उद्घाटन।",
        "status": "संपन्न",
        "key_speech": ["हिमाचल की प्राचीन संस्कृति व व्यापार को नई तकनीक से जोड़ेंगे", "पर्वतीय किसानों व बुनकरों को सीधा बाजार उपलब्ध कराएंगे"]
    }
]


def export_sheets():
    print("Exporting latest data from Google Sheets tabs...")
    import urllib.parse
    import urllib.request

    tabs = [
        ("X-UK", "x_uk.csv"),
        ("journalist twitter posts UK,HP", "journalists_x.csv"),
        ("ETV- HP & UK Data", "etv_news.csv"),
        ("DB & AU - UK & HP", "db_au_news.csv"),
        ("Uttrakhand {Print Reports}", "uk_print.csv"),
        ("Himachal {Print Reports}", "hp_print.csv")
    ]
    for tab_name, filename in tabs:
        out_path = os.path.join(TEMP_DIR, filename)
        cmd = ["gsheets", "readonly", "export", SPREADSHEET_ID, out_path, "--sheet", tab_name]
        try:
            print(f"  Fetching '{tab_name}' -> {filename}...")
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if res.returncode == 0:
                print(f"    [OK via CLI] {filename}")
                continue
            else:
                print(f"    [CLI Notice] {res.stderr.strip()}")
        except (FileNotFoundError, Exception) as e:
            pass

        # Fallback: Direct HTTP export (for GitHub Actions runner in cloud)
        try:
            encoded_sheet = urllib.parse.quote(tab_name)
            url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=25) as resp:
                with open(out_path, "wb") as f_out:
                    f_out.write(resp.read())
            print(f"    [OK via HTTP] {filename}")
        except Exception as http_err:
            print(f"    [Notice] Using existing local copy for {filename} ({http_err})")

if "--no-export" not in sys.argv:
    export_sheets()

print("Executing complete sync...")
leader_posts = load_x_uk()
journalist_posts = load_journalists_x()
etv_items = load_etv_news()
db_au_items = load_db_au_news()
uk_print = load_print_reports("uk_print.csv", "Uttarakhand")
hp_print = load_print_reports("hp_print.csv", "Himachal Pradesh")

# Combine news and dedupe
all_news = []
seen_news = set()
for item in (etv_items + db_au_items):
    key = f"{item['state']}|{item['headline'][:120]}"
    if key in seen_news:
        continue
    seen_news.add(key)
    all_news.append(item)

# Sort news newest first
all_news.sort(key=lambda x: f"{x['date']} {x['time']}", reverse=True)
leader_posts.sort(key=lambda x: f"{x['date']} {x['time']}", reverse=True)
journalist_posts.sort(key=lambda x: f"{x['date']} {x['time']}", reverse=True)
print_reports = uk_print + hp_print
print_reports.sort(key=lambda x: x['date'], reverse=True)

# Build Master Output
output_data = {
    "meta": {
        "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p IST"),
        "total_news": len(all_news),
        "total_leader_posts": len(leader_posts),
        "total_journalist_posts": len(journalist_posts),
        "total_print": len(print_reports),
        "available_dates": {
            "min": "2026-10-25",
            "max": "2026-11-14"
        }
    },
    "news": all_news[:1500],
    "leader_posts": leader_posts,
    "journalist_posts": journalist_posts,
    "print_reports": print_reports[:1500],
    "entities": ENTITIES,
    "insights": INSIGHTS,
    "rallies_events": RALLIES_EVENTS
}

with open(DATA_JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

with open(DATA_JS_PATH, "w", encoding="utf-8") as f:
    f.write("window.DASHBOARD_DATA = " + json.dumps(output_data, ensure_ascii=False) + ";\n")

print(f"Sync complete! News: {len(all_news)}, Leader X: {len(leader_posts)}, Journalist X: {len(journalist_posts)}, Print: {len(print_reports)}")
