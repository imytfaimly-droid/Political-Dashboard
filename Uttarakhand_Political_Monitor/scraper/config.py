# -*- coding: utf-8 -*-
"""
Dashboard ke saare sources aur keywords yahin se badlo.
Naya portal ya naya keyword jodna ho to sirf ye file edit karo.
"""

# ---------------- Data retention ----------------
# data.json me kitne din ka data rahe (dashboard ka sabse bada filter 30 din ka hai)
KEEP_DAYS_IN_DASHBOARD = 30
# data.json me zyada se zyada kitni khabrein (page halka rahe)
MAX_ITEMS_IN_DASHBOARD = 800
# har run me har query se kitni khabrein li jayen
MAX_ITEMS_PER_QUERY = 25

# ---------------- Google News RSS searches ----------------
# Har state ke liye Hindi + English queries. "when:2d" = pichle 2 din ki khabrein.
# Free hai, koi API key nahi chahiye.
STATE_QUERIES = {
    "Uttarakhand": [
        "उत्तराखंड भाजपा",
        "उत्तराखंड कांग्रेस",
        "उत्तराखंड सरकार मुख्यमंत्री",
        "उत्तराखंड विधानसभा OR विधायक OR मंत्री",
        "उत्तराखंड चुनाव",
        "Uttarakhand BJP Congress politics",
    ],
    "Uttar Pradesh": [
        "उत्तर प्रदेश भाजपा",
        "यूपी सपा कांग्रेस",
        "उत्तर प्रदेश सरकार मुख्यमंत्री",
        "Uttar Pradesh politics BJP SP",
    ],
    "Himachal Pradesh": [
        "हिमाचल कांग्रेस सरकार",
        "हिमाचल भाजपा",
        "हिमाचल प्रदेश मुख्यमंत्री",
        "Himachal Pradesh politics Congress BJP",
    ],
    "National": [
        "भाजपा कांग्रेस राष्ट्रीय राजनीति",
        "चुनाव आयोग विपक्ष",
        "संसद केंद्र सरकार विपक्ष",
        "India politics BJP Congress",
    ],
}

# Portal-wise searches (dashboard ke portal filter ke liye). site: se sirf us portal ki khabar.
PORTAL_SITES = {
    "Amar Ujala": "amarujala.com",
    "Dainik Jagran": "jagran.com",
    "Hindustan": "livehindustan.com",
    "Indian Express": "indianexpress.com",
    "Hindustan Times": "hindustantimes.com",
    "The Print": "theprint.in",
    "ETV Bharat": "etvbharat.com",
}
# Har portal ke saath ye state words search honge
PORTAL_STATE_WORDS = {
    "Uttarakhand": "उत्तराखंड OR Uttarakhand",
    "Uttar Pradesh": "उत्तर प्रदेश OR Uttar Pradesh",
    "Himachal Pradesh": "हिमाचल OR Himachal",
}

# Seedhe RSS feeds (agar kisi portal ka apna RSS link pata ho to yahan jodo).
# Format: ("Portal ka naam", "State", "https://...rss")
# State me "AUTO" likho to khabar ke text se state pehchani jayegi.
DIRECT_FEEDS = [
    # ("Samvad 365", "Uttarakhand", "https://example.com/feed"),
]

# ---------------- Publisher naam ko dashboard ke naam se milana ----------------
PUBLISHER_ALIASES = {
    "amar ujala": "Amar Ujala",
    "अमर उजाला": "Amar Ujala",
    "dainik jagran": "Dainik Jagran",
    "दैनिक जागरण": "Dainik Jagran",
    "jagran": "Dainik Jagran",
    "live hindustan": "Hindustan",
    "हिन्दुस्तान": "Hindustan",
    "हिंदुस्तान": "Hindustan",
    "hindustan times": "Hindustan Times",
    "the indian express": "Indian Express",
    "indian express": "Indian Express",
    "theprint": "The Print",
    "the print": "The Print",
    "etv bharat": "ETV Bharat",
    "ईटीवी भारत": "ETV Bharat",
}

# ---------------- State pehchan (AUTO feeds + cross-check) ----------------
STATE_KEYWORDS = {
    "Uttarakhand": ["उत्तराखंड", "uttarakhand", "देहरादून", "dehradun", "हरिद्वार", "haridwar",
                     "नैनीताल", "हल्द्वानी", "गढ़वाल", "कुमाऊं", "ऋषिकेश", "उधम सिंह नगर", "अल्मोड़ा"],
    "Uttar Pradesh": ["उत्तर प्रदेश", "यूपी", "uttar pradesh", " up ", "लखनऊ", "lucknow", "प्रयागराज",
                      "वाराणसी", "गोरखपुर", "अयोध्या", "कानपुर", "आगरा", "मेरठ"],
    "Himachal Pradesh": ["हिमाचल", "himachal", "शिमला", "shimla", "मंडी", "कांगड़ा", "धर्मशाला", "कुल्लू", "हमीरपुर"],
}

