"""
Indian Dance API
================
A small Flask REST API that serves the classical + folk/tribal dance
dataset and exposes search over it. The Gradio app in
dance_search_app.py calls this API instead of holding the data itself.

Run:
    pip install flask
    python dance_api.py

Runs on http://127.0.0.1:5000 by default.

Endpoints:
    GET /api/health
    GET /api/classical                 -> list all classical dances
    GET /api/folk                      -> list all folk/tribal dances
    GET /api/states                    -> list all state names
    GET /api/dance/<name>              -> lookup one dance by exact name
    GET /api/state/<name>              -> lookup one state by exact name
    GET /api/search?q=<query>          -> unified search (dance OR state OR suggestions)
"""

from flask import Flask, jsonify, request

import re
import random

import db_logger

app = Flask(__name__)

# ---------------------------------------------------------------------------
# 1. DATA
# ---------------------------------------------------------------------------

CLASSICAL_DANCES = [
    ("Bharatanatyam", "Tamil Nadu"),
    ("Kathak", "Uttar Pradesh"),
    ("Kathakali", "Kerala"),
    ("Kuchipudi", "Andhra Pradesh"),
    ("Odissi", "Odisha"),
    ("Manipuri", "Manipur"),
    ("Mohiniyattam", "Kerala"),
    ("Sattriya", "Assam"),
]

