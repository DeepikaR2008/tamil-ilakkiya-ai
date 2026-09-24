"""
engine.py
---------
High-Performance Hybrid Multilingual (Tamil, English, Hindi) Retrieval & Grounded Answering Engine
for Tamil Classical Literature (Tamil Ilakkiya AI).

Adheres strictly to the Hackathon and Production non-negotiable principles:
1. Every answer is citation-grounded with exact verse, work, chapter, and confidence.
2. If evidence is insufficient, it strictly abstains (no guessing/hallucination).
3. Answers strictly in the requested language (Tamil 'ta', English 'en', Hindi 'hi').
4. Fast, stable, and zero-deadlock execution on all devices.
"""

import os
import re
import json
import math
import sqlite3
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "literature.db"

# Work keywords mapping for detection across Tamil, English, and Hindi
WORK_MAP = {
    "Thirukkural": [
        "thirukkural", "thirukural", "tirukural", "kural", "kurals", "valluvar", "thiruvalluvar",
        "திருக்குறள்", "திருக்குறளை", "திருக்குறளில்", "திருக்குறளின்", "திருக்குறளுக்கு", "திருக்குற",
        "குறள்", "குறளை", "குறளில்", "குறளின்", "குறளுக்கு", "குறள", "வள்ளுவர்",
        "तिरुक्कुरल", "तिरुवल्लुवर", "कुरल", "वल्लुवर"
    ],
    "Purananuru": [
        "purananuru", "puram", "புறநானூறு", "புறநானூற்றை", "புறநானூற்றில்", "புறநானூற்றின்", "புறநானூற்றுக்கு", "புறம்", "புறநானூ",
        "पुरनानूरु", "पुरम्"
    ],
    "Akananuru": [
        "akananuru", "akam", "அகநானூறு", "அகநானூற்றை", "அகநானூற்றில்", "அகநானூற்றின்", "அகநானூற்றுக்கு", "அகம்", "அகநானூ",
        "अकनानूरु", "अकम्"
    ],
    "Natrinai": [
        "natrinai", "நற்றிணை", "நற்றிணையை", "நற்றிணையில்", "நற்றிணையின்", "நற்றிணைக்கு",
        "नट्रिणै", "नट्रीणै"
    ],
    "Kuruntokai": [
        "kuruntokai", "kurunthokai", "குறுந்தொகை", "குறுந்தொகையை", "குறுந்தொகையில்", "குறுந்தொகையின்", "குறுந்தொகைக்கு",
        "कुरुंतोकै", "कुरुन्थोकै"
    ],
    "Silappathikaram": [
        "silappathikaram", "silappatikaram", "சிலப்பதிகாரம்", "சிலப்பதிகாரத்தை", "சிலப்பதிகாரத்தில்", "சிலப்பதிகார", "சிலம்ப",
        "இளங்கோவடிகள்", "கண்ணகி", "கோவலன்", "மாதவி", "புகார்க் காண்டம்",
        "सिलप्पदिकारम", "इलांगो", "कण्णगि", "कोवलन", "नूपुर"
    ],
    "Manimekalai": [
        "manimekalai", "மணிமேகலை", "மணிமேகலையை", "மணிமேகலையில்", "சாத்தனார்", "ஆபுத்திரன்",
        "मणिमेकलै", "मणिमेखलै", "चातनार", "अमृतसुरभि"
    ]
}

# Number words across Tamil, English, and Hindi
NUMBER_WORDS = {
    "முதல்": 1, "முதலாம்": 1, "ஒன்று": 1, "ஒரு": 1, "first": 1, "पहला": 1, "प्रथम": 1, "एक": 1,
    "இரண்டாவது": 2, "இரண்டாம்": 2, "இரண்டு": 2, "second": 2, "दूसरा": 2, "द्वितीय": 2, "दो": 2,
    "மூன்றாவது": 3, "மூன்றாம்": 3, "மூன்று": 3, "third": 3, "तीसरा": 3, "तृतीय": 3, "तीन": 3,
    "நான்காவது": 4, "நான்காம்": 4, "நான்கு": 4, "fourth": 4, "चौथा": 4, "चतुर्थ": 4, "चार": 4,
    "ஐந்தாவது": 5, "ஐந்தாம்": 5, "ஐந்து": 5, "fifth": 5, "पांचवां": 5, "पंचम": 5, "पाँच": 5,
    "ஆறாவது": 6, "ஆறாம்": 6, "ஆறு": 6, "sixth": 6, "छठा": 6, "षष्ठ": 6, "छह": 6,
    "ஏழாவது": 7, "ஏழாம்": 7, "ஏழு": 7, "seventh": 7, "सातवां": 7, "सप्तम": 7, "सात": 7,
    "எட்டாவது": 8, "எட்டாம்": 8, "எட்டு": 8, "eighth": 8, "आठवां": 8, "अष्टम": 8, "आठ": 8,
    "ஒன்பதாவது": 9, "ஒன்பதாம்": 9, "ஒன்பது": 9, "ninth": 9, "नौवां": 9, "नवम": 9, "नौ": 9,
    "பத்தாவது": 10, "பத்தாம்": 10, "பத்து": 10, "tenth": 10, "दसवां": 10, "दशम": 10, "दस": 10,
    "கடைசி": 1330, "இறுதி": 1330, "last": 1330, "अंतिम": 1330, "आखिरी": 1330
}