# ---------------- Rajnitik khabar filter ----------------
POLITICAL_KEYWORDS = [
    "भाजपा", "बीजेपी", "कांग्रेस", "सपा", "बसपा", "विपक्ष", "सरकार", "मुख्यमंत्री", "सीएम",
    "मंत्री", "विधायक", "सांसद", "विधानसभा", "लोकसभा", "राज्यसभा", "चुनाव", "निकाय", "पंचायत",
    "प्रदेश अध्यक्ष", "नेता", "राजनीति", "सियासी", "सियासत", "आंदोलन", "धरना", "प्रदर्शन", "घेराव",
    "bjp", "congress", "minister", "mla", "mp ", "election", "chief minister", "cm ", "opposition",
    "assembly", "government", "politic", "party", "protest", "poll",
]

# ---------------- Category (pehla match jeetega) ----------------
CATEGORY_RULES = [
    ("चुनाव", ["चुनाव", "मतदान", "उपचुनाव", "निकाय", "पंचायत चुनाव", "टिकट", "प्रत्याशी", "election", "poll", "bypoll", "एसआईआर", "sir ", "मतदाता सूची"]),
    ("विरोध/आंदोलन", ["धरना", "प्रदर्शन", "आंदोलन", "घेराव", "हंगामा", "बवाल", "बंद", "protest", "agitation"]),
    ("भ्रष्टाचार/घोटाला", ["घोटाला", "भ्रष्टाचार", "रिश्वत", "घपला", "scam", "corruption", "ed ", "सीबीआई", "विजिलेंस"]),
    ("कानून-व्यवस्था", ["पुलिस", "गिरफ्तार", "हत्या", "अपराध", "मुकदमा", "fir", "कानून व्यवस्था", "arrest", "crime"]),
    ("आपदा/पर्यावरण", ["आपदा", "भूस्खलन", "बादल फटा", "बाढ़", "भूकंप", "जंगल की आग", "disaster", "landslide", "flood"]),
    ("विकास/योजना", ["योजना", "शिलान्यास", "लोकार्पण", "उद्घाटन", "परियोजना", "बजट", "निवेश", "सड़क", "स्कीम", "scheme", "project", "inaugurat"]),
    ("संगठन/दल", ["प्रदेश अध्यक्ष", "संगठन", "कार्यकारिणी", "शामिल", "इस्तीफा", "दल बदल", "बैठक", "joins", "resign"]),
    ("न्यायालय", ["हाईकोर्ट", "सुप्रीम कोर्ट", "अदालत", "कोर्ट", "high court", "supreme court"]),
]
DEFAULT_CATEGORY = "राजनीतिक अपडेट"

# ---------------- Severity / Sentiment ----------------
HIGH_ALERT_WORDS = ["विरोध", "प्रदर्शन", "हंगामा", "आरोप", "घोटाला", "गिरफ्तार", "हमला", "इस्तीफा", "बवाल",
                    "घेराव", "धरना", "भ्रष्टाचार", "निलंबित", "विवाद", "नाराज", "बगावत", "protest", "allege",
                    "scam", "arrest", "attack", "resign", "row", "controversy"]
POSITIVE_WORDS = ["शिलान्यास", "लोकार्पण", "उद्घाटन", "मंजूरी", "स्वीकृति", "सौगात", "विकास", "सम्मान",
                  "उपलब्धि", "जीत", "inaugurat", "approved", "launch", "boost"]
NEGATIVE_WORDS = HIGH_ALERT_WORDS + ["निशाना", "हमलावर", "विफल", "नाकाम", "सवाल", "घेरा", "attack", "slam", "fail"]

# ---------------- Optional free AI (Google Gemini) ----------------
# GitHub repo ke Settings > Secrets me GEMINI_API_KEY daaloge to har nayi khabar ka
# Hindi vishleshan (kya hua / kyun mahatvpurn / rajnitik asar) AI likhega.
# Key nahi hai to bhi sab chalega, bas vishleshan simple rahega.
AI_MAX_NEW_ITEMS_PER_RUN = 20
AI_BATCH_SIZE = 10