RAW_FOLK_DATA = """
North India
Rouff (Rouf, Rauf) – Kashmir Valley – Jammu & Kashmir
Dumhal (Dumhal Dance) – Kashmir – Jammu & Kashmir
Kud (Kudd) – Jammu region – Jammu & Kashmir
Bacha Nagma (Bacha Nagma Dance) – Kashmir – Jammu & Kashmir
Hafiza (Hafiza Dance) – Kashmir – Jammu & Kashmir
Bhand Pather (Bhand Pathar, Bhand Pather) – Kashmir – Jammu & Kashmir
Cham (Chaam, Chham) – Ladakh – Ladakh
Shondol (Shondol Dance, Shondal) – Ladakh – Ladakh
Jabro (Jabro Dance) – Changthang – Ladakh
Losar Dance (Losar, Losar Chham) – Ladakh – Ladakh
Nati (Natti, Nati Dance) – Himachal Pradesh – Himachal Pradesh
Kinnauri Nati (Kinnauri Natti) – Kinnaur – Himachal Pradesh
Chham (Chham Dance, Chham) – Lahaul-Spiti – Himachal Pradesh
Dangi (Dangi Dance) – Chamba – Himachal Pradesh
Kayang (Kayan, Kayang Dance) – Kinnaur – Himachal Pradesh
Thoda (Thoda Dance) – Himachal Pradesh – Himachal Pradesh
Bhangra (Bhangra Dance) – Punjab – Punjab
Giddha (Gidda, Giddha Dance) – Punjab – Punjab
Sammi (Sammi Dance, Sami) – Punjab – Punjab
Luddi (Luddi Dance, Luddi) – Punjab – Punjab
Jhumar (Jhoomar, Jhumair) – Punjab – Punjab
Dhamal (Dhamal Dance) – Punjab – Haryana
Kikli (Kiklee, Kikli Dance) – Punjab – Punjab
Khoria (Khoria Dance, Khoria Nritya) – Haryana – Haryana
Phag (Phag Dance) – Haryana – Haryana
Loor (Loor Dance) – Haryana – Haryana
Daph (Daph Dance) – Haryana – Haryana
Saang (Swang, Swaang, Saang) – Haryana – Haryana
Chholiya (Chholia, Chholiya Nritya, Chhaliya) – Kumaon – Uttarakhand
Jhora (Jhora Dance, Jhoda) – Kumaon – Uttarakhand
Chanchari (Chanchari Dance) – Kumaon – Uttarakhand
Langvir Nritya (Lang Veer Dance, Langvir Dance) – Garhwal – Uttarakhand
Pandav Nritya (Pandav Nritya, Pandava Dance) – Garhwal – Uttarakhand
Barada Nati (Barada Natti) – Jaunsar-Bawar – Uttarakhand
Raslila (Ras Leela, Rasa Lila, Raslila) – Braj – Uttar Pradesh
Charkula (Charkula Dance) – Braj – Uttar Pradesh
Rai (Rai Dance, Rai Nritya) – Bundelkhand – Uttar Pradesh
Kajri (Kajari, Kajri Dance) – Purvanchal – Uttar Pradesh
Nautanki (Nautanki Theatre, Nautanki) – Uttar Pradesh – Uttar Pradesh
Dadra (Dadra Dance) – Uttar Pradesh – Uttar Pradesh
Western & Central India
Ghoomar (Ghumar, Ghoommar, Ghoomar Dance) – Rajasthan – Rajasthan
Kalbelia (Kalbeliya, Kalbelia Dance) – Kalbelia community – Rajasthan
Bhavai (Bhavai Dance) – Rajasthan – Rajasthan
Chari (Chari Dance) – Kishangarh/Ajmer – Rajasthan
Gair (Gher, Gair Dance, Geer) – Rajasthan – Rajasthan
Kachhi Ghodi (Kachhi Ghodi Dance, Kachhi Ghori) – Shekhawati – Rajasthan
Terah Taali (Tera Tali, Terah Taal, Tera Taali) – Kamad community – Rajasthan
Gavari (Gawari, Gavri, Gavari Dance) – Bhil tribe – Rajasthan
Garba (Garbo, Garba Dance) – Gujarat – Gujarat
Dandiya Raas (Dandiya Ras, Dandiya, Raas Dandiya) – Gujarat – Gujarat
Raas (Ras, Raas Dance) – Saurashtra – Gujarat
Tippani (Tippani Dance, Tippani Nritya) – Saurashtra – Gujarat
Padhar (Padhar Dance) – Padhar community – Gujarat
Hudo (Hudo Dance) – Saurashtra – Gujarat
Lavani (Lavani Dance) – Maharashtra – Maharashtra
Koli (Koli Dance, Koli Nritya) – Coastal Maharashtra – Maharashtra
Lezim (Lezium, Lezim Dance, Lazim) – Maharashtra – Maharashtra
Tamasha (Tamasha Dance, Tamasha Theatre) – Maharashtra – Maharashtra
Dhangari Gaja (Dhangari Gaja Dance, Dhangari Gaja) – Dhangar community – Maharashtra
Gondhal (Gondhal Dance) – Maharashtra – Maharashtra
Powada (Powada Dance, Powada Performance) – Maharashtra – Maharashtra
Dindi (Dindi Dance) – Maharashtra – Maharashtra
Fugdi (Fugadi, Fugdi Dance) – Goa – Goa
Dhalo (Dhalon, Dhalo Dance) – Goa – Goa
Dekhnni (Dekhni, Dekhnni Dance) – Goa – Goa
Kunbi Dance (Kunbi Nritya) – Kunbi community – Goa
Ghode Modni (Ghode Modni Dance, Ghode Modni) – Goa – Goa
Matki (Matki Dance) – Malwa – Madhya Pradesh
Rai (Rai Nritya, Rai Dance) – Bundelkhand – Madhya Pradesh
Jawara (Jawara Dance) – Madhya Pradesh – Madhya Pradesh
Tertali (Tertali Dance, Teratali) – Kamar community – Madhya Pradesh
Grida (Grida Dance) – Madhya Pradesh – Madhya Pradesh
Bhagoria (Bhagoriya, Bhagoria Dance) – Bhil/Bhilala tribes – Madhya Pradesh
Gaur (Gaur Dance, Gaur Nritya) – Gond tribe – Madhya Pradesh
Saila (Saila Dance, Saila Nritya) – Tribal communities – Madhya Pradesh
Karma (Karma Dance, Karam Dance) – Tribal communities – Madhya Pradesh
Panthi (Panthi Dance, Panthi Nritya) – Satnami community – Chhattisgarh
Raut Nacha (Raut Nacha, Raut Naacha, Raut Nritya) – Yadav community – Chhattisgarh
Sua Nacha (Sua Dance, Suwa Nacha, Suwa Nritya) – Chhattisgarh – Chhattisgarh
Karma (Karma Nacha, Karam Dance) – Tribal communities – Chhattisgarh
Saila (Saila Nacha, Saila Nritya) – Tribal communities – Chhattisgarh
Gaur Maria (Gaur Maria Dance, Gaur-Maria) – Maria tribe – Chhattisgarh
Gendi (Gendi Dance, Gendi Nritya) – Chhattisgarh – Chhattisgarh
Danda Nacha (Danda Naacha, Danda Nritya) – Chhattisgarh – Chhattisgarh
Eastern India
Jat-Jatin (Jat Jatin, Jat-Jatin Dance) – Mithila – Bihar
Jhijhiya (Jhijia, Jhinjhiya, Jhijhiya Dance) – Mithila – Bihar
Sama Chakeva (Sama-Chakeva, Sama Chakeva Dance) – Mithila – Bihar
Bidesia (Bidesiya, Bidesia Dance) – Bhojpur – Bihar
Kajari (Kajri, Kajari Dance) – Bihar – Bihar
Jhumar (Jhoomar, Jhumair) – Bihar – Bihar
Domkach (Domkach Dance, Domkach Nritya) – Bihar – Bihar
Chhau (Chhau Dance, Chhaau) – Seraikella – Jharkhand
Jhumair (Jhumair, Jhumar) – Jharkhand – Jharkhand
Karma (Karam, Karma Dance) – Tribal communities – Jharkhand
Sarhul (Sarhul Dance) – Tribal communities – Jharkhand
Paika (Paika Dance, Paika Nritya) – Tribal communities – Jharkhand
Sohrai (Sohrai Dance) – Tribal communities – Jharkhand
Santhali Dance (Santali Dance, Santal Dance) – Santhal tribe – Jharkhand
Munda Dance (Munda Nritya) – Munda tribe – Jharkhand
Chhau (Chhau Dance, Purulia Chhau) – Purulia – West Bengal
Gambhira (Gambhira Dance, Gambhira Nritya) – Malda – West Bengal
Jhumur (Jhumur Dance, Jhumur Nritya) – Western Bengal – West Bengal
Tusu (Tusu Parab Dance, Tusu) – Rarh region – West Bengal
Santhali Dance (Santali Dance, Santal Dance) – Santhal community – West Bengal
Gajan (Gajan Dance) – West Bengal – West Bengal
Alkap (Alkap Dance, Alkap Folk Theatre) – Murshidabad/Malda – West Bengal
Dhunuchi Dance (Dhunuchi Naach, Dhunuchi Nritya) – Bengal – West Bengal
Chhau (Mayurbhanj Chhau, Chhau Dance) – Mayurbhanj – Odisha
Dalkhai (Dalkhai Dance, Dalkhai Nritya) – Western Odisha – Odisha
Ghumura (Ghumra, Ghumura Dance, Ghumura Nritya) – Kalahandi – Odisha
Gotipua (Gotipua Dance, Gotipua Nritya) – Puri – Odisha
Sambalpuri Dance (Sambalpuri Nritya) – Sambalpur/Western Odisha – Odisha
Karma (Karma Dance, Karam Dance) – Tribal regions – Odisha
Medha Nacha (Medha Naacha, Medha Dance) – Odisha – Odisha
South India
Dhimsa (Dhimsa Dance, Dhimsa Nritya) – Tribal areas – Andhra Pradesh
Kolattam (Kolata, Kolatam, Kolattam Dance) – Andhra Pradesh – Andhra Pradesh
Veeranatyam (Veera Natyam, Veeranatyam Dance) – Andhra Pradesh – Andhra Pradesh
Butta Bommalu (Butta Bommalata, Butta Bommalu Dance) – West Godavari – Andhra Pradesh
Lambadi (Lambani, Banjara Dance, Lambadi Dance) – Lambadi community – Andhra Pradesh
Dappu (Dappu Dance, Dappu Nritya) – Andhra Pradesh – Andhra Pradesh
Tappeta Gullu (Tappeta Gullu Dance, Tappeta Gullu) – Andhra Pradesh – Andhra Pradesh
Perini Shivatandavam (Perini Sivatandavam, Perini Shivathandavam, Perini Dance) – Telangana – Telangana
Bathukamma Dance (Bathukamma Nritya) – Telangana – Telangana
Lambadi (Lambani, Banjara Dance) – Lambadi community – Telangana
Dappu (Dappu Dance) – Telangana – Telangana
Gusadi (Gussadi, Gusadi Dance) – Raj Gond tribe – Telangana
Oggu Katha (Oggukatha, Oggu Katha) – Telangana – Telangana
Bonalu Dance (Bonalu Nritya) – Telangana – Telangana
Yakshagana (Yakshagana Dance, Yakshagana Bayalata) – Coastal Karnataka – Karnataka
Dollu Kunitha (Dollu Kunita, Dollu Kunitha Dance) – Karnataka – Karnataka
Kamsale (Kamsale Dance, Kamsale Nritya) – Karnataka – Karnataka
Veeragase (Veeragase Dance, Veeragase Nritya) – Karnataka – Karnataka
Kolata (Kolata Dance, Kolattam) – Karnataka – Karnataka
Hulivesha (Huli Vesha, Hulivesha Dance) – Coastal Karnataka – Karnataka
Bhootha Aradhane (Bhoota Aradhana, Bhuta Kola tradition) – Coastal Karnataka – Karnataka
Puja Kunitha (Pooja Kunitha, Puja Kunita) – Karnataka – Karnataka
Theyyam (Teyyam, Theyyam Dance) – North Malabar – Kerala
Thiruvathirakali (Thiruvathira Kali, Thiruvathirakali) – Kerala – Kerala
Oppana (Oppana Dance) – Malabar – Kerala
Kaikottikali (Kaikottikali, Kaikottikkali) – Kerala – Kerala
Ottan Thullal (Ottanthullal, Ottan Thullal) – Kerala – Kerala
Kummattikali (Kummatti Kali, Kummattikali) – Kerala – Kerala
Pulikali (Pulikkali, Pulikali Dance) – Thrissur – Kerala
Margamkali (Margam Kali, Margamkali Dance) – Kerala – Kerala
Kolkkali (Kolkali, Kolkkali Dance) – Malabar – Kerala
Karagattam (Karagattam, Karagattam Dance, Karagam) – Tamil Nadu – Tamil Nadu
Kummi (Kummi Dance, Kummi Attam) – Tamil Nadu – Tamil Nadu
Kolattam (Kolattam, Kolattam Dance) – Tamil Nadu – Tamil Nadu
Kavadi Attam (Kavadi Aattam, Kavadi Dance) – Tamil Nadu – Tamil Nadu
Oyilattam (Oyil Attam, Oyilattam Dance) – Tamil Nadu – Tamil Nadu
Devarattam (Devaraattam, Devarattam Dance) – Madurai region – Tamil Nadu
Poikkal Kuthirai (Poikkal Kuthirai Attam, Poikkal Kuthirai) – Tamil Nadu – Tamil Nadu
Therukoothu (Theru Koothu, Terukuttu, Therukoothu) – Northern Tamil Nadu – Tamil Nadu
Mayilattam (Mayil Attam, Mayilattam Dance) – Tamil Nadu – Tamil Nadu
Parai Attam (Parai Aattam, Parai Dance) – Tamil Nadu – Tamil Nadu
Puliyattam (Puli Attam, Puliyattam Dance) – Tamil Nadu – Tamil Nadu
Northeast India
Bihu (Bihu Dance, Bihu Naas) – Assam – Assam
Bagurumba (Bagurumba Dance, Bagurumba Nritya) – Bodo community – Assam
Bhortal (Bhortal Nritya, Bhortal Dance) – Assam – Assam
Deodhani (Deodhani Dance, Deo-Dhani) – Assam – Assam
Jhumur (Jhumur Dance) – Tea-tribe communities – Assam
Gumrag (Gumrag Dance) – Mising community – Assam
Ali-Aye-Ligang (Ali-Ai-Ligang, Ali-Aye-Ligang Dance) – Mising community – Assam
Ojapali (Oja-Pali, Ojapali Dance) – Assam – Assam
Huchori (Husori, Huchori Dance) – Assam – Assam
Lai Haraoba (Lai Haroba, Lai-Haraoba) – Meitei community – Manipur
Thang-Ta (Thang Ta, Thang-Ta Martial Art) – Manipur – Manipur
Pung Cholom (Pung Cholom, Pung Cholom Dance) – Manipur – Manipur
Khamba Thoibi (Khamba-Thoibi, Khamba Thoibi Dance) – Meitei community – Manipur
Maibi Dance (Maibi, Maibi Jagoi) – Meitei community – Manipur
Nupa Pala (Nupa Pala, Nupa Pala Dance) – Manipur – Manipur
Wangala (Wangala Dance, Wangala Festival Dance) – Garo tribe – Meghalaya
Nongkrem (Nongkrem Dance, Nongkrem Dance Festival) – Khasi tribe – Meghalaya
Shad Suk Mynsiem (Shad Suk Mynsiem Dance) – Khasi tribe – Meghalaya
Laho (Laho Dance) – Meghalaya – Meghalaya
Behdienkhlam (Behdienkhlam Dance) – Jaintia tribe – Meghalaya
Chang Lo (Changlo, Chang Lo Dance) – Chang tribe – Nagaland
War Dance (War Dance of Nagas, Naga War Dance) – Naga tribes – Nagaland
Zeliang Dance (Zeliangrong Dance) – Zeliang tribe – Nagaland
Konyak Dance (Konyak Warrior Dance) – Konyak tribe – Nagaland
Sumi Dance (Sumi Naga Dance) – Sumi tribe – Nagaland
Cheraw (Cheraw Dance, Bamboo Dance, Mizo Bamboo Dance) – Mizo community – Mizoram
Khuallam (Khuallam Dance, Khuallam Dance) – Mizo community – Mizoram
Chheih Lam (Chheihlam, Chheih Lam Dance) – Mizo community – Mizoram
Sarlamkai (Sarlam Kai, Sarlamkai Dance) – Mizo community – Mizoram
Chailam (Chai Lam, Chailam Dance) – Mizo community – Mizoram
Hojagiri (Hojagiri Dance, Hojagiri Nritya) – Reang/Bru tribe – Tripura
Garia (Garia Dance, Garia Nritya) – Tripuri community – Tripura
Lebang Boomani (Lebang Bumani, Lebang Boomani Dance) – Tripuri community – Tripura
Mamita (Mamita Dance) – Tripura – Tripura
Mosak Sulmani (Mosak Sulmani Dance) – Tripura – Tripura
Ponung (Ponung Dance, Ponung Nritya) – Adi tribe – Arunachal Pradesh
Popir (Popir Dance, Popir Nritya) – Galo tribe – Arunachal Pradesh
Bardo Chham (Bardo Cham, Bardo Chham Dance) – Monpa community – Arunachal Pradesh
Aji Lhamu (Aji Lhamu Dance, Ajilhamu) – Monpa community – Arunachal Pradesh
Yak Dance (Yak Chham, Yak Cham) – Arunachal Pradesh – Arunachal Pradesh
Chalo Dance (Chalo, Chalo Loku Dance) – Nocte tribe – Arunachal Pradesh
Singhi Chham (Singhi Cham, Singhi Chham Dance, Snow Lion Dance) – Bhutia community – Sikkim
Maruni (Maruni Dance, Maruni Nach) – Nepali community – Sikkim
Tamang Selo (Tamang Selo Dance) – Tamang community – Sikkim
Yak Chham (Yak Cham, Yak Dance) – Sikkim – Sikkim
Chu Faat (Chu Faat Dance) – Lepcha community – Sikkim
Kagyed Dance (Kagyed, Kagyed Chham) – Buddhist tradition – Sikkim
"""