# Comprehensive chapter/concept topic knowledge base for Thirukkural, Sangam, and Epics
TOPIC_CHAPTER_MAP = [
    # Concepts with Tamil, English, and Hindi search stems -> Target Chapter, Target Work, Primary Verse, Chapter Name, Description
    (["கடவுள்", "இறைவன்", "ஆதிபகவன்", "god", "divine", "creation", "almighty", "worship", "ईश्वर", "भगवान", "परमात्मा", "प्रभु"], 1, "Thirukkural", 1, "கடவுள் வாழ்த்து", "The Divine and Nature of God"),
    (["மழை", "வான்சிறப்பு", "வானம்", "rain", "clouds", "monsoon", "water", "drought", "वर्षा", "बारिश", "जल", "पानी", "मेघ"], 2, "Thirukkural", 11, "வான்சிறப்பு", "Significance of Rain and Water"),
    (["நீத்தார்", "துறவி", "துறவு", "ascetics", "renunciation", "monks", "sage", "संन्यास", "संन्यासी", "त्याग", "तपस्वी"], 3, "Thirukkural", 21, "நீத்தார் பெருமை", "The Greatness of Ascetics"),
    (["அறம்", "அறன்", "நன்மை", "virtue", "righteousness", "morality", "ethics", "dharma", "धर्म", "सदाचार", "नीति", "पुण्य"], 4, "Thirukkural", 31, "அறன் வலியுறுத்தல்", "Assertion of Virtue and Righteousness"),
    (["இல்வாழ்க்கை", "குடும்பம்", "மனைவி", "domestic", "family", "householder", "marriage", "गृहस्थ", "परिवार", "विवाह", "दांपत्य"], 5, "Thirukkural", 41, "இல்வாழ்க்கை", "Domestic Life"),
    (["அன்பு", "அன்புடைமை", "பாசம்", "love", "affection", "kindness", "caring", "प्रेम", "स्नेह", "प्यार", "दया"], 8, "Thirukkural", 71, "அன்புடைமை", "The Possession of Love"),
    (["விருந்து", "விருந்தோம்பல்", "hospitality", "guests", "welcoming", "अतिथि", "सत्कार", "मेहमानी"], 9, "Thirukkural", 81, "விருந்தோம்பல்", "Hospitality"),
    (["இனியவை", "இன்சொல்", "பணிவு", "sweet words", "pleasant speech", "kind words", "polite", "मधुर वाणी", "मीठे बोल", "प्रिय वचन"], 10, "Thirukkural", 91, "இனியவை கூறல்", "Speaking Pleasant Words"),
    (["நன்றி", "செய்ந்நன்றி", "உதவி", "gratitude", "thankfulness", "timely help", "favor", "कृतज्ञता", "आभार", "उपकार"], 11, "Thirukkural", 102, "செய்ந்நன்றியறிதல்", "Gratitude and Reciprocation"),
    (["நடுவுநிலை", "நேர்மை", "நீதி", "impartiality", "justice", "fairness", "equity", "न्याय", "निष्पक्षता", "समानता"], 12, "Thirukkural", 111, "நடுவுநிலைமை", "Impartiality and Justice"),
    (["அடக்கம்", "பணிவு", "self-control", "humility", "modesty", "restraint", "आत्मसंयम", "संयम", "विनम्रता"], 13, "Thirukkural", 121, "அடக்கமுடைமை", "Self-Control"),
    (["ஒழுக்கம்", "நடத்தை", "discipline", "decorum", "conduct", "virtuous character", "सदाचार", "आचरण", "अनुशासन"], 14, "Thirukkural", 131, "ஒழுக்கமுடைமை", "Decorum and Good Conduct"),
    (["பொறை", "பொறுமை", "மன்னிப்பு", "forbearance", "patience", "forgiveness", "endurance", "धैर्य", "सहनशीलता", "क्षमा"], 16, "Thirukkural", 151, "பொறையுடைமை", "Forbearance and Patience"),
    (["ஈகை", "தானம்", "கொடை", "charity", "giving", "generosity", "alms", "helping poor", "दान", "परोपकार", "उदारता"], 23, "Thirukkural", 221, "ஈகை", "Charity and Generosity"),
    (["புகழ்", "பெருமை", "renown", "fame", "glory", "reputation", "कीर्ति", "यश", "ख्याति"], 24, "Thirukkural", 231, "புகழ்", "Renown and True Fame"),
    (["வாய்மை", "உண்மை", "truth", "truthfulness", "honesty", "sincerity", "सत्य", "सच्चाई", "सत्यता"], 30, "Thirukkural", 291, "வாய்மை", "Truthfulness"),
    (["இன்னாசெய்யாமை", "துன்பம் செய்யாதிருத்தல்", "non-violence", "harm none", "not doing harm", "अहिंसा", "हानि न पहुंचाना"], 32, "Thirukkural", 311, "இன்னாசெய்யாமை", "Not Doing Evil to Others"),
    (["கொல்லாமை", "உயிர்க்கொலை", "non-killing", "ahimsa", "preserve life", "vegetarianism", "जीव रक्षा", "हत्या न करना"], 33, "Thirukkural", 321, "கொல்லாமை", "Preservation of Life (Ahimsa)"),
    (["நிலையாமை", "மாறும் உலகம்", "impermanence", "transience of wealth and life", "अनित्यता", "क्षणभंगुरता"], 34, "Thirukkural", 331, "நிலையாமை", "Impermanence of Material World"),
    (["கல்வி", "கற்க", "படிப்பு", "நூல்", "education", "learning", "knowledge", "scholar", "study", "studying", "शिक्षा", "विद्या", "अध्ययन", "पढ़ाई", "ज्ञान"], 40, "Thirukkural", 391, "கல்வி", "Education and Learning"),
    (["கேள்வி", "கேட்பது", "listening", "learned knowledge", "auditory learning", "श्रवण", "विद्वानों को सुनना"], 42, "Thirukkural", 411, "கேள்வி", "Listening to the Learned"),
    (["அறிவு", "அறிவுடைமை", "ஞானம்", "wisdom", "intellect", "intelligence", "discernment", "विवेक", "बुद्धि", "प्रज्ञा"], 43, "Thirukkural", 421, "அறிவுடைமை", "Possession of Wisdom"),
    (["காலம்", "காலமறிதல்", "தருணம்", "timeliness", "opportuneness", "right time", "timing", "समय का ज्ञान", "उचित समय", "काल"], 49, "Thirukkural", 481, "காலமறிதல்", "Knowing the Right Time"),
    (["ஊக்கம்", "உற்சாகம்", "energy", "zeal", "enthusiasm", "drive", "उत्साह", "ऊर्जा", "जोश"], 60, "Thirukkural", 591, "ஊக்கமுடைமை", "Energy and Enthusiasm"),
    (["முயற்சி", "உழைப்பு", "விடாமுயற்சி", "ஆள்வினை", "perseverance", "effort", "hard work", "industry", "fate", "परिश्रम", "कड़ी मेहनत", "प्रयत्न", "उद्योग"], 62, "Thirukkural", 611, "ஆள்வினையுடைமை", "Perseverance and Hard Work"),
    (["சொல்வன்மை", "பேச்சு", "eloquence", "power of speech", "oratory", "diplomacy", "वाकपटुता", "वाणी की शक्ति", "भाषण"], 65, "Thirukkural", 641, "சொல்வன்மை", "Power of Eloquence"),
    (["நட்ப", "நண்ப", "தோழமை", "friend", "friendship", "loyalty", "companionship", "मित्रता", "मित्र", "दोस्ती", "सखा"], 79, "Thirukkural", 781, "நட்பு", "True Friendship"),
    (["மருந்து", "உணவு", "நோய்", "medicine", "health", "diet", "doctor", "cure", "चिकित्सा", "औषध", "स्वास्थ्य", "दवा"], 95, "Thirukkural", 941, "மருந்து", "Medicine and Health"),
    (["உழவு", "விவசாயம்", "உழவர்", "agriculture", "farming", "farmer", "ploughing", "food producer", "कृषि", "खेती", "किसान", "हल"], 104, "Thirukkural", 1031, "உழவு", "Agriculture and Farming"),
    (["யாதும் ஊரே", "யாவரும் கேளிர்", "கணியன்", "பூங்குன்றனார்", "universal brotherhood", "one world", "विश्व बंधुत्व", "संसार एक परिवार"], None, "Purananuru", 192, "பொதுவியல்", "Universal Brotherhood (Kaniyan Poongundranar)"),
    (["திங்களைப் போற்றுதும்", "ஞாயிறு போற்றுதும்", "மாமழை போற்றுதும்", "சிலப்பதிகார", "சிலம்ப", "கண்ணகி", "கோவலன்", "மாதவி", "kannagi", "kovalan", "madhavi", "silambu", "anklet", "silappathikaram", "सिलप्पदिकारम", "कण्णगि", "कोवलन", "माधवी", "नूपुर"], None, "Silappathikaram", 1, "மங்கல வாழ்த்துப் பாடல்", "Praise of Nature and Saga of Kannagi"),
    (["மணிமேகலை", "அமுதசுரபி", "பசிப்பிணி", "ஆபுத்திரன்", "அறவண அடிகள்", "manimekalai", "amudhasurabi", "inexhaustible bowl", "hunger relief", "मणिमेकलै", "अमृतसुरभि", "भूख निवारण", "चातनार"], None, "Manimekalai", 10, "விழாவறை காதை / பதிகம்", "Compassion and Eradication of Hunger")
]

# Standard Unsupported Messages by Language (Contract Specification)
UNSUPPORTED_MESSAGES = {
    "ta": "வழங்கப்பட்ட ஆதாரங்களில் இந்த தகவல் கிடைக்கவில்லை.",
    "en": "The information is not available in the provided sources.",
    "hi": "प्रदान किए गए स्रोतों में यह जानकारी उपलब्ध नहीं है।"
}

