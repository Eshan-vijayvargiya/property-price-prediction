"""Tidy locality names and group Mumbai localities into zones.

Listings type the same place many ways ("Goregaon (East)", "Goregaon East",
"Dahisar W", "Sector-13 Kharghar"). A model can't learn much from a locality
with 3 listings, so every Mumbai locality is also put in one of 7 zones that
a buyer would recognise. Zones are matched by whole-word keywords, in order
(whole words, so "Khar" does not catch "Kharghar").
"""
import re

FIX = {
    r"\(|\)": " ", r"[-_,.]": " ", r"\bw$": "west", r"\be$": "east",
    r"\bdombivali\b": "dombivli", r"\bbunglows?\b": "bungalows", r"\bkapur ?bawdi\b": "kapurbawdi",
    r"\bvikroli\b": "vikhroli", r"\bnapeansea\b": "nepean sea", r"\bambivli\b": "ambivali",
    r"\bpokhran\b": "pokharan", r"\btaloje\b": "taloja", r"\bkoper khairane\b": "koparkhairane",
    r"\bkopar khairane\b": "koparkhairane", r"\bambarnath\b": "ambernath", r"\bville parle\b": "vile parle", r"\bkapurbawadi\b": "kapurbawdi",
    r"\bkasar vadavali\b": "kasarvadavali", r"\bnalasopara\b": "nala sopara",
    r"\bsector(\d)": r"sector \1",
}


def tidy(name):
    """'Goregaon (East)' -> 'Goregaon East'; 'Dahisar W' -> 'Dahisar West'."""
    s = str(name).strip().lower()
    for pat, rep in FIX.items():
        s = re.sub(pat, rep, s)
        s = re.sub(r"\s+", " ", s).strip()
    return " ".join(w.upper() if w in {"ii", "iii", "bkc", "cbd", "mhada", "it", "dn", "tps", "mg", "ic"}
                    else w.capitalize() for w in s.split())


# Order matters: the first zone with a matching keyword wins.
ZONES = [
    ("South Mumbai", [  # the island city, Colaba up to Sion and Mahim
        "colaba", "cuffe", "nariman", "churchgate", "marine lines", "malabar", "nepean", "breach candy",
        "peddar", "haji ali", "tardeo", "mahalaxmi", "grant road", "girgaon", "byculla", "mumbai central",
        "worli", "upper worli", "lower parel", "parel", "prabhadevi", "dadar", "mahim", "matunga", "sewri",
        "wadala", "sion", "antop hill", "altamount", "cumballa", "walkeshwar", "sea face", "agripada",
        "dharavi", "lalbaug", "chinchpokli", "cotton green", "gulal wadi", "kalbadevi", "wadi bandar",
        "willingdon", "bhakti park", "fort", "mazagaon", "mazgaon", "babulnath", "kamathipura",
    ]),
    ("Western Suburbs", [
        "bandra", "khar", "santacruz", "vile parle", "juhu", "andheri", "jogeshwari", "goregaon",
        "malad", "kandivali", "borivali", "dahisar", "versova", "lokhandwala", "oshiwara", "marol",
        "saki naka", "four bungalows", "4 bungalows", "seven bungalows", "pali hill", "charkop",
        "thakur village", "thakur complex", "magathane", "bangur nagar", "dn nagar", "link road",
        "vakola", "kondivita", "chandivali", "almeida park", "gulmohar", "akurli", "samata nagar",
        "shimpoli", "gorai", "dindoshi", "aarey", "rawal pada", "i c colony", "ic colony", "poisar",
        "mahavir nagar", "evershine", "krishanlal marwah", "devidas", "jankalyan", "natakwala",
        "yari road", "gokuldham", "dattapada", "vivek vidyalaya", "dhanukarwadi", "vazira", "poddar road",
        "sen nagar",
    ]),
    ("Central Suburbs", [
        "kurla", "ghatkopar", "vikhroli", "kanjurmarg", "bhandup", "mulund", "powai", "chembur",
        "govandi", "deonar", "mankhurd", "tilak nagar", "nahur", "vidyavihar", "trombay", "chedda",
        "pant nagar", "saki vihar", "jeejamata", "tolaram", "sindhi society", "shell colony",
        "kannamwar", "eastern express", "anushakti", "raheja vihar", "yogi hills",
    ]),
    ("Thane", [
        "thane", "ghodbunder", "majiwada", "kolshet", "balkum", "manpada", "pokharan", "vartak nagar",
        "kasarvadavali", "kalwa", "mumbra", "diva", "shil phata", "shilphata", "kasheli",
        "hiranandani estates", "hiranandani meadows", "vasant vihar", "panch pakhadi", "kapurbawdi",
        "kharegaon", "patlipada", "dokali", "owale", "anand nagar", "brahmand", "waghbil", "naupada",
        "wagle", "bhayandarpada", "parsik", "padle", "rutu enclave", "vedant complex", "beturkar",
        "dhokali", "kavesar", "haware city", "panch pakhdi",
    ]),
    ("Navi Mumbai & Panvel", [
        "kharghar", "ulwe", "panvel", "kamothe", "kalamboli", "vashi", "nerul", "seawoods", "belapur",
        "airoli", "ghansoli", "koparkhairane", "sanpada", "taloja", "dronagiri", "uran", "karanjade",
        "khanda", "juinagar", "turbhe", "rabale", "mahape", "palm beach", "navi mumbai", "sector",
        "roadpali", "nere", "vichumbe", "koproli", "kewale", "karave", "rasayani", "khalapur",
        "palidevad", "petali", "sukapur", "adaigaon", "usarli", "vahal", "shivkar", "kolkhe", "sec",
        "navade",
    ]),
    ("Mira Road & Vasai-Virar", [
        "mira", "bhayandar", "naigaon", "vasai", "nala sopara", "virar", "boisar", "palghar",
        "poonam sagar", "kashimira", "ramdev park", "beverly park", "global city", "shirgaon",
        "umroli", "saphale", "uttan", "vevoor",
    ]),
    ("Kalyan-Dombivli & beyond", [
        "kalyan", "dombivli", "thakurli", "titwala", "ambernath", "badlapur", "vangani", "neral",
        "karjat", "asangaon", "vasind", "palava", "shahad", "ulhasnagar", "bhiwandi", "ambivali",
        "kasara", "katrap", "nilje", "manvel pada", "mumbai nashik", "mumbai agra", "anjurdive",
        "godrej hill", "khopoli", "khoni", "gandhar nagar", "chikhloli", "kulgaon", "morivali",
        "vishnunagar", "vitthalwadi", "shahapur", "kalher", "usarghar",
    ]),
]

ZONE_ORDER = [z for z, _ in ZONES] + ["Other / unclear"]


def zone(name):
    s = tidy(name).lower()
    for z, keys in ZONES:
        for k in keys:
            if re.search(r"\b" + re.escape(k) + r"\b", s):
                return z
    return "Other / unclear"