def parse_folk_data(raw: str):
    """
    Parses 'Dance (Alias1, Alias2) – Region – State' lines.
    The parenthesized aliases are optional — plain 'Dance – Region – State'
    lines still work fine.
    """
    records = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line or " – " not in line:
            continue
        parts = [p.strip() for p in line.split(" – ")]
        if len(parts) != 3:
            continue
        name_part, region, state = parts

        alias_match = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", name_part)
        if alias_match:
            dance = alias_match.group(1).strip()
            aliases = [a.strip() for a in alias_match.group(2).split(",") if a.strip()]
        else:
            dance = name_part
            aliases = []

        records.append({"dance": dance, "aliases": aliases, "region": region, "state": state})
    return records


FOLK_DANCES = parse_folk_data(RAW_FOLK_DATA)

# Flat list of every searchable name variant (primary + aliases) -> its record.
# Lets "Rauf" find the same record as "Rouff".
FOLK_NAME_VARIANTS = []
for _r in FOLK_DANCES:
    FOLK_NAME_VARIANTS.append((_r["dance"].lower(), _r))
    for _alias in _r["aliases"]:
        FOLK_NAME_VARIANTS.append((_alias.lower(), _r))


def is_tribal_region(region: str) -> bool:
    """
    An entry counts as TRIBAL only if its region text explicitly says
    'tribe' or 'tribal' (e.g. 'Bhil tribe', 'Tribal communities').
    '...community' entries are NOT treated as tribal just for saying
    'community' — per instruction, community labels alone don't count.
    """
    r = region.lower()
    return "tribe" in r or "tribal" in r