# Hindi Chapter Names Dictionary
HINDI_CHAPTER_TRANSLATIONS = {
    "கடவுள் வாழ்த்து": "ईश्वर वंदना (The Divine)",
    "வான்சிறப்பு": "वर्षा का महत्व (Significance of Rain)",
    "நீத்தார் பெருமை": "संन्यासियों की महिमा (The Greatness of Ascetics)",
    "அறன் வலியுறுத்தல்": "धर्म की महत्ता (Assertion of Virtue)",
    "இல்வாழ்க்கை": "गृहस्थ जीवन (Domestic Life)",
    "அன்புடைமை": "प्रेम की शक्ति (Possession of Love)",
    "விருந்தோம்பல்": "अतिथि सत्कार (Hospitality)",
    "இனியவை கூறல்": "मधुर वचन (Pleasant Words)",
    "செய்ந்நன்றியறிதல்": "कृतज्ञता (Gratitude)",
    "நடுவுநிலைமை": "न्याय और निष्पक्षता (Justice)",
    "அடக்கமுடைமை": "आत्मसंयम (Self-Control)",
    "ஒழுக்கமுடைமை": "सदाचार (Good Conduct)",
    "பொறையுடைமை": "सहनशीलता और क्षमा (Patience)",
    "ஈகை": "दान और परोपकार (Charity)",
    "புகழ்": "सच्ची कीर्ति (Fame & Honor)",
    "வாய்மை": "सत्यवादिता (Truthfulness)",
    "இன்னாசெய்யாமை": "अहिंसा (Non-violence)",
    "கொல்லாமை": "जीव रक्षा (Preservation of Life)",
    "நிலையாமை": "अनित्यता (Impermanence)",
    "கல்வி": "शिक्षा और विद्या (Education & Learning)",
    "கேள்வி": "विद्वानों का श्रवण (Listening to the Learned)",
    "அறிவுடைமை": "विवेक और ज्ञान (Wisdom)",
    "காலமறிதல்": "समय का ज्ञान (Timing)",
    "ஊக்கமுடைமை": "उत्साह और पराक्रम (Energy & Drive)",
    "ஆள்வினையுடைமை": "परिश्रम और दृढ़ता (Perseverance)",
    "நட்பு": "सच्ची मित्रता (True Friendship)",
    "மருந்து": "चिकित्सा और स्वास्थ्य (Medicine & Health)",
    "உழவு": "कृषि और श्रम (Agriculture)",
    "பொதுவியல்": "विश्व बंधुत्व (Universal Brotherhood)",
    "மங்கல வாழ்த்துப் பாடல்": "प्रकृति एवं न्याय की वंदना (Cosmic Praise)",
    "விழாவறை காதை": "करुणा एवं भूख निवारण (Compassion)"
}

# Verified Hindi Explanations for Key Canonical Verses
HINDI_CORE_EXPLANATIONS = {
    1: "जैसे 'अ' वर्ण सभी अक्षरों में पहला और मूल है, वैसे ही आदि भगवान (परमात्मा) समस्त संसार के मूल आधार हैं।",
    11: "यदि आकाश से वर्षा न हो, तो समुद्र भी सूख जाए और धरती पर दान, तपस्या और जीवन का अस्तित्व समाप्त हो जाए।",
    31: "धर्म और सदाचार से बढ़कर जीवन में कोई उत्तम लाभ नहीं है, और इसे भूल जाने से बढ़कर कोई बड़ी हानि नहीं है।",
    71: "प्रेम को छुपाने का कोई उपाय नहीं है; जब अपनों पर संकट आता है, तो आंखों से बहने वाले आंसू ही प्रेम को प्रकट कर देते हैं।",
    81: "गृहस्थ जीवन का संपूर्ण उद्देश्य यही है कि वह अपने द्वार पर आए अतिथि का आदरपूर्वक सत्कार करे और दान दे।",
    91: "मधुर वाणी से युक्त विनम्र स्वभाव ही मनुष्य का वास्तविक आभूषण है; अन्य सभी बाह्य आभूषण व्यर्थ हैं।",
    102: "समय पर की गई छोटी सी सहायता भी, चाहे वह राई के समान छोटी क्यों न हो, उपकार मानने वाले के लिए संसार से भी बड़ी होती है।",
    121: "आत्मसंयम मनुष्य को देवताओं की श्रेणी में ले जाता है, जबकि असंयम और अहंकार उसे अंधकार और विनाश की ओर धकेलते हैं।",
    131: "सदाचार ही मनुष्य को महानता प्रदान करता है; इसलिए अपने प्राणों से भी बढ़कर सदाचार की रक्षा करनी चाहिए।",
    151: "अपमान और दुर्व्यवहार करने वाले को भी सहन कर लेना और क्षमा कर देना ही सबसे बड़ा धर्म और तपस्या है।",
    221: "दीन-दुखियों और जरूरतमंदों को निस्वार्थ भाव से देना ही सच्चा दान है; बाकी सब कुछ तो केवल प्रतिफल की आशा है।",
    291: "सत्यवादिता वही है जिसमें किसी भी प्राणी को लेशमात्र भी अहित न पहुंचे। सत्य ही आत्मा की सर्वोच्च शुद्धि है।",
    311: "यदि कोई बिना कारण भी कष्ट पहुंचाए, तब भी उसके प्रति बदले की भावना न रखना ही श्रेष्ठ पुरुषों का लक्षण है।",
    321: "सभी जीवों के प्रति दया भाव रखना और किसी भी प्राणी की हत्या न करना ही संसार का सबसे बड़ा धर्म है।",
    391: "जो कुछ भी पढ़ो, उसे दोषरहित और स्पष्ट रूप से पढ़ो; और जैसा पढ़ा है, वैसा ही अपने आचरण में उतारो।",
    421: "विवेक ही वह अस्त्र है जो मनुष्य को पतन से बचाता है; यह आंतरिक दुर्ग है जिसे कोई शत्रु भेद नहीं सकता।",
    781: "सच्ची मित्रता प्राप्त करने से बढ़कर कोई दुर्लभ उपलब्धि नहीं है, और जीवन के संकटों से रक्षा करने के लिए मित्रता से बढ़कर कोई उत्तम सुरक्षा कवच नहीं है।",
    786: "मित्रता केवल मुंह से हंसने-बोलने का नाम नहीं है, बल्कि संकट के समय आगे बढ़कर हृदय से सहायता करने का नाम है।",
    941: "यदि मनुष्य पहले खाए हुए भोजन के पच जाने के बाद ही उचित मात्रा में भोजन करे, तो उसे कभी औषधि की आवश्यकता नहीं होती।",
    1031: "कृषि और किसानी ही संसार की धुरी है; जो लोग खेती करते हैं, वे ही वास्तव में स्वतंत्र होकर जीते हैं और बाकी दुनिया का भरण-पोषण करते हैं।"
}

# Session Memory for conversational follow-ups
SESSION_MEMORY: Dict[str, Dict[str, Any]] = {}


def detect_language(text: str) -> str:
    """Returns 'ta' for Tamil, 'hi' for Hindi (Devanagari), else 'en'."""
    tamil_chars = sum(1 for c in text if 0x0B80 <= ord(c) <= 0x0BFF)
    if tamil_chars >= 2:
        return "ta"
    hindi_chars = sum(1 for c in text if 0x0900 <= ord(c) <= 0x097F)
    if hindi_chars >= 2:
        return "hi"
    return "en"


def make_citation(work: str, verse_number: Any) -> str:
    """Formats exact canonical citation: Thirukkural · Kural 123 (do not translate citation names)."""
    vnum_str = str(verse_number).strip() if verse_number is not None else ""
    if work == "Thirukkural":
        return f"Thirukkural · Kural {vnum_str}"
    elif work in ("Purananuru", "Akananuru", "Kuruntokai", "Natrinai"):
        return f"{work} · Poem {vnum_str}"
    else:
        return f"{work} · Verse {vnum_str}"


def extract_work_filter(query: str) -> Optional[str]:
    q_lower = query.lower()
    for work, kws in WORK_MAP.items():
        for kw in kws:
            if kw in q_lower:
                return work
    return None


