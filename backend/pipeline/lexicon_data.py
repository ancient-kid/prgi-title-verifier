"""
Stage 4C: Multilingual Cross-Lingual Concept Lexicon Data

Structured lexical repository mapping cross-lingual semantic concepts across
English and major Indian languages:
- Hindi (hi), Bengali (bn), Tamil (ta), Telugu (te), Marathi (mr),
- Gujarati (gu), Kannada (kn), Malayalam (ml), Punjabi (pa), Urdu (ur), Odia (or).

Audited for precision: preserves clear distinctions between distinct concepts
(e.g., nation vs state, great vs chief, news vs message).
"""

from typing import Any, Dict, List, Set

CONCEPT_REGISTRY: List[Dict[str, Any]] = [
    # --- Periodicities ---
    {
        "concept": "daily",
        "category": "periodicity",
        "language_variants": {
            "en": ["daily", "dailies"],
            "hi": ["dainik", "rozana", "roznama"],
            "bn": ["pratidin", "dainik"],
            "ta": ["dinamalar", "dinakaran", "naalthorum"],
            "te": ["dinapatrika", "prathidhwani"],
            "mr": ["dainik", "rojnama"],
            "gu": ["dainik", "rojnama"],
            "kn": ["dinapatrike"],
            "ml": ["dinapatram"],
            "pa": ["rozana", "dainik"],
            "ur": ["roznamah", "rozana"],
            "or": ["dainika", "pratidin"]
        }
    },
    {
        "concept": "morning",
        "category": "periodicity",
        "language_variants": {
            "en": ["morning", "mornings"],
            "hi": ["prabhat", "subah", "saver", "bhor", "bhorer"],
            "bn": ["prabhat", "bhor", "sakal"],
            "ta": ["kalai", "vidiyal"],
            "te": ["prabhatam", "udayam"],
            "mr": ["prabhat", "sakal"],
            "gu": ["prabhat", "sakal"],
            "kn": ["prabhata", "beligge"],
            "ml": ["prabhatham"],
            "pa": ["saver", "prabhat"],
            "ur": ["subah", "sahar"],
            "or": ["prabhata", "sakala"]
        }
    },
    {
        "concept": "evening",
        "category": "periodicity",
        "language_variants": {
            "en": ["evening", "evenings"],
            "hi": ["sandhya", "shaam", "sanjh"],
            "bn": ["sandhya", "sanjh"],
            "ta": ["malai", "sandhyavani"],
            "te": ["sandhya", "saayantram"],
            "mr": ["sandhya", "sanj"],
            "gu": ["sandhya", "sanj"],
            "kn": ["sanje", "sandhya"],
            "ml": ["sandhya"],
            "pa": ["shaam", "sanjh"],
            "ur": ["shaam", "sehar"],
            "or": ["sandhya", "sanjha"]
        }
    },
    {
        "concept": "weekly",
        "category": "periodicity",
        "language_variants": {
            "en": ["weekly", "weeklies"],
            "hi": ["saptahik", "hafta", "haftawar"],
            "bn": ["saptahik"],
            "ta": ["varam", "vaaram"],
            "te": ["vaaram", "varapatrika"],
            "mr": ["saptahik"],
            "gu": ["saptahik"],
            "kn": ["varapatrike"],
            "ml": ["aazhchappathippu"],
            "pa": ["haftawar", "saptahik"],
            "ur": ["haftawar", "hafta"],
            "or": ["saptahika"]
        }
    },
    {
        "concept": "monthly",
        "category": "periodicity",
        "language_variants": {
            "en": ["monthly", "monthlies"],
            "hi": ["masik", "mahina", "mahana"],
            "bn": ["masik"],
            "ta": ["matham", "maadham"],
            "te": ["maasam", "masapatrika"],
            "mr": ["masik"],
            "gu": ["masik"],
            "kn": ["masapatrike"],
            "ml": ["masika"],
            "pa": ["mahina", "masik"],
            "ur": ["mahana", "mahwar"],
            "or": ["masika"]
        }
    },

    # --- Media Nouns & Publication Terms ---
    {
        "concept": "news",
        "category": "media",
        "language_variants": {
            "en": ["news"],
            "hi": ["samachar", "khabar", "varta", "suchna", "akhbar"],
            "bn": ["samachar", "khabor", "sambad", "bartaman"],
            "ta": ["seithi", "seithigal"],
            "te": ["vartha", "varthalu", "samacharam"],
            "mr": ["batmya", "vartahar", "samachar", "khabar"],
            "gu": ["samachar", "khabar"],
            "kn": ["suddi", "varte", "samachara"],
            "ml": ["vartha", "varthakal"],
            "pa": ["khabar", "samachar", "akhbar"],
            "ur": ["khabar", "akhbar", "suchna"],
            "or": ["sambada", "samachara", "khabara"]
        }
    },
    {
        "concept": "voice",
        "category": "media",
        "language_variants": {
            "en": ["voice", "voices"],
            "hi": ["vani", "vaani", "awaaz", "shabda", "swar"],
            "bn": ["vani", "awaaz", "swara", "dhwani"],
            "ta": ["kural", "vaani", "oli"],
            "te": ["vaani", "swaram", "sabdam", "ravam"],
            "mr": ["awaaz", "vani", "swar"],
            "gu": ["awaaz", "vani", "sur"],
            "kn": ["dhwani", "vani", "swara"],
            "ml": ["shabdam", "dhwani", "vani"],
            "pa": ["awaaz", "boli"],
            "ur": ["awaaz", "sada"],
            "or": ["dhwani", "swara", "swar"]
        }
    },
    {
        "concept": "times",
        "category": "media",
        "language_variants": {
            "en": ["times", "time"],
            "hi": ["samay", "kaal", "yug", "waqt"],
            "bn": ["samay", "kaal", "yug"],
            "ta": ["neram", "kalam"],
            "te": ["samayam", "kaalam"],
            "mr": ["vel", "kaal", "samay"],
            "gu": ["samay", "kaal"],
            "kn": ["samaya", "kala"],
            "ml": ["samayam", "kaalam"],
            "pa": ["waqt", "samay"],
            "ur": ["waqt", "zamanah", "asr"],
            "or": ["samaya", "kala"]
        }
    },
    {
        "concept": "herald",
        "category": "media",
        "language_variants": {
            "en": ["herald", "courier", "messenger"],
            "hi": ["doot", "sandeshvahak"],
            "bn": ["doot", "barta"],
            "ta": ["murasu", "murasam", "thoodhu"],
            "te": ["dhootha", "sandeshahari"],
            "mr": ["doot", "sandeshvahak"],
            "gu": ["doot", "sandeshvahak"],
            "kn": ["dootha"],
            "ml": ["dhoothan"],
            "pa": ["doot"],
            "ur": ["qasid", "paighambar"],
            "or": ["duta"]
        }
    },
    {
        "concept": "post",
        "category": "media",
        "language_variants": {
            "en": ["post", "posts", "mail", "letter"],
            "hi": ["dak", "patra", "chithi"],
            "bn": ["dak", "patra", "chithi"],
            "ta": ["thabal", "anjal"],
            "te": ["dhaaka", "utharam"],
            "mr": ["dak", "patra"],
            "gu": ["dak", "patra"],
            "kn": ["anche", "patra"],
            "ml": ["thapal"],
            "pa": ["dak", "chithi"],
            "ur": ["daak", "khat"],
            "or": ["daka", "patra"]
        }
    },
    {
        "concept": "journal",
        "category": "media",
        "language_variants": {
            "en": ["journal", "journals", "magazine", "magazines", "periodical", "bulletin"],
            "hi": ["patrika", "patrikayen", "darshika", "sangrah"],
            "bn": ["patrika"],
            "ta": ["ithazh", "patrikai"],
            "te": ["patrika"],
            "mr": ["patrika", "niyatkalik"],
            "gu": ["patrika"],
            "kn": ["patrike"],
            "ml": ["pathram", "masika"],
            "pa": ["patrika"],
            "ur": ["jaridah", "risala"],
            "or": ["patrika"]
        }
    },
    {
        "concept": "science",
        "category": "domain",
        "language_variants": {
            "en": ["science", "scientific"],
            "hi": ["vigyan", "shastra", "vidya"],
            "bn": ["bigyan"],
            "ta": ["ariviyal"],
            "te": ["vignanam", "shastram"],
            "mr": ["vidnyan", "shastra"],
            "gu": ["vigyan"],
            "kn": ["vijnana", "shastra"],
            "ml": ["shasthram"],
            "pa": ["vigyan"],
            "ur": ["science"],
            "or": ["bijnana"]
        }
    },
    {
        "concept": "mirror",
        "category": "media",
        "language_variants": {
            "en": ["mirror", "mirrors"],
            "hi": ["darpan", "aaina", "sheesha"],
            "bn": ["darpan", "aaina"],
            "ta": ["kannadi"],
            "te": ["darpana", "addamu"],
            "mr": ["aarasa", "darpan"],
            "gu": ["aaino", "darpan"],
            "kn": ["kannadi", "darpana"],
            "ml": ["kannadi"],
            "pa": ["sheesha", "darpan"],
            "ur": ["aaina", "sheesha"],
            "or": ["darpana"]
        }
    },
    {
        "concept": "chronicle",
        "category": "media",
        "language_variants": {
            "en": ["chronicle", "chronicles"],
            "hi": ["itihaas", "vrittant", "katha", "vrittanta"],
            "bn": ["itihaas", "brittanta"],
            "ta": ["varalaru"],
            "te": ["charithra", "vrithantham"],
            "mr": ["itihaas", "vruttanta"],
            "gu": ["itihaas", "vruttanta"],
            "kn": ["ithihasa", "vritthantha"],
            "ml": ["charithram"],
            "pa": ["itihaas"],
            "ur": ["tareekh"],
            "or": ["itihasa"]
        }
    },

    # --- Societal & Philosophical Concepts ---
    {
        "concept": "people",
        "category": "society",
        "language_variants": {
            "en": ["people", "peoples", "public", "masses"],
            "hi": ["jan", "lok", "janta", "praja", "awam"],
            "bn": ["jan", "lok", "janta", "gonobani", "gono"],
            "ta": ["makkal", "janam"],
            "te": ["praja", "janam", "lokam"],
            "mr": ["lok", "janata", "praja"],
            "gu": ["lok", "janta", "praja"],
            "kn": ["jana", "praje", "janate"],
            "ml": ["janam", "janangal", "praja"],
            "pa": ["lok", "janta", "awam"],
            "ur": ["awam", "khalq"],
            "or": ["jana", "loka", "praja"]
        }
    },
    {
        "concept": "nation",
        "category": "society",
        "language_variants": {
            "en": ["nation"],
            "hi": ["rashtra", "desh", "watan"],
            "bn": ["rashtra", "desh"],
            "ta": ["thesam", "naadu"],
            "te": ["desham", "rashtramu"],
            "mr": ["rashtra", "desh"],
            "gu": ["rashtra", "desh"],
            "kn": ["rashtra", "desha"],
            "ml": ["rajyam", "desham"],
            "pa": ["watan", "desh", "rashtra"],
            "ur": ["watan", "qaum"],
            "or": ["rastra", "desa"]
        }
    },
    {
        "concept": "national",
        "category": "society",
        "language_variants": {
            "en": ["national"],
            "hi": ["rashtriya", "deshi", "qaumi"],
            "bn": ["rashtriya", "jatiya"],
            "ta": ["thesiya"],
            "te": ["jaathiya", "rashtriya"],
            "mr": ["rashtriya"],
            "gu": ["rashtriya"],
            "kn": ["rashtriya"],
            "ml": ["theshiya"],
            "pa": ["qaumi", "rashtriya"],
            "ur": ["qaumi"],
            "or": ["jativa", "rastriya"]
        }
    },
    {
        "concept": "world",
        "category": "society",
        "language_variants": {
            "en": ["world", "globe", "earth"],
            "hi": ["sansar", "duniya", "jagat", "vishwa", "srishti"],
            "bn": ["sansar", "duniya", "jagat", "bishwo"],
            "ta": ["ulagam", "prapancham"],
            "te": ["prapancham", "lokam", "viswam"],
            "mr": ["jagat", "duniya", "vishwa"],
            "gu": ["duniya", "jagat", "vishwa"],
            "kn": ["jagat", "prapancha", "vishwa"],
            "ml": ["lokam", "prapancham"],
            "pa": ["duniya", "jahan", "sansar"],
            "ur": ["duniya", "jahan", "alam"],
            "or": ["sansara", "jagat", "biswa"]
        }
    },
    {
        "concept": "truth",
        "category": "society",
        "language_variants": {
            "en": ["truth"],
            "hi": ["satya", "sach", "haq"],
            "bn": ["satya", "shotti"],
            "ta": ["unmai", "sathyam"],
            "te": ["nijam", "sathyam"],
            "mr": ["khare", "satya"],
            "gu": ["saachu", "satya"],
            "kn": ["sathya", "nija"],
            "ml": ["sathyam"],
            "pa": ["sach", "sat"],
            "ur": ["sach", "haq", "sadaqat"],
            "or": ["satya", "sata"]
        }
    },
    {
        "concept": "light",
        "category": "nature",
        "language_variants": {
            "en": ["light", "ray", "glow"],
            "hi": ["jyoti", "prakash", "deep", "deepak", "ujala", "roshni", "kiran"],
            "bn": ["jyoti", "alo", "prakash", "deep", "kiran"],
            "ta": ["velicham", "oli", "theepam", "kiran"],
            "te": ["velugu", "prakaasam", "deepam", "jyothi"],
            "mr": ["prakash", "ujed", "jyoti", "deep"],
            "gu": ["prakash", "ujash", "jyoti", "deepak"],
            "kn": ["belaku", "prakasha", "jyothi", "deepa"],
            "ml": ["velicham", "prakasham", "deepam"],
            "pa": ["roshni", "channan", "jyoti", "prakash"],
            "ur": ["roshni", "noor", "ujala", "kiran"],
            "or": ["aloka", "jyoti", "dipaka"]
        }
    },
    {
        "concept": "sun",
        "category": "nature",
        "language_variants": {
            "en": ["sun", "solar"],
            "hi": ["surya", "ravi", "bhaskar", "dinkar", "aditya", "bhanu"],
            "bn": ["surya", "robi", "bhaskar", "aditya"],
            "ta": ["suriyan", "kathiravan", "aadirai", "dinamani"],
            "te": ["suryudu", "ravi", "bhanudu", "bhaskara"],
            "mr": ["surya", "ravi", "bhaskar"],
            "gu": ["surya", "ravi", "bhaskar"],
            "kn": ["surya", "ravi", "bhaskara"],
            "ml": ["suryan", "ravi", "bhanu"],
            "pa": ["suraj", "ravi"],
            "ur": ["suraj", "shams", "khursheed"],
            "or": ["surya", "rabi", "bhaskara"]
        }
    },
    {
        "concept": "moon",
        "category": "nature",
        "language_variants": {
            "en": ["moon", "lunar"],
            "hi": ["chandra", "chand", "shashi", "soma", "indu", "himanshu"],
            "bn": ["chandra", "chand", "shoshi", "shashi"],
            "ta": ["chandran", "nilavu", "thingal"],
            "te": ["chandrudu", "chandamama", "sasi"],
            "mr": ["chandra", "chand"],
            "gu": ["chandra", "chand"],
            "kn": ["chandra", "tingalu"],
            "ml": ["chandran", "thingal"],
            "pa": ["chann", "chand"],
            "ur": ["chand", "qamar", "hilal"],
            "or": ["chandra", "jahn"]
        }
    },
    {
        "concept": "revolution",
        "category": "society",
        "language_variants": {
            "en": ["revolution"],
            "hi": ["kranti", "inquilab"],
            "bn": ["kranti", "biplob"],
            "ta": ["puratchi"],
            "te": ["viplavam"],
            "mr": ["kranti"],
            "gu": ["kranti"],
            "kn": ["kranthi"],
            "ml": ["viplavam"],
            "pa": ["inquilab", "kranti"],
            "ur": ["inquilab"],
            "or": ["kranti", "biplaba"]
        }
    },
    {
        "concept": "victory",
        "category": "society",
        "language_variants": {
            "en": ["victory", "triumph", "win"],
            "hi": ["vijay", "jeet", "jay", "fatah"],
            "bn": ["bijoy", "joy", "jeet"],
            "ta": ["vetri", "jayam"],
            "te": ["vijayam", "gelupu", "jayam"],
            "mr": ["vijay", "jit", "jay"],
            "gu": ["vijay", "jit", "jay"],
            "kn": ["vijaya", "gelluvu", "jaya"],
            "ml": ["vijayam", "jayam"],
            "pa": ["jeet", "vijay", "fateh"],
            "ur": ["fatah", "jeet", "kamrani"],
            "or": ["bijaya", "jaya"]
        }
    },
    {
        "concept": "peace",
        "category": "society",
        "language_variants": {
            "en": ["peace", "harmony"],
            "hi": ["shanti", "aman", "sukoon", "chain"],
            "bn": ["shanti", "aman"],
            "ta": ["amaithi"],
            "te": ["shanthi"],
            "mr": ["shanti", "aman"],
            "gu": ["shanti", "aman"],
            "kn": ["shanthi"],
            "ml": ["samadhanam", "shanthi"],
            "pa": ["aman", "shanti"],
            "ur": ["aman", "sukoon", "salaam"],
            "or": ["shanti"]
        }
    },
    {
        "concept": "new",
        "category": "modifier",
        "language_variants": {
            "en": ["new", "novel", "modern"],
            "hi": ["naya", "nayi", "nav", "nava", "navin", "adhunik"],
            "bn": ["notun", "nobo", "nava", "kotha"],
            "ta": ["puthiya", "pudhu", "nava"],
            "te": ["kottha", "nava", "nuthana"],
            "mr": ["naveen", "nava", "naya"],
            "gu": ["navu", "nava", "naya"],
            "kn": ["hosa", "nava", "nuthana"],
            "ml": ["puthiya", "nava"],
            "pa": ["nawan", "nava", "naya"],
            "ur": ["naya", "jadeed"],
            "or": ["nua", "naba", "nutana"]
        }
    }
]

# Build fast compiled lookup tables
WORD_TO_CONCEPT: Dict[str, str] = {}
CONCEPT_TO_WORDS: Dict[str, Set[str]] = {}
WORD_TO_LANG: Dict[str, str] = {}

for item in CONCEPT_REGISTRY:
    concept_id = item["concept"].lower()
    all_words: Set[str] = set()
    for lang, words in item["language_variants"].items():
        for w in words:
            w_clean = w.lower().strip()
            if w_clean:
                WORD_TO_CONCEPT[w_clean] = concept_id
                WORD_TO_LANG[w_clean] = lang
                all_words.add(w_clean)
    CONCEPT_TO_WORDS[concept_id] = all_words

# Flat dictionary compatible with legacy lexicon
CROSS_LINGUAL_LEXICON: Dict[str, Set[str]] = {}
for item in CONCEPT_REGISTRY:
    c = item["concept"]
    variants = CONCEPT_TO_WORDS.get(c, set())
    CROSS_LINGUAL_LEXICON[c] = variants

INDIAN_TO_ENGLISH: Dict[str, Set[str]] = {}
for w, c in WORD_TO_CONCEPT.items():
    INDIAN_TO_ENGLISH.setdefault(w, set()).add(c)