def is_community_region(region: str) -> bool:
    """An entry counts as COMMUNITY if its region text says 'community'."""
    return "community" in region.lower()


# Three mutually exclusive pools: Tribal, Community, and plain Folk
# (plain Folk = neither tribe/tribal NOR community in the region text).
TRIBAL_DANCES = [r for r in FOLK_DANCES if is_tribal_region(r["region"])]
COMMUNITY_DANCES = [
    r for r in FOLK_DANCES if is_community_region(r["region"]) and not is_tribal_region(r["region"])
]
PURE_FOLK_DANCES = [
    r for r in FOLK_DANCES if not is_tribal_region(r["region"]) and not is_community_region(r["region"])
]

CLASSICAL_BY_DANCE = {d.lower(): s for d, s in CLASSICAL_DANCES}
CLASSICAL_BY_STATE = {}
for d, s in CLASSICAL_DANCES:
    CLASSICAL_BY_STATE.setdefault(s.lower(), []).append(d)

ALL_STATES = sorted(set([s for _, s in CLASSICAL_DANCES] + [r["state"] for r in FOLK_DANCES]))


# ---------------------------------------------------------------------------
# 2. TYPO TOLERANCE (edit distance)
# ---------------------------------------------------------------------------
# Classical dance names & state names: allow up to 4 characters of typo.
# Folk/tribal dance names (incl. aliases): allow up to 2 characters of typo.
# (Folk names get a tighter threshold since there are hundreds of them —
# a looser threshold would start matching the wrong dance.)
CLASSICAL_STATE_TYPO_LIMIT = 4
FOLK_TYPO_LIMIT = 2