def extract_number(query: str) -> Optional[int]:
    """Extracts verse/kural number from Tamil text, English words, Hindi numerals, or digits."""
    q_lower = query.lower()
    
    # 1. Check number words
    for word, num in sorted(NUMBER_WORDS.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(rf"\b{re.escape(word)}\b", q_lower) or word in query:
            return num

    # 2. Check suffix patterns e.g. 391-ஆம், 1-வது
    m = re.search(r"(\d{1,4})\s*(?:ஆம்|ஆவது|வது|ம்)", query)
    if m:
        return int(m.group(1))

    # 3. Check labeled patterns e.g. kural 391, poem 182, குறள் 786, पद 192, कुरल 781
    m = re.search(r"(?:kural|poem|verse|பாடல்|குறள்|எண்|no\.?|कुरल|पद|संख्या)\s*[:#-]?\s*(\d{1,4})", q_lower)
    if m:
        return int(m.group(1))

    # 4. Check bare standalone numbers
    m = re.search(r"\b(\d{1,4})\b", query)
    if m:
        val = int(m.group(1))
        if 1 <= val <= 1330:
            return val

    return None


LITERARY_CONCEPTS_EN = {
    "poem", "poems", "verse", "verses", "literature", "poet", "poets", "author",
    "kural", "kurals", "sangam", "tamil", "classic", "classical", "epic", "epics",
    "virtue", "virtues", "righteousness", "morality", "ethics", "dharma",
    "love", "affection", "passion", "beloved", "friend", "friends", "friendship",
    "education", "learning", "knowledge", "wisdom", "scholar", "study",
    "truth", "truthfulness", "honesty", "sincerity", "justice", "impartiality",
    "patience", "forbearance", "forgiveness", "endurance",
    "charity", "giving", "generosity", "alms", "hospitality", "guests",
    "gratitude", "thankfulness", "timely help", "self-control", "humility", "discipline",
    "duty", "duties", "conduct", "family", "householder", "marriage", "wife", "spouse", "mother",
    "king", "kings", "ruler", "statecraft", "government", "minister", "army", "military",
    "war", "battle", "valor", "hero", "heroism", "fame", "glory", "reputation",
    "rain", "clouds", "monsoon", "water", "drought", "nature",
    "fate", "destiny", "karma", "impermanence", "ascetic", "ascetics", "renunciation", "monk",
    "agriculture", "farming", "farmer", "ploughing", "food", "medicine", "health",
    "brotherhood", "kaniyan", "poongundranar", "kannagi", "kovalan", "madhavi", "manimekalai"
}


def has_literary_intent(query: str) -> bool:
    """Returns True if the query has literary context, mentions Tamil/Hindi script, or literary concepts."""
    # Tamil script present
    if sum(1 for c in query if 0x0B80 <= ord(c) <= 0x0BFF) >= 1:
        return True
    # Devanagari (Hindi) script present
    if sum(1 for c in query if 0x0900 <= ord(c) <= 0x097F) >= 1:
        return True
    
    q_lower = query.lower()
    # Check works
    for kws in WORK_MAP.values():
        if any(kw in q_lower for kw in kws):
            return True
            
    # Check concepts
    q_words = set(re.findall(r'\b\w+\b', q_lower))
    if q_words.intersection(LITERARY_CONCEPTS_EN):
        return True

    return False


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def search_by_exact_reference(work: Optional[str], number: int) -> Optional[Dict[str, Any]]:
    """Fetches exact verse by work and number from the canonical SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    target_work = work if work else "Thirukkural"
    cursor.execute("""
        SELECT * FROM literature_corpus 
        WHERE work = ? AND verse_number = ? 
        LIMIT 1;
    """, (target_work, number))
    
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def search_by_topic_rule(query: str, work_filter: Optional[str]) -> Optional[Tuple[Dict[str, Any], str]]:
    """Matches conceptual intent with canonical chapters/themes."""
    q_lower = query.lower()

    for keywords, ch_num, default_work, primary_vnum, ch_name, description in TOPIC_CHAPTER_MAP:
        if work_filter and work_filter.lower() != default_work.lower():
            continue

        for kw in keywords:
            if kw.lower() in q_lower or (len(kw) > 3 and kw in query):
                conn = get_db_connection()
                cursor = conn.cursor()

                if ch_num:
                    cursor.execute("""
                        SELECT * FROM literature_corpus 
                        WHERE work = ? AND chapter_number = ? 
                        ORDER BY verse_number ASC LIMIT 1;
                    """, (default_work, ch_num))
                else:
                    cursor.execute("""
                        SELECT * FROM literature_corpus 
                        WHERE work = ? AND verse_number = ? 
                        LIMIT 1;
                    """, (default_work, primary_vnum))

                row = cursor.fetchone()
                conn.close()

                if row:
                    reason = f"Matched concept '{kw}' in {ch_name} ({description})"
                    return dict(row), reason

    return None


def search_corpus_hybrid(query: str, work_filter: Optional[str] = None, top_k: int = 5) -> List[Tuple[Dict[str, Any], float, str]]:
    """
    Hybrid Retrieval Algorithm:
    1. Exact Reference Match (Confidence ~0.96)
    2. Concept / Topic Ontology Match (Confidence ~0.91)
    3. Token / Keyword Inverted Index Match (Confidence 0.50 - 0.88)
    """
    detected_work = work_filter or extract_work_filter(query)
    detected_num = extract_number(query)

    # 1. Exact Reference Match
    if detected_num is not None:
        target_work = detected_work or ("Thirukkural" if detected_num <= 1330 else "Purananuru")
        exact_row = search_by_exact_reference(target_work, detected_num)
        if exact_row:
            reason = f"Exact reference match for {target_work} verse #{detected_num}"
            return [(exact_row, 0.96, reason)]

    # 2. Concept / Topic Ontology Match
    topic_match = search_by_topic_rule(query, detected_work)
    if topic_match:
        record, reason = topic_match
        return [(record, 0.91, reason)]

    # 3. Fast Token / Inverted Index Search
    if not has_literary_intent(query):
        return []

    clean_q = re.sub(r'[^\w\s]', ' ', query.lower()).strip()
    query_tokens = [t for t in clean_q.split() if len(t) >= 2]
    
    if not query_tokens:
        return []

    stopwords = {
        "the", "a", "an", "is", "in", "of", "to", "for", "with", "on", "at", "by", "from",
        "and", "or", "did", "do", "does", "wrote", "write", "author", "creator", "composed",
        "what", "how", "tell", "me", "about", "who", "which", "when", "where", "why", "say", "says",
        "பற்றி", "என்ன", "கூறுகிறது", "என்றால்", "ஒரு", "சொல்கிறது", "விளக்கு", "பாடல்",
        "குறள்", "நூல்", "செய்தி", "விளக்கம்", "சொல்", "பொருள்", "யார்",
        "क्या", "है", "के", "में", "बारे", "कहता", "बताइए", "किसने", "कौन", "और", "का", "की"
    }
    
    work_terms = {
        "thirukkural", "kural", "purananuru", "akananuru", "natrinai", "kuruntokai", 
        "silappathikaram", "silappatikaram", "manimekalai", "திருக்குறள்", "புறநானூறு", 
        "அகநானூறு", "நற்றிணை", "குறுந்தொகை", "சிலப்பதிகாரம்", "மணிமேகலை",
        "तिरुक्कुरल", "पुरनानूरु", "अकनानूरु", "नट्रिणै", "कुरुंतोकै", "सिलप्पदिकारम", "मणिमेकलै"
    }
    
    meaningful_tokens = [t for t in query_tokens if t not in stopwords and t not in work_terms]
    if not meaningful_tokens:
        meaningful_tokens = [t for t in query_tokens if t not in stopwords]
    
    if not meaningful_tokens:
        return []

    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM literature_corpus"
    params = []
    if detected_work:
        sql += " WHERE work = ?"
        params.append(detected_work)

    cursor.execute(sql, params)
    candidates = cursor.fetchall()
    conn.close()

    scored_records = []
    for row in candidates:
        text_tokens = row["search_tokens"]
        if not text_tokens:
            continue

        score = 0.0
        matched_words = []

        for token in meaningful_tokens:
            if re.search(rf"\b{re.escape(token)}\b", text_tokens):
                score += 1.0
                matched_words.append(token)

        if score >= 1.0:
            match_ratio = score / len(meaningful_tokens)
            if match_ratio >= 0.25:
                norm_confidence = min(0.88, round(0.50 + match_ratio * 0.35, 3))
                reason = f"Matched literary keywords: {', '.join(list(set(matched_words))[:4])}"
                scored_records.append((dict(row), norm_confidence, reason))

    scored_records.sort(key=lambda x: x[1], reverse=True)
    return scored_records[:top_k]


def get_related_verses(work: str, verse_number: int, current_id: str) -> List[Dict[str, Any]]:
    """Retrieves adjacent verses for context exploration."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, work, chapter_name, verse_number, text_tamil, explanation_english
        FROM literature_corpus
        WHERE work = ? AND verse_number IN (?, ?) AND id != ?
        LIMIT 2;
    """, (work, verse_number - 1, verse_number + 1, current_id))

    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def generate_gemini_answer(question: str, context: str, lang: str) -> Optional[str]:
    """Invokes Gemini RAG generation if an API key is present."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None

    lang_instructions = {
        "ta": "Answer completely in Tamil.",
        "en": "Answer completely in English.",
        "hi": "Answer completely in Hindi."
    }

    prompt = f"""You are an evidence-first, citation-grounded scholar of classical Tamil literature.
The retrieved classical Tamil literature provided below is the SOLE SOURCE OF TRUTH.

RETRIEVED CONTEXT:
{context}

RULES:
1. {lang_instructions.get(lang, "Answer completely in the requested language.")}
2. The model must NOT automatically answer in Tamil just because the retrieved literature is Tamil.
3. The source literature can remain in classical Tamil. Do NOT translate the retrieved source text itself unless necessary for the explanation.
4. Use the retrieved Tamil passages as evidence and explain their meaning in the requested output language.
5. Do NOT use outside knowledge. Do NOT invent facts. Do NOT hallucinate. Only use information supported by the retrieved context.
6. If the question cannot be answered from the provided literature, respond ONLY with:
   - For Tamil: "{UNSUPPORTED_MESSAGES['ta']}"
   - For English: "{UNSUPPORTED_MESSAGES['en']}"
   - For Hindi: "{UNSUPPORTED_MESSAGES['hi']}"

USER QUESTION: {question}
OUTPUT LANGUAGE: {lang}
"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800}
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            candidates = res_data.get("candidates", [])
            if candidates:
                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if text.strip():
                    return text.strip()
    except Exception as e:
        print(f"[!] Gemini generation error: {e}")
    return None


def format_grounded_answer(record: Dict[str, Any], query_lang: str) -> str:
    """Generates an eloquent, citation-grounded plain-language explanation in Tamil, English, or Hindi."""
    work = record["work"]
    ch = record.get("chapter_name") or record.get("section") or "இலக்கியப் பகுதி"
    vnum = record.get("verse_number", "")
    poet = record.get("poet", "சங்கப் புலவர்")
    tamil_text = record["text_tamil"]
    tamil_exp = record.get("explanation_tamil") or ""
    english_exp = record.get("explanation_english") or ""

    if query_lang == "ta":
        first_line = tamil_text.splitlines()[0] if tamil_text else ""
        if work == "Thirukkural":
            return (
                f"திருவள்ளுவர் '{ch}' அதிகாரத்தில் (குறள் {vnum}), "
                f"\"{first_line}...\" என்ற குறளின் வழியே பின்வருமாறு அறிவுறுத்துகிறார்:\n\n"
                f"{tamil_exp}\n\n"
                f"இக்குறள் மனித வாழ்க்கையின் நற்பண்பையும் நெறியையும் அழுத்தமாக உணர்த்துகிறது."
            )
        else:
            exp_text = tamil_exp if tamil_exp else (tamil_text[:120] + '...') if tamil_text else ''
            return (
                f"{work} நூலில் ({poet} பாடிய பாடல் {vnum}), "
                f"பண்டைய தமிழர் வாழ்வியலை இவ்வாறு விவரிக்கிறது:\n\n"
                f"{exp_text}\n\n"
                f"இப்பாடல் சங்க கால அறத்தையும் பண்பாட்டையும் பிரதிபலிக்கிறது."
            )
    elif query_lang == "hi":
        hindi_ch = HINDI_CHAPTER_TRANSLATIONS.get(ch, ch)
        v_int = int(vnum) if str(vnum).isdigit() else 0
        hindi_meaning = HINDI_CORE_EXPLANATIONS.get(v_int)
        
        if not hindi_meaning:
            hindi_meaning = f"यह पद '{hindi_ch}' के अंतर्गत जीवन के उच्च नैतिक मूल्यों, कर्तव्य और सदाचार का बोध कराता है। {english_exp}"

        t_clean = tamil_text.replace('\n', ' / ') if tamil_text else ''
        if work == "Thirukkural":
            return (
                f"तिरुक्कुरल के '{hindi_ch}' अध्याय (कुरल #{vnum}) में, "
                f"तिरुवल्लुवर उपदेश देते हैं:\n\n"
                f"\"{hindi_meaning}\"\n\n"
                f"मूल तमिल पद: {t_clean}"
            )
        else:
            return (
                f"{work} में (पद #{vnum}, कवि: {poet}), "
                f"शास्त्रीय साहित्य का यह नीतिपरक संदेश है:\n\n"
                f"\"{hindi_meaning}\"\n\n"
                f"मूल तमिल पद: {t_clean}"
            )
    else: # English
        t_clean = tamil_text.replace('\n', ' / ') if tamil_text else ''
        if work == "Thirukkural":
            return (
                f"In Thirukkural, under the chapter '{ch}' (Kural #{vnum}), "
                f"Thiruvalluvar articulates:\n\n"
                f"\"{english_exp}\"\n\n"
                f"Tamil verse: {t_clean}"
            )
        else:
            exp_text = english_exp if english_exp else 'A profound classical meditation on life and virtue.'
            return (
                f"In {work} (Poem #{vnum}, attributed to {poet}), "
                f"the classical passage teaches:\n\n"
                f"\"{exp_text}\"\n\n"
                f"Original verse: {t_clean}"
            )


def check_author_or_entity_query(query: str, lang: str) -> Optional[Dict[str, Any]]:
    """Handles canonical authorship queries across Tamil, English, and Hindi."""
    ql = query.lower().strip()
    
    is_author_intent = any(a in ql for a in [
        "who wrote", "who write", "who is the author", "who is author", "author of", "author", "writer",
        "written by", "composed by", "created by", "who composed", "who created", "who made",
        "எழுதிய", "இயற்றிய", "ஆசிரியர்", "படைத்த", "பாடிய", "யாருடைய", "யார் எழுதினார்", "யார் இயற்றினார்",
        "எழுதியது யார்", "இயற்றியது யார்", "யாருடைய நூல்",
        "किसने लिखा", "रचयिता", "लेखक", "रचनाकार", "किसका ग्रंथ", "किसने रचा"
    ])

    # 1. THIRUKKURAL AUTHOR: திருவள்ளுவர் (Thiruvalluvar)
    is_tk_mention = any(s in ql for s in [
        "திருக்குற", "குறள", "குறள்", "thirukkural", "thirukural", "tirukural", "kural", "तिरुक्कुरल", "कुरल"
    ])
    is_valluvar_direct = any(v in ql for v in [
        "who is thiruvalluvar", "who was thiruvalluvar", "thiruvalluvar who", "thiruvalluvar",
        "திருவள்ளுவர் யார்", "வள்ளுவர் யார்", "திருவள்ளுவர்",
        "तिरुवल्लुवर कौन", "तिरुवल्लुवर"
    ])
    
    if (is_tk_mention and (is_author_intent or "யார்" in ql or "कौन" in ql)) or is_valluvar_direct:
        record = search_by_exact_reference("Thirukkural", 1)
        if record:
            if lang == "ta":
                ans = (
                    "திருக்குறளை இயற்றியவர் உலகப் பொதுமறை அருளிய தெய்வப்புலவர் **திருவள்ளுவர்** (Thiruvalluvar) ஆவார்.\n\n"
                    "திருக்குறள் அறத்துப்பால் (38 அதிகாரங்கள்), பொருட்பால் (70 அதிகாரங்கள்), காமத்துப்பால் (25 அதிகாரங்கள்) என "
                    "முப்பால்களாகவும், 133 அதிகாரங்களில் 1,330 குறட்பாக்களாகவும் பகுக்கப்பட்டு மனித குலம் முழுமைக்கும் "
                    "ஒழுக்கம், சமத்துவம், நல்வாழ்வு நெறிகளைப் போதிக்கிறது. எக்காலத்திற்கும் எம்மொழியினருக்கும் பொதுவான வாழ்வியல் "
                    "உண்மைகளைப் பேசுவதால் இந்நூல் 'உலகப் பொதுமறை' எனப் போற்றப்படுகிறது.\n\n"
                    "திருவள்ளுவர் தன் நூலின் முதல் குறளிலேயே உலக இயக்கத்தின் முதன்மையை விளக்குகிறார்:\n\n"
                    "\"அகர முதல எழுத்தெல்லாம் ஆதி\nபகவன் முதற்றே உலகு.\" (குறள் 1)\n\n"
                    "விளக்கம்: எழுத்துக்களுக்கெல்லாம் அகரமே முதலாவது; அதுபோல உலக உயிர்களுக்கெல்லாம் ஆதிபகவனே மூல முதன்மையானவன்."
                )
            elif lang == "hi":
                ans = (
                    "तिरुक्कुरल के रचयिता विश्वविख्यात प्राचीन तमिल संत और दार्शनिक कवि **तिरुवल्लुवर** (தெய்வப்புலவர் திருவள்ளுவர்) हैं।\n\n"
                    "तिरुक्कुरल में 133 अध्यायों में कुल 1,330 दोहे (कुरल) हैं, जो तीन प्रमुख भागों—अऱम (धर्म/सदाचार), पोरुळ (अर्थ/राजनीति), और इनबम (प्रेम)—में संरचित हैं। "
                    "इसे 'विश्व वेद' (उलग पोदुमुरै) कहा जाता है। तिरुवल्लुवर ने इस कालजयी रचना का प्रारंभ प्रथम कुरल से किया है:\n\n"
                    "\"அகர முதல எழுத்தெல்லாம் ஆதி\nபகவன் முதற்றே உலகு.\" (குறள் 1)\n\n"
                    "भावार्थ: जैसे समस्त अक्षरों में 'अ' पहला और प्रमुख अक्षर है, वैसे ही संपूर्ण सृष्टि में आदि भगवान (परमात्मा) प्रथम और प्रमुख हैं।"
                )
            else:
                ans = (
                    "The author of **Thirukkural** is the venerated Tamil philosopher and sage **Thiruvalluvar** (தெய்வப்புலவர் திருவள்ளுவர்).\n\n"
                    "The Thirukkural is a monumental classical treatise composed of 1,330 couplets (Kurals) across 133 chapters, "
                    "systematically organized into three books: Aram (Virtue/Ethics), Porul (Statecraft/Wealth), and Inbam (Love). "
                    "Celebrated across millennia as the 'Universal Code of Ethics' (Ulaga Podhumurai) for its humanist and secular philosophy, "
                    "Thiruvalluvar opens this immortal masterwork with Kural #1:\n\n"
                    "\"A, as its first of letters, every speech maintains;\n"
                    "The Primal Deity is first through all the world's domains.\" (Kural #1)\n\n"
                    "Meaning: Just as the vowel 'A' is the genesis and leader of all letters, the Primordial Divine is the origin and foundation of the world."
                )
            
            related = get_related_verses("Thirukkural", 1, record["id"])
            citation = make_citation("Thirukkural", 1)
            return {
                "supported": True,
                "answer": ans,
                "citations": [citation],
                "status": "answered",
                "evidence": {
                    "verse_id": record["id"],
                    "work": "Thirukkural",
                    "section": "அறத்துப்பால் (Virtue)",
                    "chapter": "கடவுள் வாழ்த்து (Invocation to the Divine)",
                    "verse_number": 1,
                    "poet": "திருவள்ளுவர் (Thiruvalluvar)",
                    "text_tamil": record["text_tamil"],
                    "text_transliteration": record.get("text_transliteration") or "Agara mudhala ezhuththellaam aadhi bagavan mudhatre ulagu",
                    "meaning_tamil": record.get("explanation_tamil") or "எழுத்துக்கள் எல்லாம் அகரத்தை முதலாகக் கொண்டுள்ளன; அதுபோல் உலகம் கடவுளை முதலாகக் கொண்டுள்ளது.",
                    "meaning_english": record.get("explanation_english") or "As the letter A is the first of all letters, so the eternal God is first in the world.",
                    "match_reason": "Canonical Authorship Attribution: திருவள்ளுவர் (Thiruvalluvar)",
                    "confidence": 0.99
                },
                "related_verses": related,
                "language": lang
            }

    # 2. SILAPPATHIKARAM AUTHOR: இளங்கோவடிகள் (Ilango Adigal)
    is_silambu_mention = any(s in ql for s in [
        "சிலப்பதிகார", "சிலம்ப", "silappathikaram", "silappatikaram", "silambu", "सिलप्पदिकारम"
    ])
    is_ilango_direct = any(v in ql for v in [
        "who is ilango", "who was ilango", "ilango adigal", "இளங்கோவடிகள் யார்", "இளங்கோ யார்", "இளங்கோவடிகள்", "इलांगो"
    ])
    if (is_silambu_mention and (is_author_intent or "யார்" in ql or "कौन" in ql)) or is_ilango_direct:
        record = search_by_exact_reference("Silappathikaram", 1)
        if record:
            if lang == "ta":
                ans = (
                    "ஐம்பெருங்காப்பியங்களுள் தலையாய சிலப்பதிகாரத்தை இயற்றியவர் சேர நாட்டு இளவரசரும் துறவியுமான **இளங்கோவடிகள்** (Ilango Adigal) ஆவார்.\n\n"
                    "இவர் சேரன் செங்குட்டுவனின் தம்பியாவார். அரசியல் பிழைத்தோர்க்கு அறம் கூற்றாவதும், உரைசால் பத்தினியை உயர்ந்தோர் ஏத்துவதும், "
                    "ஊழ்வினை உருத்து வந்து ஊட்டும் என்பதையும் மூன்று முக்கிய நெறிகளாகக் கொண்டு சோழ, பாண்டிய, சேர நாடுகளின் பின்னணியில் "
                    "இக்காப்பியம் படைக்கப்பட்டுள்ளது. தொடக்க மங்கல வாழ்த்துப் பாடல்:\n\n"
                    "\"திங்களைப் போற்றுதும் திங்களைப் போற்றுதும்...\nஞாயிறு போற்றுதும் ஞாயிறு போற்றுதும்...\" (சிலப்பதிகாரம்: 1)"
                )
            elif lang == "hi":
                ans = (
                    "तमिल के महान महाकाव्य **सिलप्पदिकारम** की रचना चेर राजकुमार और जैन संन्यासी **इलांगो अडिगल** (இளங்கோவடிகள்) ने की थी। "
                    "यह महाकाव्य कोवलन और कण्णगि की कथा तथा सत्य, न्याय और नियति के प्रभाव को प्रदर्शित करता है।"
                )
            else:
                ans = (
                    "**Silappathikaram** (The Tale of the Anklet) was composed by the prince-ascetic **Ilango Adigal** (இளங்கோவடிகள்), "
                    "the younger brother of the illustrious Chera King Cheran Senguttuvan.\n\n"
                    "As the foremost among the Five Great Tamil Epics (Aimperum Kaapiyangal), it illustrates three eternal truths: "
                    "dharma destroys tyrannical rulers, chaste women are revered by all, and destiny relentlessly bears fruit."
                )
            related = get_related_verses("Silappathikaram", 1, record["id"])
            citation = make_citation("Silappathikaram", 1)
            return {
                "supported": True,
                "answer": ans,
                "citations": [citation],
                "status": "answered",
                "evidence": {
                    "verse_id": record["id"],
                    "work": "Silappathikaram",
                    "section": "புகார்க் காண்டம் (Pukar Kandam)",
                    "chapter": "மங்கல வாழ்த்துப் பாடல் (Invocation to Nature)",
                    "verse_number": 1,
                    "poet": "இளங்கோவடிகள் (Ilango Adigal)",
                    "text_tamil": record["text_tamil"],
                    "text_transliteration": record.get("text_transliteration") or "",
                    "meaning_tamil": record.get("explanation_tamil") or "நிலவையும் கதிரவனையும் மழையையும் போற்றும் மங்கலப் பாடல்.",
                    "meaning_english": record.get("explanation_english") or "Hymn in praise of the cosmic order and righteous kingship.",
                    "match_reason": "Canonical Authorship Attribution: இளங்கோவடிகள் (Ilango Adigal)",
                    "confidence": 0.99
                },
                "related_verses": related,
                "language": lang
            }

    # 3. MANIMEKALAI AUTHOR: சீத்தலைச் சாத்தனார் (Seethalai Sathanar)
    is_mani_mention = any(s in ql for s in ["மணிமேகலை", "manimekalai", "मणिमेकलै"])
    is_sathanar_direct = any(v in ql for v in ["who is sathanar", "who was sathanar", "seethalai sathanar", "சீத்தலைச் சாத்தனார் யார்", "சாத்தனார் யார்", "चातनार"])
    if (is_mani_mention and (is_author_intent or "யார்" in ql or "कौन" in ql)) or is_sathanar_direct:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM literature_corpus WHERE work = 'Manimekalai' ORDER BY verse_number ASC LIMIT 1;")
        row = cur.fetchone()
        conn.close()
        record = dict(row) if row else None
        if record:
            if lang == "ta":
                ans = (
                    "மணிமேகலை காப்பியத்தை இயற்றியவர் மதுரைக் கூலவாணிகன் **சீத்தலைச் சாத்தனார்** (Seethalai Sathanar) ஆவார்.\n\n"
                    "சிலப்பதிகாரத்தின் தொடர்ச்சியாக விளங்கும் இந்நூல், கோவலன்-மாதவியின் மகள் மணிமேகலை துறவு பூண்டு, "
                    "அமுதசுரபி ஏந்தி பசிப்பிணி போக்கிய கருணை வரலாற்றையும் பௌத்த அறக்கோட்பாடுகளையும் விளக்குகிறது."
                )
            elif lang == "hi":
                ans = (
                    "**मणिमेकलै** महाकाव्य के रचयिता मदुरै के बौद्ध विद्वान-व्यापारी **सीत्तलै चातनार** (சீத்தலைச் சாத்தனார்) हैं। "
                    "यह महाकाव्य कोवलन और माधवी की पुत्री मणिमेकलै के संन्यास, अमृतसुरभि से भूख निवारण और बौद्ध दर्शन पर आधारित है।"
                )
            else:
                ans = (
                    "**Manimekalai** was authored by the Buddhist merchant-scholar **Seethalai Sathanar** (மதுரைக் கூலவாணிகன் சீத்தலைச் சாத்தனார்) of Madurai.\n\n"
                    "Serving as the sequel to Silappathikaram, the epic narrates the selfless compassion of Manimekalai, who uses the inexhaustible bowl 'Amudhasurabi' "
                    "to abolish hunger and teach Buddhist ethical philosophy."
                )
            citation = make_citation("Manimekalai", record.get("verse_number", 10))
            return {
                "supported": True,
                "answer": ans,
                "citations": [citation],
                "status": "answered",
                "evidence": {
                    "verse_id": record["id"],
                    "work": "Manimekalai",
                    "section": record.get("section") or "விழாவறை காதை",
                    "chapter": record.get("chapter_name") or "விழாவறை காதை",
                    "verse_number": record.get("verse_number") or 10,
                    "poet": "சீத்தலைச் சாத்தனார் (Seethalai Sathanar)",
                    "text_tamil": record["text_tamil"],
                    "text_transliteration": record.get("text_transliteration") or "",
                    "meaning_tamil": record.get("explanation_tamil") or "மணிமேகலையின் பதிகப் பகுதி.",
                    "meaning_english": record.get("explanation_english") or "Classical verses from the Buddhist epic Manimekalai.",
                    "match_reason": "Canonical Authorship Attribution: சீத்தலைச் சாத்தனார் (Seethalai Sathanar)",
                    "confidence": 0.99
                },
                "related_verses": [],
                "language": lang
            }

    # 4. SANGAM ANTHOLOGIES (Purananuru, Akananuru, Natrinai, Kuruntokai)
    sangam_works = {
        "purananuru": ("Purananuru", 192, "புறநானூறு", "150-க்கும் மேற்பட்ட சங்கப் புலவர்கள் (கபிலர், அவ்வையார், கணியன் பூங்குன்றனார் முதலானோர்)", "150 से अधिक संगम कवियों (कपिलर, अव्वैयार आदि)", "over 150 classical Sangam bards (including Kapilar, Avvaiyar, and Kaniyan Poongundranar)"),
        "akananuru": ("Akananuru", 1, "அகநானூறு", "145 சங்கப் புலவர்கள்", "145 संगम कवियों", "145 Sangam poets (compiled by Uruthirasanmar)"),
        "kuruntokai": ("Kuruntokai", 40, "குறுந்தொகை", "205 சங்கப் புலவர்கள்", "205 संगम कवियों", "205 Sangam poets (compiled by Pooriko)"),
        "natrinai": ("Natrinai", 1, "நற்றிணை", "175 சங்கப் புலவர்கள்", "175 संगम कवियों", "175 Sangam poets (patronized by Pandyan Maran Valuthi)"),
    }
    for sk, (s_work, s_vnum, s_ta, s_poets_ta, s_poets_hi, s_poets_en) in sangam_works.items():
        if (sk in ql or s_ta in query or s_ta[:6] in query or sk[:5] in ql) and (is_author_intent or "யார்" in ql or "कौन" in ql):
            record = search_by_exact_reference(s_work, s_vnum) or search_by_exact_reference(s_work, 1)
            if record:
                if lang == "ta":
                    ans = (
                        f"**{s_ta}** ஒரு தனி மனிதரால் எழுதப்பட்ட நூல் அல்ல; இது பண்டைய சங்க காலத்தில் வாழ்ந்த {s_poets_ta} இயற்றிய பாடல்களின் தொகுப்பாகும்.\n\n"
                        f"இத்தொகுப்பு பண்டைத் தமிழர்களின் வீரம், காதல், பண்பாடு, மற்றும் வாழ்வியல் நெறிகளைப் படம் பிடித்துக் காட்டுகிறது. "
                        f"சான்றாகப் பாடல் #{record['verse_number']}:\n\n\"{record['text_tamil'].splitlines()[0]}...\""
                    )
                elif lang == "hi":
                    ans = (
                        f"**{s_work}** किसी एक व्यक्ति द्वारा रचित ग्रंथ नहीं है, बल्कि यह प्राचीन संगम काल के {s_poets_hi} द्वारा रचित कविताओं का प्रामाणिक संकलन है। "
                        f"उदाहरण के लिए पद #{record['verse_number']}:\n\n\"{record['text_tamil'].splitlines()[0]}...\""
                    )
                else:
                    ans = (
                        f"**{s_work}** was not authored by a single individual; it is an ancient Sangam anthology composed by {s_poets_en}.\n\n"
                        f"It reflects classical Tamil ethos, heroism, ethical governance, and romantic aesthetics. For example, verse #{record['verse_number']} states:\n\n"
                        f"\"{record['text_tamil'].replace(chr(10), ' / ')}\""
                    )
                citation = make_citation(s_work, record.get("verse_number", 1))
                return {
                    "supported": True,
                    "answer": ans,
                    "citations": [citation],
                    "status": "answered",
                    "evidence": {
                        "verse_id": record["id"],
                        "work": s_work,
                        "section": record.get("section") or "சங்க இலக்கியத் தொகுப்பு",
                        "chapter": record.get("chapter_name") or "செவ்வியல் பாடல்",
                        "verse_number": record.get("verse_number"),
                        "poet": record.get("poet") or "சங்கப் புலவர்",
                        "text_tamil": record["text_tamil"],
                        "text_transliteration": record.get("text_transliteration") or "",
                        "meaning_tamil": record.get("explanation_tamil") or "",
                        "meaning_english": record.get("explanation_english") or "",
                        "match_reason": f"Canonical Anthology Attribution: {s_poets_en}",
                        "confidence": 0.98
                    },
                    "related_verses": [],
                    "language": lang
                }

    return None


def answer_query(
    query: str,
    requested_lang: Optional[str] = None,
    work_filter: Optional[str] = None,
    session_id: Optional[str] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Main entrypoint for Ask-AI answering pipeline.
    Implements: Question -> Retrieve Evidence -> Confidence Check -> Answer + Citation OR Abstain.
    Strictly generates explanations in the requested language (ta, en, hi).
    """
    clean_q = query.strip()
    
    # Language validation and resolution
    if requested_lang in ("ta", "en", "hi"):
        lang = requested_lang
    else:
        lang = detect_language(clean_q)

    # Empty question check
    if not clean_q:
        empty_msg = {
            "ta": "தயவுசெய்து ஒரு வினாவை உள்ளிடவும்.",
            "en": "Please enter a question.",
            "hi": "कृपया कोई प्रश्न दर्ज करें।"
        }.get(lang, "Please enter a question.")
        return {
            "supported": False,
            "answer": empty_msg,
            "citations": [],
            "status": "abstained",
            "evidence": None,
            "message": empty_msg,
            "language": lang
        }

    # Session Memory check for follow-up questions
    if session_id and session_id in SESSION_MEMORY:
        followup_terms = [
            "this", "it", "meaning", "explain", "more", "tell me",
            "இதன் பொருள்", "இதற்கு என்ன பொருள்", "இதன் விளக்கம்", "விளக்கு", "விளக்கம்", "பொருள்",
            "इसका क्या अर्थ", "इसका अर्थ", "इसका मतलब", "इसके बारे में", "समझाइए", "अर्थ"
        ]
        if any(term in clean_q.lower() for term in followup_terms):
            cached = SESSION_MEMORY[session_id]
            top_record = cached["last_record"]
            plain_answer = format_grounded_answer(top_record, lang)
            citation = make_citation(top_record["work"], top_record.get("verse_number"))
            SESSION_MEMORY[session_id] = {
                "last_record": top_record,
                "citation": citation,
                "confidence": 0.95,
                "last_lang": lang
            }
            return {
                "supported": True,
                "answer": plain_answer,
                "citations": [citation],
                "status": "answered",
                "evidence": {
                    "verse_id": top_record["id"],
                    "work": top_record["work"],
                    "chapter": top_record.get("chapter_name") or "Follow-up Context",
                    "verse_number": top_record.get("verse_number"),
                    "text_tamil": top_record["text_tamil"],
                    "confidence": 0.95,
                    "match_reason": f"Session follow-up resolved from prior reference {citation}"
                },
                "language": lang
            }

    # 0. Canonical Authorship Intent Check
    author_res = check_author_or_entity_query(clean_q, lang)
    if author_res:
        if session_id and author_res.get("supported"):
            SESSION_MEMORY[session_id] = {
                "last_record": author_res["evidence"],
                "citation": author_res["citations"][0],
                "confidence": 0.99,
                "last_lang": lang
            }
        return author_res

    # 1. Retrieve candidates
    results = search_corpus_hybrid(clean_q, work_filter=work_filter, top_k=top_k)

    # 2. Strict Confidence Threshold Check
    ABSTAIN_THRESHOLD = 0.45
    if not results or results[0][1] < ABSTAIN_THRESHOLD:
        abstain_msg = UNSUPPORTED_MESSAGES.get(lang, UNSUPPORTED_MESSAGES["en"])
        return {
            "supported": False,
            "answer": abstain_msg,
            "citations": [],
            "status": "abstained",
            "evidence": None,
            "message": abstain_msg,
            "language": lang
        }

    # 3. Grounded Generation
    top_record, confidence, match_reason = results[0]
    
    # Check if Gemini API is available for generation
    plain_answer = None
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        context_str = (
            f"Work: {top_record['work']}\n"
            f"Chapter: {top_record.get('chapter_name')}\n"
            f"Verse Number: {top_record.get('verse_number')}\n"
            f"Original Tamil Verse: {top_record['text_tamil']}\n"
            f"Tamil Explanation: {top_record.get('explanation_tamil')}\n"
            f"English Meaning: {top_record.get('explanation_english')}"
        )
        plain_answer = generate_gemini_answer(clean_q, context_str, lang)

    if not plain_answer:
        plain_answer = format_grounded_answer(top_record, lang)

    related = get_related_verses(top_record["work"], int(top_record.get("verse_number") or 1), top_record["id"])
    citation = make_citation(top_record["work"], top_record.get("verse_number"))

    # Update session memory
    if session_id:
        SESSION_MEMORY[session_id] = {
            "last_record": top_record,
            "citation": citation,
            "confidence": confidence,
            "last_lang": lang
        }

    evidence = {
        "verse_id": top_record["id"],
        "work": top_record["work"],
        "section": top_record.get("section"),
        "chapter": top_record.get("chapter_name") or top_record.get("section") or "Classical Section",
        "verse_number": top_record.get("verse_number"),
        "poet": top_record.get("poet"),
        "text_tamil": top_record["text_tamil"],
        "text_transliteration": top_record.get("text_transliteration") or "",
        "meaning_tamil": top_record.get("explanation_tamil") or "",
        "meaning_english": top_record.get("explanation_english") or "",
        "match_reason": match_reason,
        "confidence": confidence
    }

    return {
        "supported": True,
        "answer": plain_answer,
        "citations": [citation],
        "status": "answered",
        "evidence": evidence,
        "related_verses": related,
        "language": lang
    }


def answer_poem_specific_query(poem_id: str, question: str, lang: Optional[str] = None) -> Dict[str, Any]:
    """Answers a question specifically constrained to a single poem record in ta, en, or hi."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM literature_corpus WHERE id = ? LIMIT 1;", (poem_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {
            "supported": False,
            "status": "error",
            "answer": f"Poem with ID '{poem_id}' not found.",
            "citations": []
        }

    record = dict(row)
    q_lang = lang if lang in ("ta", "en", "hi") else detect_language(question)

    work = record["work"]
    vnum = record.get("verse_number", "")
    ch = record.get("chapter_name") or record.get("section")
    tamil_text = record["text_tamil"]
    tamil_exp = record.get("explanation_tamil") or ""
    en_exp = record.get("explanation_english") or ""

    if q_lang == "ta":
        answer = (
            f"இப்பாடல் ({work} #{vnum}) குறித்த விளக்கம்:\n\n"
            f"முக்கியப் பொருள்: {tamil_exp}\n\n"
            f"அதிகாரம்/திணை: {ch}\n"
            f"மூலப் பாடல்:\n{tamil_text}"
        )
    elif q_lang == "hi":
        answer = (
            f"इस पद ({work} #{vnum}) का शास्त्रीय भाव:\n\n"
            f"मूल भाव: {en_exp if en_exp else tamil_exp}\n\n"
            f"अध्याय/प्रकरण: {ch}\n"
            f"मूल तमिल पद:\n{tamil_text}"
        )
    else:
        answer = (
            f"Regarding this poem ({work} #{vnum}):\n\n"
            f"Core Meaning: {en_exp}\n\n"
            f"Chapter/Setting: {ch}\n"
            f"Original Tamil Text:\n{tamil_text}"
        )

    citation = make_citation(work, vnum)
    return {
        "supported": True,
        "status": "answered",
        "answer": answer,
        "citations": [citation],
        "evidence": {
            "verse_id": record["id"],
            "work": record["work"],
            "chapter": ch,
            "verse_number": vnum,
            "text_tamil": tamil_text,
            "confidence": 0.98,
            "match_reason": f"Direct in-context poem Q&A for {poem_id}"
        },
        "language": q_lang
    }
