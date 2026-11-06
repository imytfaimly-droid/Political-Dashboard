# -*- coding: utf-8 -*-
"""
Dashboard ke saare sources aur keywords yahin se badlo.
Naya portal ya naya keyword jodna ho to sirf ye file edit karo.
"""

# ---------------- Data retention ----------------
# data.json me kitne din ka data rahe (dashboard ka sabse bada filter 30 din ka hai)
KEEP_DAYS_IN_DASHBOARD = 30
# data.json me zyada se zyada kitni khabrein (30 din x ~200 roz; dashboard 60-60 karke dikhata hai)
MAX_ITEMS_IN_DASHBOARD = 8000
# har run me har query se kitni khabrein li jayen
MAX_ITEMS_PER_QUERY = 25

# ---------------- Google News RSS searches ----------------
# Har state ke liye Hindi + English queries. "when:2d" = pichle 2 din ki khabrein.
# Free hai, koi API key nahi chahiye.
STATE_QUERIES = {
    "Uttarakhand": [
        "\u0909\u0924\u094d\u0924\u0930\u093e\u0916\u0902\u0921 \u092d\u093e\u091c\u092a\u093e",
        "\u0909\u0924\u094d\u0924\u0930\u093e\u0916\u0902\u0921 \u0915\u093e\u0902\u0917\u094d\u0930\u0947\u0938",
        "\u0909\u0924\u094d\u0924\u0930\u093e\u0916\u0902\u0921 \u0938\u0930\u0915\u093e\u0930 \u092e\u0941\u0916\u094d\u092f\u092e\u0902\u0924\u094d\u0930\u0940",
        "\u0909\u0924\u094d\u0924\u0930\u093e\u0916\u0902\u0921 \u0935\u093f\u0927\u093e\u0928\u0938\u092d\u093e OR \u0935\u093f\u0927\u093e\u092f\u0915 OR \u092e\u0902\u0924\u094d\u0930\u0940",
        "\u0909\u0924\u094d\u0924\u0930\u093e\u0916\u0902\u0921 \u091a\u0941\u0928\u093e\u0935",
        "Uttarakhand BJP Congress politics",
    ],
    "Uttar Pradesh": [
        "\u0909\u0924\u094d\u0924\u0930 \u092a\u094d\u0930\u0926\u0947\u0936 \u092d\u093e\u091c\u092a\u093e",
        "\u092f\u0942\u092a\u0940 \u0938\u092a\u093e \u0915\u093e\u0902\u0917\u094d\u0930\u0947\u0938",
        "\u0909\u0924\u094d\u0924\u0930 \u092a\u094d\u0930\u0926\u0947\u0936 \u0938\u0930\u0915\u093e\u0930 \u092e\u0941\u0916\u094d\u092f\u092e\u0902\u0924\u094d\u0930\u0940",
        "Uttar Pradesh politics BJP SP",
    ],
    "Himachal Pradesh": [
        "\u0939\u093f\u092e\u093e\u091a\u0932 \u0915\u093e\u0902\u0917\u094d\u0930\u0947\u0938 \u0938\u0930\u0915\u093e\u0930",
        "\u0939\u093f\u092e\u093e\u091a\u0932 \u092d\u093e\u091c\u092a\u093e",
        "\u0939\u093f\u092e\u093e\u091a\u0932 \u092a\u094d\u0930\u0926\u0947\u0936 \u092e\u0941\u0916\u094d\u092f\u092e\u0902\u0924\u094d\u0930\u0940",
        "Himachal Pradesh politics Congress BJP",
    ],
    "National": [
        "\u092d\u093e\u091c\u092a\u093e \u0915\u093e\u0902\u0917\u094d\u0930\u0947\u0938 \u0930\u093e\u0937\u094d\u091f\u094d\u0930\u0940\u092f \u0930\u093e\u091c\u0928\u0940\u0924\u093f",
        "\u091a\u0941\u0928\u093e\u0935 \u0906\u092f\u094b\u0917 \u0935\u093f\u092a\u0915\u094d\u0937",
        "\u0938\u0902\u0938\u0926 \u0915\u0947\u0902\u0926\u094d\u0930 \u0938\u0930\u0915\u093e\u0930 \u0935\u093f\u092a\u0915\u094d\u0937",
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
    "Uttarakhand": "\u0909\u0924\u094d\u0924\u0930\u093e\u0916\u0902\u0921 OR Uttarakhand",
    "Uttar Pradesh": "\u0909\u0924\u094d\u0924\u0930 \u092a\u094d\u0930\u0926\u0947\u0936 OR Uttar Pradesh",
    "Himachal Pradesh": "\u0939\u093f\u092e\u093e\u091a\u0932 OR Himachal",
}

# Seedhe RSS feeds (agar kisi portal ka apna RSS link pata ho to yahan jodo).
# Format: ("Portal ka naam", "State", "https://...rss")
# State me "AUTO" likho to khabar ke text se state pehchani jayegi.
DIRECT_FEEDS = [
    # ("Samvad 365", "Uttarakhand", "https://example.com/feed"),
]

# Portal ke state page seedhe padhe jaate hain (in sites ka RSS nahi hai).
# Format: ("Portal ka naam", "State", "page link", "parser")
# parser: "etv" = ETV Bharat jaisi Next.js site, "bhaskar" = Dainik Bhaskar
PAGE_SOURCES = [
    ("ETV Bharat", "Uttarakhand", "https://www.etvbharat.com/hi/uttarakhand/!state", "etv"),
    ("ETV Bharat", "Himachal Pradesh", "https://www.etvbharat.com/hi/himachal-pradesh/!state", "etv"),
    ("Dainik Bhaskar", "Uttarakhand", "https://www.bhaskar.com/local/uttarakhand/", "bhaskar"),
    ("Dainik Bhaskar", "Himachal Pradesh", "https://www.bhaskar.com/local/himachal/", "bhaskar"),
]

# ---------------- Publisher naam ko dashboard ke naam se milana ----------------
PUBLISHER_ALIASES = {
    "amar ujala": "Amar Ujala",
    "\u0905\u092e\u0930 \u0909\u091c\u093e\u0932\u093e": "Amar Ujala",
    "dainik jagran": "Dainik Jagran",
    "\u0926\u0948\u0928\u093f\u0915 \u091c\u093e\u0917\u0930\u0923": "Dainik Jagran",
    "jagran": "Dainik Jagran",
    "live hindustan": "Hindustan",
    "\u0939\u093f\u0928\u094d\u0926\u0941\u0938\u094d\u0924\u093e\u0928": "Hindustan",
    "\u0939\u093f\u0902\u0926\u0941\u0938\u094d\u0924\u093e\u0928": "Hindustan",
    "hindustan times": "Hindustan Times",
    "the indian express": "Indian Express",
    "indian express": "Indian Express",
    "theprint": "The Print",
    "the print": "The Print",
    "etv bharat": "ETV Bharat",
    "\u0908\u091f\u0940\u0935\u0940 \u092d\u093e\u0930\u0924": "ETV Bharat",
    "dainik bhaskar": "Dainik Bhaskar",
    "\u0926\u0948\u0928\u093f\u0915 \u092d\u093e\u0938\u094d\u0915\u0930": "Dainik Bhaskar",
    "bhaskar": "Dainik Bhaskar",
}

# ---------------- State pehchan (AUTO feeds + cross-check) ----------------
STATE_KEYWORDS = {
    "Uttarakhand": ["\u0909\u0924\u094d\u0924\u0930\u093e\u0916\u0902\u0921", "uttarakhand", "\u0926\u0947\u0939\u0930\u093e\u0926\u0942\u0928", "dehradun", "\u0939\u0930\u093f\u0926\u094d\u0935\u093e\u0930", "haridwar",
                     "\u0928\u0948\u0928\u0940\u0924\u093e\u0932", "\u0939\u0932\u094d\u0926\u094d\u0935\u093e\u0928\u0940", "\u0917\u0922\u093c\u0935\u093e\u0932", "\u0915\u0941\u092e\u093e\u090a\u0902", "\u090b\u0937\u093f\u0915\u0947\u0936", "\u0909\u0927\u092e \u0938\u093f\u0902\u0939 \u0928\u0917\u0930", "\u0905\u0932\u094d\u092e\u094b\u0921\u093c\u093e"],
    "Uttar Pradesh": ["\u0909\u0924\u094d\u0924\u0930 \u092a\u094d\u0930\u0926\u0947\u0936", "\u092f\u0942\u092a\u0940", "uttar pradesh", " up ", "\u0932\u0916\u0928\u090a", "lucknow", "\u092a\u094d\u0930\u092f\u093e\u0917\u0930\u093e\u091c",
                      "\u0935\u093e\u0930\u093e\u0923\u0938\u0940", "\u0917\u094b\u0930\u0916\u092a\u0941\u0930", "\u0905\u092f\u094b\u0927\u094d\u092f\u093e", "\u0915\u093e\u0928\u092a\u0941\u0930", "\u0906\u0917\u0930\u093e", "\u092e\u0947\u0930\u0920"],
    "Himachal Pradesh": ["\u0939\u093f\u092e\u093e\u091a\u0932", "himachal", "\u0936\u093f\u092e\u0932\u093e", "shimla", "\u092e\u0902\u0921\u0940", "\u0915\u093e\u0902\u0917\u0921\u093c\u093e", "\u0927\u0930\u094d\u092e\u0936\u093e\u0932\u093e", "\u0915\u0941\u0932\u094d\u0932\u0942", "\u0939\u092e\u0940\u0930\u092a\u0941\u0930"],
}

# ---------------- Rajnitik khabar filter ----------------
POLITICAL_KEYWORDS = [
    "\u092d\u093e\u091c\u092a\u093e", "\u092c\u0940\u091c\u0947\u092a\u0940", "\u0915\u093e\u0902\u0917\u094d\u0930\u0947\u0938", "\u0938\u092a\u093e", "\u092c\u0938\u092a\u093e", "\u0935\u093f\u092a\u0915\u094d\u0937", "\u0938\u0930\u0915\u093e\u0930", "\u092e\u0941\u0916\u094d\u092f\u092e\u0902\u0924\u094d\u0930\u0940", "\u0938\u0940\u090f\u092e",
    "\u092e\u0902\u0924\u094d\u0930\u0940", "\u0935\u093f\u0927\u093e\u092f\u0915", "\u0938\u093e\u0902\u0938\u0926", "\u0935\u093f\u0927\u093e\u0928\u0938\u092d\u093e", "\u0932\u094b\u0915\u0938\u092d\u093e", "\u0930\u093e\u091c\u094d\u092f\u0938\u092d\u093e", "\u091a\u0941\u0928\u093e\u0935", "\u0928\u093f\u0915\u093e\u092f", "\u092a\u0902\u091a\u093e\u092f\u0924",
    "\u092a\u094d\u0930\u0926\u0947\u0936 \u0905\u0927\u094d\u092f\u0915\u094d\u0937", "\u0928\u0947\u0924\u093e", "\u0930\u093e\u091c\u0928\u0940\u0924\u093f", "\u0938\u093f\u092f\u093e\u0938\u0940", "\u0938\u093f\u092f\u093e\u0938\u0924", "\u0906\u0902\u0926\u094b\u0932\u0928", "\u0927\u0930\u0928\u093e", "\u092a\u094d\u0930\u0926\u0930\u094d\u0936\u0928", "\u0918\u0947\u0930\u093e\u0935",
    "bjp", "congress", "minister", "mla", "mp ", "election", "chief minister", "cm ", "opposition",
    "assembly", "government", "politic", "party", "protest", "poll",
]

# ---------------- Category (pehla match jeetega) ----------------
CATEGORY_RULES = [
    ("\u091a\u0941\u0928\u093e\u0935", ["\u091a\u0941\u0928\u093e\u0935", "\u092e\u0924\u0926\u093e\u0928", "\u0909\u092a\u091a\u0941\u0928\u093e\u0935", "\u0928\u093f\u0915\u093e\u092f", "\u092a\u0902\u091a\u093e\u092f\u0924 \u091a\u0941\u0928\u093e\u0935", "\u091f\u093f\u0915\u091f", "\u092a\u094d\u0930\u0924\u094d\u092f\u093e\u0936\u0940", "election", "poll", "bypoll", "\u090f\u0938\u0906\u0908\u0906\u0930", "sir ", "\u092e\u0924\u0926\u093e\u0924\u093e \u0938\u0942\u091a\u0940"]),
    ("\u0935\u093f\u0930\u094b\u0927/\u0906\u0902\u0926\u094b\u0932\u0928", ["\u0927\u0930\u0928\u093e", "\u092a\u094d\u0930\u0926\u0930\u094d\u0936\u0928", "\u0906\u0902\u0926\u094b\u0932\u0928", "\u0918\u0947\u0930\u093e\u0935", "\u0939\u0902\u0917\u093e\u092e\u093e", "\u092c\u0935\u093e\u0932", "\u092c\u0902\u0926", "protest", "agitation"]),
    ("\u092d\u094d\u0930\u0937\u094d\u091f\u093e\u091a\u093e\u0930/\u0918\u094b\u091f\u093e\u0932\u093e", ["\u0918\u094b\u091f\u093e\u0932\u093e", "\u092d\u094d\u0930\u0937\u094d\u091f\u093e\u091a\u093e\u0930", "\u0930\u093f\u0936\u094d\u0935\u0924", "\u0918\u092a\u0932\u093e", "scam", "corruption", "ed ", "\u0938\u0940\u092c\u0940\u0906\u0908", "\u0935\u093f\u091c\u093f\u0932\u0947\u0902\u0938"]),
    ("\u0915\u093e\u0928\u0942\u0928-\u0935\u094d\u092f\u0935\u0938\u094d\u0925\u093e", ["\u092a\u0941\u0932\u093f\u0938", "\u0917\u093f\u0930\u092b\u094d\u0924\u093e\u0930", "\u0939\u0924\u094d\u092f\u093e", "\u0905\u092a\u0930\u093e\u0927", "\u092e\u0941\u0915\u0926\u092e\u093e", "fir", "\u0915\u093e\u0928\u0942\u0928 \u0935\u094d\u092f\u0935\u0938\u094d\u0925\u093e", "arrest", "crime"]),
    ("\u0906\u092a\u0926\u093e/\u092a\u0930\u094d\u092f\u093e\u0935\u0930\u0923", ["\u0906\u092a\u0926\u093e", "\u092d\u0942\u0938\u094d\u0916\u0932\u0928", "\u092c\u093e\u0926\u0932 \u092b\u091f\u093e", "\u092c\u093e\u0922\u093c", "\u092d\u0942\u0915\u0902\u092a", "\u091c\u0902\u0917\u0932 \u0915\u0940 \u0906\u0917", "disaster", "landslide", "flood"]),
    ("\u0935\u093f\u0915\u093e\u0938/\u092f\u094b\u091c\u0928\u093e", ["\u092f\u094b\u091c\u0928\u093e", "\u0936\u093f\u0932\u093e\u0928\u094d\u092f\u093e\u0938", "\u0932\u094b\u0915\u093e\u0930\u094d\u092a\u0923", "\u0909\u0926\u094d\u0918\u093e\u091f\u0928", "\u092a\u0930\u093f\u092f\u094b\u091c\u0928\u093e", "\u092c\u091c\u091f", "\u0928\u093f\u0935\u0947\u0936", "\u0938\u0921\u093c\u0915", "\u0938\u094d\u0915\u0940\u092e", "scheme", "project", "inaugurat"]),
    ("\u0938\u0902\u0917\u0920\u0928/\u0926\u0932", ["\u092a\u094d\u0930\u0926\u0947\u0936 \u0905\u0927\u094d\u092f\u0915\u094d\u0937", "\u0938\u0902\u0917\u0920\u0928", "\u0915\u093e\u0930\u094d\u092f\u0915\u093e\u0930\u093f\u0923\u0940", "\u0936\u093e\u092e\u093f\u0932", "\u0907\u0938\u094d\u0924\u0940\u092b\u093e", "\u0926\u0932 \u092c\u0926\u0932", "\u092c\u0948\u0920\u0915", "joins", "resign"]),
    ("\u0928\u094d\u092f\u093e\u092f\u093e\u0932\u092f", ["\u0939\u093e\u0908\u0915\u094b\u0930\u094d\u091f", "\u0938\u0941\u092a\u094d\u0930\u0940\u092e \u0915\u094b\u0930\u094d\u091f", "\u0905\u0926\u093e\u0932\u0924", "\u0915\u094b\u0930\u094d\u091f", "high court", "supreme court"]),
]
DEFAULT_CATEGORY = "\u0930\u093e\u091c\u0928\u0940\u0924\u093f\u0915 \u0905\u092a\u0921\u0947\u091f"

# ---------------- Severity / Sentiment ----------------
HIGH_ALERT_WORDS = ["\u0935\u093f\u0930\u094b\u0927", "\u092a\u094d\u0930\u0926\u0930\u094d\u0936\u0928", "\u0939\u0902\u0917\u093e\u092e\u093e", "\u0906\u0930\u094b\u092a", "\u0918\u094b\u091f\u093e\u0932\u093e", "\u0917\u093f\u0930\u092b\u094d\u0924\u093e\u0930", "\u0939\u092e\u0932\u093e", "\u0907\u0938\u094d\u0924\u0940\u092b\u093e", "\u092c\u0935\u093e\u0932",
                    "\u0918\u0947\u0930\u093e\u0935", "\u0927\u0930\u0928\u093e", "\u092d\u094d\u0930\u0937\u094d\u091f\u093e\u091a\u093e\u0930", "\u0928\u093f\u0932\u0902\u092c\u093f\u0924", "\u0935\u093f\u0935\u093e\u0926", "\u0928\u093e\u0930\u093e\u091c", "\u092c\u0917\u093e\u0935\u0924", "protest", "allege",
                    "scam", "arrest", "attack", "resign", "row", "controversy"]
POSITIVE_WORDS = ["\u0936\u093f\u0932\u093e\u0928\u094d\u092f\u093e\u0938", "\u0932\u094b\u0915\u093e\u0930\u094d\u092a\u0923", "\u0909\u0926\u094d\u0918\u093e\u091f\u0928", "\u092e\u0902\u091c\u0942\u0930\u0940", "\u0938\u094d\u0935\u0940\u0915\u0943\u0924\u093f", "\u0938\u094c\u0917\u093e\u0924", "\u0935\u093f\u0915\u093e\u0938", "\u0938\u092e\u094d\u092e\u093e\u0928",
                  "\u0909\u092a\u0932\u092c\u094d\u0927\u093f", "\u091c\u0940\u0924", "inaugurat", "approved", "launch", "boost"]
NEGATIVE_WORDS = HIGH_ALERT_WORDS + ["\u0928\u093f\u0936\u093e\u0928\u093e", "\u0939\u092e\u0932\u093e\u0935\u0930", "\u0935\u093f\u092b\u0932", "\u0928\u093e\u0915\u093e\u092e", "\u0938\u0935\u093e\u0932", "\u0918\u0947\u0930\u093e", "attack", "slam", "fail"]

# ---------------- Optional free AI (Google Gemini) ----------------
# GitHub repo ke Settings > Secrets me GEMINI_API_KEY daaloge to har nayi khabar ka
# Hindi vishleshan (kya hua / kyun mahatvpurn / rajnitik asar) AI likhega.
# Key nahi hai to bhi sab chalega, bas vishleshan simple rahega.
AI_MAX_NEW_ITEMS_PER_RUN = 20
AI_BATCH_SIZE = 10