def levenshtein(a: str, b: str) -> int:
    """Standard edit distance (insertions/deletions/substitutions)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev_row = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr_row = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr_row[j] = min(
                prev_row[j] + 1,      # deletion
                curr_row[j - 1] + 1,  # insertion
                prev_row[j - 1] + cost,  # substitution
            )
        prev_row = curr_row
    return prev_row[-1]


def scaled_limit(word_len: int, category_limit: int) -> int:
    """
    Scales the allowed typo distance down ONLY for very short words (3-4
    characters), where a full category limit (4, or even 2) would let a
    query match almost anything (e.g. 'xyzz' matching 'Goa'). Words of
    5+ characters keep the full category limit as originally specified.

        word length   max typos allowed
        3-4             1
        5+              category_limit (4 for classical/state, 2 for folk)
    """
    if word_len <= 4:
        return min(1, category_limit)
    return category_limit


def closest_match(query_lower: str, candidates, limit: int):
    """
    candidates: iterable of (name_lower, payload) tuples.
    Returns (payload, matched_name_lower, distance) for the closest candidate
    within the length-scaled limit, or None if nothing is close enough.
    """
    if len(query_lower) < 3:
        return None  # too short to safely fuzzy-match at all

    best = None
    best_dist = limit + 1
    for name_lower, payload in candidates:
        effective_limit = scaled_limit(min(len(query_lower), len(name_lower)), limit)
        dist = levenshtein(query_lower, name_lower)
        if dist <= effective_limit and dist < best_dist:
            best_dist = dist
            best = (payload, name_lower, dist)
    return best


# ---------------------------------------------------------------------------
# 3. "LIST ALL / SAMPLE" KEYWORD TRIGGERS
# ---------------------------------------------------------------------------
# Typing category words (in any order, with typos, with/without "and"/"&")
# triggers a themed sample instead of a normal dance/state search:
#   1 category detected  -> 6 random dances from that category
#   2-4 categories detected -> 3 random dances from EACH detected category
# Typo tolerance: "classical" uses the classical/state limit (4, length-
# scaled); "folk"/"tribal"/"community" use the folk limit (2, length-scaled)
# — same rules as everywhere else in this file.
CATEGORY_BASE_WORDS = {
    "Classical": ("classical", CLASSICAL_STATE_TYPO_LIMIT),
    "Folk": ("folk", FOLK_TYPO_LIMIT),
    "Tribal": ("tribal", FOLK_TYPO_LIMIT),
    "Community": ("community", FOLK_TYPO_LIMIT),
}
CATEGORY_STOP_WORDS = {"and", "dance", "dances", "the", "of", "all"}
CANONICAL_CATEGORY_ORDER = ["Classical", "Folk", "Tribal", "Community"]

# Pre-built sampling pools, all in the same {dance, region, state} shape.
CATEGORY_POOLS = {
    "Classical": [{"dance": d, "region": None, "state": s} for d, s in CLASSICAL_DANCES],
    "Folk": PURE_FOLK_DANCES,
    "Tribal": TRIBAL_DANCES,
    "Community": COMMUNITY_DANCES,
}


def word_matches_category(word: str, category: str) -> bool:
    base_word, limit = CATEGORY_BASE_WORDS[category]
    if word == base_word:
        return True
    if len(word) < 3:
        return False
    effective_limit = scaled_limit(min(len(word), len(base_word)), limit)
    return levenshtein(word, base_word) <= effective_limit


def analyze_query(q: str):
    """
    Splits the query into words, drops connector words, and checks each
    remaining word against all 4 category base words. Returns:
      (categories, remainder)
    - categories: detected category names in canonical order (Classical,
      Folk, Tribal, Community) — works for ANY word order/phrasing.
    - remainder: the leftover words (joined back with spaces) that did NOT
      match a category — this is tested separately as a possible state
      name, so "classical Kerala" or "folk tribal Punjab" work.
    """
    words = [w for w in re.split(r"[^a-zA-Z]+", q) if w]
    found = set()
    remainder_words = []
    for word in words:
        if word in CATEGORY_STOP_WORDS:
            continue
        matched_category = False
        for category in CANONICAL_CATEGORY_ORDER:
            if word_matches_category(word, category):
                found.add(category)
                matched_category = True
                break
        if not matched_category:
            remainder_words.append(word)
    categories = [c for c in CANONICAL_CATEGORY_ORDER if c in found]
    remainder = " ".join(remainder_words)
    return categories, remainder


def sample_pool(pool: list, n: int, category: str) -> list:
    chosen = random.sample(pool, min(n, len(pool)))
    return [
        {"dance": r["dance"], "region": r["region"], "state": r["state"], "category": category}
        for r in chosen
    ]


def categorize_region(region: str) -> str:
    if is_tribal_region(region):
        return "Tribal"
    if is_community_region(region):
        return "Community"
    return "Folk"


def sample_state_mixed(state: str, n: int = 3) -> list:
    """
    Picks up to n dances from ONE state, mixing classical + folk/tribal/
    community together. Classical dance(s) for that state come first
    (if the state has any), then the rest is filled randomly.
    """
    classical_names = CLASSICAL_BY_STATE.get(state.lower(), [])
    classical_entries = [
        {"dance": d, "region": None, "state": state, "category": "Classical"} for d in classical_names
    ][:n]

    remaining = n - len(classical_entries)
    other_entries = []
    if remaining > 0:
        other_records = [r for r in FOLK_DANCES if r["state"] == state]
        other_entries = random.sample(other_records, min(remaining, len(other_records)))
        other_entries = [
            {"dance": r["dance"], "region": r["region"], "state": r["state"], "category": categorize_region(r["region"])}
            for r in other_entries
        ]

    return classical_entries + other_entries


def normalize_connectors(q: str) -> str:
    """Turns 'and' / '&' / ',' into plain spaces so 'X and Y' and 'X Y' are handled the same way."""
    q = re.sub(r"\s*(?:,|&|\band\b)\s*", " ", q)
    return re.sub(r"\s+", " ", q).strip()


def segment_into_states(q: str) -> list:
    """
    Greedily walks the query word-by-word looking for state names — with
    or without a connector between them ("Kerala Maharashtra" and
    "Kerala and Maharashtra" both work). Tries the longest word-window
    first at each position (so multi-word states like "Tamil Nadu" match
    before falling back to single words), with typo tolerance on each
    candidate window. A window is only fuzzy-matched against state names
    with the SAME number of words — otherwise a 2-word window like
    "punjab goa" can wrongly fuzzy-match the unrelated single-word state
    "Punjab" by "deleting" the extra word within the typo budget.
    Words that don't match anything are simply skipped, so this safely
    returns 0 or 1 matches (and does nothing) for queries that aren't
    actually about multiple states — e.g. a normal 2-word dance name like
    "Kachhi Ghodi" won't false-trigger.
    """
    normalized = normalize_connectors(q)
    words = normalized.split(" ") if normalized else []
    if not words:
        return []

    states_by_word_count = {}
    for s in ALL_STATES:
        states_by_word_count.setdefault(len(s.split()), []).append(s)
    max_window = max(states_by_word_count.keys())

    result = []
    i = 0
    n = len(words)
    while i < n:
        matched = False
        for window in range(min(max_window, n - i), 0, -1):
            candidate = " ".join(words[i:i + window])
            same_length_states = states_by_word_count.get(window, [])

            exact = next((s for s in same_length_states if s.lower() == candidate), None)
            if exact:
                result.append(exact)
                i += window
                matched = True
                break

            candidates_lower = [(s.lower(), s) for s in same_length_states]
            fuzzy = closest_match(candidate, candidates_lower, CLASSICAL_STATE_TYPO_LIMIT)
            if fuzzy:
                result.append(fuzzy[0])
                i += window
                matched = True
                break
        if not matched:
            i += 1  # skip this word, it didn't match any state window

    seen = set()
    ordered = []
    for s in result:
        if s not in seen:
            seen.add(s)
            ordered.append(s)
    return ordered


# ---------------------------------------------------------------------------
# 4. SEARCH LOGIC
# ---------------------------------------------------------------------------
def do_search(query: str):
    q = query.strip().lower()
    if not q:
        return {"type": "empty"}

    # --- Category sample trigger (classical / folk / tribal / community,
    #     alone or combined in any order/phrasing, optionally scoped to
    # --- Category sample trigger (classical / folk / tribal / community,
    #     alone or combined in any order/phrasing). This is intentionally
    #     independent of state search — the two never mix. If the query
    #     contains ONLY category words (no leftover/unmatched words), it's
    #     treated as a pure category request. If there's leftover text
    #     (e.g. a state name got typed alongside a category word), we
    #     don't try to guess — that falls through to normal search below.
    categories, remainder = analyze_query(q)
    if categories and not remainder:
        if len(categories) == 1:
            cat = categories[0]
            dances = sample_pool(CATEGORY_POOLS[cat], 6, cat)
            label = cat
        else:
            dances = []
            for cat in categories:
                dances += sample_pool(CATEGORY_POOLS[cat], 3, cat)
            label = " & ".join(categories)
        return {"type": "folk_list", "label": label, "dances": dances}

    # --- Multiple states combo: e.g. "Kerala and Maharashtra" -> 3 from
    #     EACH state (classical shown first within each state's picks).
    #     A single state (no connector) is untouched and keeps the full
    #     classical+folk/tribal/community list, exactly as before. ---
    multi_states = segment_into_states(q)
    if len(multi_states) >= 2:
        dances = []
        for state in multi_states:
            dances += sample_state_mixed(state, 3)
        label = " & ".join(multi_states)
        return {"type": "folk_list", "label": label, "dances": dances}

    # --- Exact matches first ---
    if q in CLASSICAL_BY_DANCE:
        original_name = next(d for d, s in CLASSICAL_DANCES if d.lower() == q)
        return {
            "type": "dance",
            "dance": original_name,
            "category": "Classical",
            "states": [{"state": CLASSICAL_BY_DANCE[q], "region": None}],
        }

    folk_matches = [r for (variant, r) in FOLK_NAME_VARIANTS if variant == q]
    if folk_matches:
        canonical = folk_matches[0]["dance"]
        # Gather every state this (canonical) dance appears under.
        same_dance = [r for r in FOLK_DANCES if r["dance"] == canonical]
        return {
            "type": "dance",
            "dance": canonical,
            "category": "Folk / Tribal",
            "states": [{"state": r["state"], "region": r["region"]} for r in same_dance],
        }

    state_match = next((s for s in ALL_STATES if s.lower() == q), None)
    if state_match:
        return {
            "type": "state",
            "state": state_match,
            "classical": CLASSICAL_BY_STATE.get(q, []),
            "folk": [r for r in FOLK_DANCES if r["state"].lower() == q],
        }

    # --- No exact match: try typo-tolerant fuzzy matching ---
    # Check all three categories, then pick whichever candidate is actually
    # closest (fewest edits) rather than returning the first category that
    # happens to have any match within its threshold.
    classical_candidates = [(d.lower(), (d, s)) for d, s in CLASSICAL_DANCES]
    classical_fuzzy = closest_match(q, classical_candidates, CLASSICAL_STATE_TYPO_LIMIT)

    folk_fuzzy = closest_match(q, FOLK_NAME_VARIANTS, FOLK_TYPO_LIMIT)

    state_candidates = [(s.lower(), s) for s in ALL_STATES]
    state_fuzzy = closest_match(q, state_candidates, CLASSICAL_STATE_TYPO_LIMIT)

    fuzzy_options = []
    if classical_fuzzy:
        fuzzy_options.append(("classical", classical_fuzzy))
    if folk_fuzzy:
        fuzzy_options.append(("folk", folk_fuzzy))
    if state_fuzzy:
        fuzzy_options.append(("state", state_fuzzy))

    if fuzzy_options:
        # Sort by edit distance (the 3rd element of each (payload, name_lower, dist) tuple)
        fuzzy_options.sort(key=lambda opt: opt[1][2])
        best_category, (payload, _, _) = fuzzy_options[0]

        if best_category == "classical":
            d, s = payload
            return {
                "type": "dance",
                "dance": d,
                "category": "Classical",
                "states": [{"state": s, "region": None}],
            }

        if best_category == "folk":
            canonical = payload["dance"]
            same_dance = [r for r in FOLK_DANCES if r["dance"] == canonical]
            return {
                "type": "dance",
                "dance": canonical,
                "category": "Folk / Tribal",
                "states": [{"state": r["state"], "region": r["region"]} for r in same_dance],
            }

        if best_category == "state":
            matched_state = payload
            return {
                "type": "state",
                "state": matched_state,
                "classical": CLASSICAL_BY_STATE.get(matched_state.lower(), []),
                "folk": [r for r in FOLK_DANCES if r["state"].lower() == matched_state.lower()],
            }

    # --- Still nothing: fall back to substring suggestions ---
    partial_dance = [r["dance"] for r in FOLK_DANCES if q in r["dance"].lower()]
    partial_classical = [d for d, s in CLASSICAL_DANCES if q in d.lower()]
    partial_state = [s for s in ALL_STATES if q in s.lower()]
    if partial_dance or partial_classical or partial_state:
        return {
            "type": "suggestions",
            "dances": partial_classical + partial_dance,
            "states": partial_state,
        }

    return {"type": "none", "query": query}


# ---------------------------------------------------------------------------
# 3. ROUTES
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/classical")
def get_classical():
    return jsonify([{"dance": d, "state": s} for d, s in CLASSICAL_DANCES])


@app.get("/api/folk")
def get_folk():
    return jsonify(FOLK_DANCES)


@app.get("/api/states")
def get_states():
    return jsonify(ALL_STATES)


@app.get("/api/dance/<name>")
def get_dance(name):
    result = do_search(name)
    if result["type"] != "dance":
        return jsonify({"error": f"No dance found matching '{name}'"}), 404
    return jsonify(result)


@app.get("/api/state/<name>")
def get_state(name):
    result = do_search(name)
    if result["type"] != "state":
        return jsonify({"error": f"No state found matching '{name}'"}), 404
    return jsonify(result)


def corrected_query_text(original_query: str, result: dict) -> str:
    """
    Returns the CORRECTED spelling to log, based on what actually matched
    (typo-fixed dance/state name), falling back to the original text the
    user typed if nothing matched (e.g. 'none' or 'suggestions' results).
    """
    if result.get("type") == "dance":
        return result.get("dance", original_query)
    if result.get("type") == "state":
        return result.get("state", original_query)
    return original_query


@app.get("/api/search")
def search():
    q = request.args.get("q", "")
    result = do_search(q)
    db_logger.log_search(corrected_query_text(q, result), result)
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)