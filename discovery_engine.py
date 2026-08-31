"""
TCF Discovery Agent — Scoring Engine
Stage 1 of the AI Career Guidance System

This module is standalone and testable — no UI, no framework dependency.
It takes raw student answers (dict) and produces:
  1. RIASEC scores
  2. Big Five scores
  3. Skills self-ratings
  4. Contradiction flags
  5. Field suggestions
  6. Student report + Counsellor report

Author: Qarib Javed (Developed by Qarib Javed)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import json


# ---------------------------------------------------------------------------
# 1. QUESTION DEFINITIONS
# ---------------------------------------------------------------------------

RIASEC_CATEGORIES = ["R", "I", "A", "S", "E", "C"]

RIASEC_QUESTIONS = {
    "R": [
        {"en": "Fixing something broken (a bike, a gadget, furniture) using tools.",
         "ur": "ٹولز استعمال کر کے کوئی خراب چیز ٹھیک کرنا (سائیکل، گیجٹ، فرنیچر)۔"},
        {"en": "Working outdoors on a physical project (construction, farming, sports).",
         "ur": "کسی جسمانی کام کے لیے باہر کام کرنا (تعمیرات، کھیتی باڑی، کھیل)۔"},
        {"en": "Assembling or building something from parts (a model, a machine, a circuit).",
         "ur": "پرزوں سے کوئی چیز بنانا یا جوڑنا (ماڈل، مشین، سرکٹ)۔"},
        {"en": "Operating or repairing equipment/machinery.",
         "ur": "مشینری چلانا یا اس کی مرمت کرنا۔"},
        {"en": "Working with your hands rather than at a desk all day.",
         "ur": "دن بھر ڈیسک پر بیٹھنے کے بجائے ہاتھوں سے کام کرنا۔"},
        {"en": "Learning a physical/technical trade over a purely theoretical subject.",
         "ur": "خالص نظریاتی مضمون کی بجائے کوئی تکنیکی ہنر سیکھنا۔"},
    ],
    "I": [
        {"en": "Solving a difficult logic or math puzzle just for fun.",
         "ur": "صرف تفریح کے لیے کوئی مشکل منطقی یا ریاضی کی پہیلی حل کرنا۔"},
        {"en": "Researching why something happens rather than just accepting it.",
         "ur": "کسی بات کو مان لینے کے بجائے یہ تحقیق کرنا کہ ایسا کیوں ہوتا ہے۔"},
        {"en": "Running an experiment to test an idea, even if it might fail.",
         "ur": "کسی خیال کو جانچنے کے لیے تجربہ کرنا، چاہے وہ ناکام ہو جائے۔"},
        {"en": "Reading about a scientific discovery in detail out of curiosity.",
         "ur": "تجسس کی وجہ سے کسی سائنسی دریافت کے بارے میں تفصیل سے پڑھنا۔"},
        {"en": "Debugging a problem step-by-step until you find the root cause.",
         "ur": "کسی مسئلے کو قدم بہ قدم حل کرنا جب تک اصل وجہ نہ مل جائے۔"},
        {"en": "Choosing a subject because it makes you think harder, not because it's easy.",
         "ur": "کوئی مضمون اس لیے چننا کہ وہ سوچنے پر مجبور کرے، آسان ہونے کی وجہ سے نہیں۔"},
    ],
    "A": [
        {"en": "Coming up with an original idea rather than following a template.",
         "ur": "کسی سانچے کی پیروی کرنے کے بجائے اپنا اصل خیال پیش کرنا۔"},
        {"en": "Designing something (visual, written, or musical) from scratch.",
         "ur": "کوئی چیز شروع سے ڈیزائن کرنا (بصری، تحریری، یا موسیقی)۔"},
        {"en": "Expressing an opinion through writing, art, or performance.",
         "ur": "تحریر، فن، یا پرفارمنس کے ذریعے اپنی رائے کا اظہار کرنا۔"},
        {"en": "Being given an open-ended task with no fixed 'right answer.'",
         "ur": "ایسا کام جس کا کوئی مقررہ 'صحیح جواب' نہ ہو۔"},
        {"en": "Noticing and caring about how something looks or sounds, not just how it works.",
         "ur": "یہ خیال رکھنا کہ کوئی چیز کیسی نظر آتی یا سنائی دیتی ہے، نہ صرف یہ کہ کیسے کام کرتی ہے۔"},
        {"en": "Choosing originality over following an established method.",
         "ur": "رائج طریقے کی پیروی کے بجائے اصلیت کو ترجیح دینا۔"},
    ],
    "S": [
        {"en": "Explaining a difficult topic to a friend who's stuck.",
         "ur": "کسی دوست کو مشکل موضوع سمجھانا جو الجھن میں ہو۔"},
        {"en": "Being the person others come to for advice.",
         "ur": "وہ شخص ہونا جس کے پاس لوگ مشورے کے لیے آتے ہیں۔"},
        {"en": "Working in a group project where you naturally take the 'people' role.",
         "ur": "گروپ پراجیکٹ میں فطری طور پر 'لوگوں' والا کردار نبھانا۔"},
        {"en": "Volunteering or helping in your community.",
         "ur": "اپنی کمیونٹی میں رضاکارانہ کام یا مدد کرنا۔"},
        {"en": "Noticing when someone is upset even if they haven't said anything.",
         "ur": "کسی کے پریشان ہونے کو محسوس کرنا چاہے اس نے کچھ نہ کہا ہو۔"},
        {"en": "Choosing a task that involves people over one that involves working alone.",
         "ur": "اکیلے کام کرنے کے بجائے لوگوں کے ساتھ کام کرنے کو ترجیح دینا۔"},
    ],
    "E": [
        {"en": "Convincing a group to go along with your plan or idea.",
         "ur": "کسی گروپ کو اپنے منصوبے یا خیال پر راضی کرنا۔"},
        {"en": "Taking charge when a group project has no clear leader.",
         "ur": "جب گروپ پراجیکٹ کا کوئی واضح رہنما نہ ہو تو ذمہ داری سنبھالنا۔"},
        {"en": "Starting something of your own (a small project, page, business idea).",
         "ur": "اپنا کچھ شروع کرنا (چھوٹا پراجیکٹ، پیج، بزنس آئیڈیا)۔"},
        {"en": "Negotiating for something you want (a better grade, a deal, a decision).",
         "ur": "کسی چیز کے لیے بات چیت کرنا جو آپ چاہتے ہیں (بہتر گریڈ، ڈیل، فیصلہ)۔"},
        {"en": "Taking a risk for a bigger potential reward.",
         "ur": "بڑے ممکنہ فائدے کے لیے خطرہ مول لینا۔"},
        {"en": "Choosing a competitive environment over a stable, predictable one.",
         "ur": "مستحکم اور متوقع ماحول کے بجائے مسابقتی ماحول کو ترجیح دینا۔"},
    ],
    "C": [
        {"en": "Organizing a messy set of files, notes, or a schedule.",
         "ur": "بکھری ہوئی فائلوں، نوٹس، یا شیڈول کو ترتیب دینا۔"},
        {"en": "Following a clear step-by-step process rather than improvising.",
         "ur": "فی البدیہہ کام کرنے کے بجائے واضح مرحلہ وار طریقہ اپنانا۔"},
        {"en": "Double-checking details (numbers, spelling, data) before submitting work.",
         "ur": "کام جمع کرانے سے پہلے تفصیلات دوبارہ چیک کرنا (نمبرز، ہجے، ڈیٹا)۔"},
        {"en": "Keeping track of a budget, schedule, or checklist without being told to.",
         "ur": "بغیر کہے بجٹ، شیڈول، یا چیک لسٹ کا خیال رکھنا۔"},
        {"en": "Working within clear rules and structure rather than ambiguity.",
         "ur": "غیر واضح صورتحال کے بجائے واضح اصولوں اور ڈھانچے میں کام کرنا۔"},
        {"en": "Choosing accuracy and consistency over speed.",
         "ur": "رفتار کے بجائے درستگی اور تسلسل کو ترجیح دینا۔"},
    ],
}


# ---------------------------------------------------------------------------
# 1b. PEOPLE / DATA / THINGS / IDEAS (PDTI) — the actual instrument students
# answer. TCF's own scholarship counselling framework references a
# "People, Idea, Things, Data" personality assessment (Scholarship Evaluation
# Process document, Step 2). RIASEC is still the backbone of Stage 1's
# scoring and TCF-domain-suggestion logic — PDTI answers are converted into
# RIASEC scores via a standard vocational-psychology crosswalk (see
# PDTI_TO_RIASEC_CROSSWALK below), so downstream logic is unaffected.
# ---------------------------------------------------------------------------

PDTI_CATEGORIES = ["People", "Data", "Things", "Ideas"]

PDTI_QUESTIONS = {
    "People": [
        {"en": "Helping a struggling classmate understand a topic until it finally clicks for them."},
        {"en": "Leading a small group project and making sure everyone's voice gets heard."},
        {"en": "Sitting with a friend who's upset and just listening, without rushing to fix it."},
        {"en": "Introducing yourself to a room full of strangers and starting conversations."},
        {"en": "Convincing a group to try your idea when they were initially unsure."},
        {"en": "Organizing an event or activity that gets a lot of different people involved."},
        {"en": "Noticing when someone nearby is having a hard day, even if they haven't said anything."},
        {"en": "Being the person people come to first when they need advice or support."},
    ],
    "Data": [
        {"en": "Digging through numbers to find a pattern nobody else noticed."},
        {"en": "Keeping precise track of money spent and saved over a period of time."},
        {"en": "Running a small experiment step by step to see if your prediction was right."},
        {"en": "Double-checking a report for errors before anyone else sees it."},
        {"en": "Figuring out the most cost-efficient way to plan a trip or a budget."},
        {"en": "Writing a set of instructions or code that a computer follows exactly."},
        {"en": "Comparing multiple options using clear criteria before deciding which is best."},
        {"en": "Organizing a messy set of information into clean categories or a table."},
    ],
    "Things": [
        {"en": "Taking apart a broken gadget or toy to figure out what went wrong inside."},
        {"en": "Building or assembling something with your hands until it's finished right."},
        {"en": "Following a recipe or set of steps exactly to cook or make something."},
        {"en": "Fixing something that stopped working — a bike chain, a leaky tap, a loose hinge."},
        {"en": "Spending an afternoon on a hands-on project rather than reading about one."},
        {"en": "Learning how a machine or engine actually works by examining it directly."},
        {"en": "Working outdoors doing physical tasks rather than sitting at a desk."},
        {"en": "Using tools carefully and precisely to get a physical task exactly right."},
    ],
    "Ideas": [
        {"en": "Coming up with a completely new way to solve a problem everyone else does the same old way."},
        {"en": "Writing a story, poem, or piece of music just because an idea wouldn't leave you alone."},
        {"en": "Wondering 'why does this work this way?' until you actually go find out."},
        {"en": "Sketching, designing, or imagining something that doesn't exist yet."},
        {"en": "Debating a big 'what if' or philosophical question just for the fun of thinking it through."},
        {"en": "Noticing a completely different way to look at a familiar problem."},
        {"en": "Getting absorbed in art, design, or performance until you lose track of time."},
        {"en": "Preferring open-ended tasks where you get to decide the approach yourself."},
    ],
}

# Each PDTI category's signal is redistributed across the RIASEC categories
# it's most associated with in standard vocational-psychology crosswalks.
# Each row (PDTI category) sums to 1.0 across its own outgoing weights.
PDTI_TO_RIASEC_CROSSWALK = {
    "People": {"S": 0.55, "E": 0.35, "A": 0.10},
    "Data":   {"C": 0.50, "I": 0.30, "E": 0.20},
    "Things": {"R": 0.75, "I": 0.25},
    "Ideas":  {"A": 0.50, "I": 0.50},
}


def score_pdti(answers: Dict[str, List[int]]) -> Dict[str, int]:
    """Sum each PDTI category's 8 answers (1-5 scale each). Max 40 per category."""
    scores = {}
    for cat in PDTI_CATEGORIES:
        vals = answers.get(cat, [])
        scores[cat] = sum(vals)
    return scores


def crosswalk_pdti_to_riasec(pdti_scores: Dict[str, int], pdti_max_per_category: int = 40,
                               riasec_max_per_category: int = 30) -> Dict[str, int]:
    """
    Converts PDTI category scores into RIASEC category scores using
    PDTI_TO_RIASEC_CROSSWALK, so all of Stage 1's existing RIASEC-based logic
    (TCF domain suggestion, field mapping, contradiction detection) keeps
    working unchanged even though students now answer PDTI-framed questions.
    """
    pdti_fraction = {cat: (pdti_scores.get(cat, 0) / pdti_max_per_category) for cat in PDTI_CATEGORIES}

    incoming_weight = {cat: 0.0 for cat in RIASEC_CATEGORIES}
    for pdti_cat, weights in PDTI_TO_RIASEC_CROSSWALK.items():
        for riasec_cat, w in weights.items():
            incoming_weight[riasec_cat] += w

    riasec_scores = {}
    for riasec_cat in RIASEC_CATEGORIES:
        total = 0.0
        for pdti_cat, weights in PDTI_TO_RIASEC_CROSSWALK.items():
            w = weights.get(riasec_cat, 0.0)
            if w:
                total += pdti_fraction[pdti_cat] * w
        fraction = (total / incoming_weight[riasec_cat]) if incoming_weight[riasec_cat] else 0.0
        riasec_scores[riasec_cat] = round(fraction * riasec_max_per_category)
    return riasec_scores


BIG_FIVE_TRAITS = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "EmotionalStability"]

# Adapted from the IPIP (International Personality Item Pool, Goldberg 1992) —
# a public-domain, research-validated item set. Each trait includes at least
# one reverse-keyed item so genuine variation can be distinguished from
# simple agreement bias. "reverse": True means a HIGH rating on this item
# actually indicates a LOW level of the trait, and must be inverted when scored.
BIG_FIVE_QUESTIONS = {
    "Openness": [
        {"text": "I have a vivid imagination.", "text_ur": "میری تخیل بہت زرخیز ہے۔", "reverse": False},
        {"text": "I enjoy thinking about abstract or theoretical ideas.", "text_ur": "مجھے تجریدی یا نظریاتی خیالات پر سوچنا اچھا لگتا ہے۔", "reverse": False},
        {"text": "I am not very interested in abstract ideas.", "text_ur": "مجھے تجریدی خیالات میں زیادہ دلچسپی نہیں۔", "reverse": True},
        {"text": "I prefer familiar routines over new experiences.", "text_ur": "میں نئے تجربات کی بجائے جانی پہچانی روٹین کو ترجیح دیتا/دیتی ہوں۔", "reverse": True},
    ],
    "Conscientiousness": [
        {"text": "I am always prepared before I need to be.", "text_ur": "میں ضرورت سے پہلے ہی تیار رہتا/رہتی ہوں۔", "reverse": False},
        {"text": "I pay close attention to details in my work.", "text_ur": "میں اپنے کام کی باریکیوں پر خاص توجہ دیتا/دیتی ہوں۔", "reverse": False},
        {"text": "I often leave things until the last minute.", "text_ur": "میں اکثر کام آخری وقت کے لیے چھوڑ دیتا/دیتی ہوں۔", "reverse": True},
        {"text": "I have a hard time following through once something gets boring.", "text_ur": "جب کوئی کام بورنگ ہو جائے تو اسے مکمل کرنا میرے لیے مشکل ہوتا ہے۔", "reverse": True},
    ],
    "Extraversion": [
        {"text": "I feel comfortable around people I don't know well.", "text_ur": "میں ان لوگوں کے ساتھ بھی سہولت محسوس کرتا/کرتی ہوں جنہیں اچھی طرح نہیں جانتا/جانتی۔", "reverse": False},
        {"text": "I start conversations rather than waiting for others to.", "text_ur": "میں دوسروں کا انتظار کرنے کے بجائے خود بات چیت شروع کرتا/کرتی ہوں۔", "reverse": False},
        {"text": "I prefer to stay in the background in group settings.", "text_ur": "گروپ میں مَیں پیچھے رہنا پسند کرتا/کرتی ہوں۔", "reverse": True},
        {"text": "I find it draining to be around large groups for long.", "text_ur": "بڑے گروہوں میں زیادہ دیر رہنا مجھے تھکا دیتا ہے۔", "reverse": True},
    ],
    "Agreeableness": [
        {"text": "I sympathize with others' feelings easily.", "text_ur": "میں دوسروں کے جذبات کو آسانی سے سمجھ لیتا/لیتی ہوں۔", "reverse": False},
        {"text": "I take time out for others even when it's inconvenient.", "text_ur": "میں مشکل وقت میں بھی دوسروں کے لیے وقت نکالتا/نکالتی ہوں۔", "reverse": False},
        {"text": "I am not very interested in other people's problems.", "text_ur": "مجھے دوسروں کے مسائل میں زیادہ دلچسپی نہیں۔", "reverse": True},
        {"text": "I find it hard to compromise when I disagree with someone.", "text_ur": "جب کسی سے اختلاف ہو تو سمجھوتہ کرنا میرے لیے مشکل ہوتا ہے۔", "reverse": True},
    ],
    "EmotionalStability": [
        {"text": "I remain calm under pressure or deadlines.", "text_ur": "دباؤ یا ڈیڈ لائن میں بھی میں پرسکون رہتا/رہتی ہوں۔", "reverse": False},
        {"text": "Setbacks don't affect my mood for long.", "text_ur": "ناکامیاں میرے موڈ کو زیادہ دیر متاثر نہیں کرتیں۔", "reverse": False},
        {"text": "I get stressed out easily.", "text_ur": "میں آسانی سے تناؤ کا شکار ہو جاتا/جاتی ہوں۔", "reverse": True},
        {"text": "I worry about things more than most people seem to.", "text_ur": "میں دوسروں کی نسبت زیادہ فکر مند رہتا/رہتی ہوں۔", "reverse": True},
    ],
}

SKILLS = [
    "Mathematics",
    "LogicalReasoning",
    "WrittenCommunication",
    "VerbalCommunication",
    "Creativity",
    "Leadership",
    "AttentionToDetail",
    "IndependentWork",
]

SKILLS_LABELS_UR = {
    "Mathematics": "ریاضی",
    "LogicalReasoning": "منطقی استدلال",
    "WrittenCommunication": "تحریری ابلاغ",
    "VerbalCommunication": "زبانی ابلاغ",
    "Creativity": "تخلیقی صلاحیت",
    "Leadership": "قیادت",
    "AttentionToDetail": "باریک بینی",
    "IndependentWork": "خودمختار کام",
}

# Academic subject self-rating — a direct cross-check against RIASEC-based
# field suggestions. Interest and personality can point toward a field, but
# if a student is genuinely weak in a subject that field actually requires,
# that's a real, practical mismatch worth surfacing — independent of how
# "into" the field they feel.
ACADEMIC_SUBJECTS = [
    "Biology",
    "Chemistry",
    "Physics",
    "Mathematics",
    "ComputerScience",
    "EnglishLanguage",
]

ACADEMIC_SUBJECTS_LABELS = {
    "Biology": "Biology",
    "Chemistry": "Chemistry",
    "Physics": "Physics",
    "Mathematics": "Mathematics",
    "ComputerScience": "Computer Science",
    "EnglishLanguage": "English / Language & Writing",
}

# Which subjects genuinely matter for each suggested field. Only fields with
# a clear, well-known subject dependency are listed — no entry means no
# subject-based check is applied for that field.
FIELD_SUBJECT_REQUIREMENTS = {
    "Bachelor of Medicine, Bachelor of Surgery (MBBS)": ["Biology", "Chemistry"],
    "Bachelor of Dental Surgery (BDS)": ["Biology", "Chemistry"],
    "Pharmaceutical & Nutritional Sciences": ["Biology", "Chemistry"],
    "Clinical & Medical": ["Biology", "Chemistry"],
    "Vision Care, Diagnostic & Technical": ["Biology", "Chemistry"],
    "Political & Social Sciences": ["Biology"],
    "Aerospace & Aeronautical Engineering": ["Physics", "Mathematics"],
    "Chemical & Petrochemical Engineering": ["Chemistry", "Mathematics"],
    "Civil & Environmental Engineering": ["Physics", "Mathematics"],
    "Electrical & Electronics Engineering": ["Physics", "Mathematics"],
    "Mechanical Engineering": ["Physics", "Mathematics"],
    "Materials, Mining & Textile Engineering": ["Chemistry", "Mathematics"],
    "Chemistry, Physics & Marine Science": ["Physics", "Mathematics"],
    "Computer Science": ["Mathematics", "ComputerScience"],
    "Computer Engineering": ["Mathematics", "Physics"],
    "Software Engineering": ["Mathematics", "ComputerScience"],
    "Statistics & Mathematics": ["Mathematics"],
    "Finance": ["Mathematics"],
    "Economics": ["Mathematics"],
    "Chartered Accountancy (CA/ACCA/ICMA)": ["Mathematics"],
    "Law & Criminal Studies": ["EnglishLanguage"],
}

# Comprehensive mapping — all 15 possible RIASEC top-2 combinations (6 choose 2).
# Field names below are TCF's own official TSP Grid subgroup names.
FIELD_MAPPING_BY_PAIR = {
    frozenset(("R", "I")): ["Civil & Environmental Engineering", "Computer Science", "Chemical & Petrochemical Engineering", "Materials, Mining & Textile Engineering", "Chemistry, Physics & Marine Science"],
    frozenset(("R", "A")): ["Architecture", "Art & Design"],
    frozenset(("R", "S")): ["Health & Physical Education", "Allied Health", "Clinical & Medical"],
    frozenset(("R", "E")): ["Tourism & Hospitality", "Aerospace & Aeronautical Engineering", "Industrial and Manufacturing Engineering"],
    frozenset(("R", "C")): ["Mechanical Engineering", "Electrical & Electronics Engineering", "Materials, Mining & Textile Engineering", "Agricultural Sciences"],
    frozenset(("I", "A")): ["Architecture", "Biological Sciences", "Art & Design"],
    frozenset(("I", "S")): ["Bachelor of Medicine, Bachelor of Surgery (MBBS)", "Bachelor of Dental Surgery (BDS)", "Pharmaceutical & Nutritional Sciences", "Political & Social Sciences", "Clinical & Medical"],
    frozenset(("I", "E")): ["Finance", "Economics", "Biotechnology & Biomedical Engineering"],
    frozenset(("I", "C")): ["Computer Science", "Computer Engineering", "Software Engineering", "Data Science", "Cyber Security", "Statistics & Mathematics", "Chartered Accountancy (CA/ACCA/ICMA)", "Chemistry, Physics & Marine Science"],
    frozenset(("A", "S")): ["Political & Social Sciences", "Education", "Media Sciences & Communication", "Language & Literature"],
    frozenset(("A", "E")): ["Fashion & Textile", "Media Sciences & Communication"],
    frozenset(("A", "C")): ["Art & Design", "Language & Literature"],
    frozenset(("S", "E")): ["Business Administration & Management", "Tourism & Hospitality", "Education", "Law & Criminal Studies"],
    frozenset(("S", "C")): ["Allied Health", "Bachelor of Science in Nursing (BSN)", "Education"],
    frozenset(("E", "C")): ["Business Administration & Management", "Finance", "Chartered Accountancy (CA/ACCA/ICMA)", "Law & Criminal Studies", "Information Technology"],
}

# Single-category fallback (used only if a clean top-2 pair isn't found)
FIELD_MAPPING_SINGLE = {
    "R": ["Mechanical Engineering", "Industrial and Manufacturing Engineering", "Agricultural Sciences"],
    "I": ["Computer Science", "Biological Sciences", "Chemistry, Physics & Marine Science"],
    "A": ["Art & Design", "Media Sciences & Communication", "Architecture"],
    "S": ["Political & Social Sciences", "Education", "Allied Health"],
    "E": ["Business Administration & Management", "Tourism & Hospitality"],
    "C": ["Finance", "Economics", "Chartered Accountancy (CA/ACCA/ICMA)"],
}


# ---------------------------------------------------------------------------
# 2. DATA STRUCTURES
# ---------------------------------------------------------------------------

@dataclass
class StudentResponse:
    student_name: str
    pdti_answers: Dict[str, List[int]]             # e.g. {"People": [3,4,2,5,1,3,4,2], ...} 1-5 scale
    big_five_answers: Dict[str, List[int]]        # e.g. {"Openness": [4,5,3], ...}
    skills_ratings: Dict[str, Tuple[int, str]]     # e.g. {"Mathematics": (2, "I find algebra hard")}
    academic_ratings: Dict[str, int] = None        # e.g. {"Biology": 4, "Chemistry": 2}
    roll_number: str = ""
    student_class: str = ""

    def __post_init__(self):
        if self.academic_ratings is None:
            self.academic_ratings = {}


@dataclass
class ContradictionFlag:
    rule_id: int
    description: str
    follow_up_question: str
    student_response: str = ""


# ---------------------------------------------------------------------------
# 3. SCORING FUNCTIONS
# ---------------------------------------------------------------------------

def score_riasec(answers: Dict[str, List[int]]) -> Dict[str, int]:
    """Sum each RIASEC category's 6 answers. Max 30 per category."""
    scores = {}
    for cat in RIASEC_CATEGORIES:
        vals = answers.get(cat, [])
        scores[cat] = sum(vals)
    return scores


def score_big_five(answers: Dict[str, List[int]]) -> Dict[str, float]:
    """
    Average each Big Five trait's answers (1-5 scale). Reverse-keyed items
    (see BIG_FIVE_QUESTIONS) are inverted (6 - value) before averaging, so a
    high rating on a reverse item correctly pulls the trait score down.
    """
    scores = {}
    for trait in BIG_FIVE_TRAITS:
        raw_vals = answers.get(trait, [])
        item_defs = BIG_FIVE_QUESTIONS[trait]
        adjusted_vals = []
        for i, val in enumerate(raw_vals):
            is_reverse = item_defs[i]["reverse"] if i < len(item_defs) else False
            adjusted_vals.append((6 - val) if is_reverse else val)
        scores[trait] = round(sum(adjusted_vals) / len(adjusted_vals), 2) if adjusted_vals else 0.0
    return scores


def top_riasec_categories(riasec_scores: Dict[str, int], n: int = 2) -> List[str]:
    ranked = sorted(riasec_scores.items(), key=lambda x: x[1], reverse=True)
    return [cat for cat, _ in ranked[:n]]


def bottom_riasec_categories(riasec_scores: Dict[str, int], n: int = 2) -> List[str]:
    ranked = sorted(riasec_scores.items(), key=lambda x: x[1])
    return [cat for cat, _ in ranked[:n]]


# ---------------------------------------------------------------------------
# 3b. RESPONSE VALIDITY CHECK
# ---------------------------------------------------------------------------

import statistics

def check_response_validity(pdti_answers: Dict[str, List[int]]) -> Dict:
    """
    Detects genuine 'straight-lining' — when a student picks the same value
    over and over regardless of what the question actually says.

    Important: this checks variation in the RAW individual answers (all 32
    of them), NOT the final category totals. Category totals can legitimately
    end up close together for a thoughtful student (people naturally cluster
    around middle values) — that is not the same thing as not having read
    the questions. Only near-zero variation in the raw answers themselves
    is a real red flag.

    Returns a dict with 'valid' (bool) and 'reason' (str, only if invalid).
    """
    all_answers = [v for values in pdti_answers.values() for v in values]

    if not all_answers:
        return {"valid": True, "reason": ""}

    unique_values_used = len(set(all_answers))

    # Every single one of the 36 questions got the exact same value —
    # this is the clearest possible sign the questions weren't read.
    if unique_values_used == 1:
        return {
            "valid": False,
            "reason": (
                "Every question got the exact same rating, which makes it impossible to tell "
                "what you actually enjoy versus don't. Please retake this thinking through each "
                "scenario individually — they're each asking about something different."
            ),
        }

    # Beyond exact repetition, check for near-zero variation using standard deviation.
    # A genuinely varied (even if narrow) response pattern will have some spread;
    # true carelessness clusters almost entirely on one or two values.
    stdev = statistics.pstdev(all_answers)
    if stdev < 0.4:
        return {
            "valid": False,
            "reason": (
                "Your answers barely varied across the questions, which makes it hard to tell "
                "what genuinely interests you. Please retake this thinking through each scenario "
                "individually rather than picking the same rating each time."
            ),
        }

    return {"valid": True, "reason": ""}


# ---------------------------------------------------------------------------
# 4. CONTRADICTION DETECTION (fixed rule table — not free-form AI judgment)
# ---------------------------------------------------------------------------

def detect_contradictions(
    riasec_scores: Dict[str, int],
    big_five_scores: Dict[str, float],
    skills_ratings: Dict[str, Tuple[int, str]],
) -> List[ContradictionFlag]:

    flags = []
    top2 = top_riasec_categories(riasec_scores, 2)
    bottom2 = bottom_riasec_categories(riasec_scores, 2)

    # Rule 1: Low Maths rating but leans Engineering/CS (high R or I)
    maths_rating = skills_ratings.get("Mathematics", (3, ""))[0]
    if maths_rating <= 2 and ("R" in top2 or "I" in top2):
        flags.append(ContradictionFlag(
            rule_id=1,
            description="Low Maths self-rating but interest profile leans Engineering/CS.",
            follow_up_question=(
                "You rated Maths low, but your answers point toward Engineering/CS-type fields. "
                "Tell me more — is it the subject you find hard, or how it's taught?"
            ),
        ))

    # Rule 2: Low Extraversion but Enterprising is top-2
    if big_five_scores.get("Extraversion", 3) <= 2 and "E" in top2:
        flags.append(ContradictionFlag(
            rule_id=2,
            description="Low Extraversion but Enterprising scores are top-2.",
            follow_up_question=(
                "You leaned toward leadership/enterprising scenarios, but described yourself as "
                "more reserved in groups. Do you enjoy leading in smaller or written/behind-the-scenes "
                "ways rather than big group settings?"
            ),
        ))

    # Rule 3: Social is top-2 but prefers independent work
    independent_rating = skills_ratings.get("IndependentWork", (3, ""))[0]
    if "S" in top2 and independent_rating <= 2:
        flags.append(ContradictionFlag(
            rule_id=3,
            description="High Social interest but strong preference for independent work.",
            follow_up_question=(
                "You scored high on helping/working with people, but said you prefer working "
                "independently. Can you tell me about a time you helped someone — did you enjoy "
                "the interaction, or just the outcome?"
            ),
        ))

    # Rule 4: Low Conventional but high Attention to Detail
    detail_rating = skills_ratings.get("AttentionToDetail", (3, ""))[0]
    if "C" in bottom2 and detail_rating >= 4:
        flags.append(ContradictionFlag(
            rule_id=4,
            description="Low Conventional interest but high Attention-to-Detail self-rating.",
            follow_up_question=(
                "You said you're very detail-oriented, but structured/organized tasks didn't come "
                "up as something you enjoy. Do you like detail because it's satisfying, or because "
                "it's necessary for something else you care about?"
            ),
        ))

    # Rule 5: Low Emotional Stability but Enterprising is top-2
    if big_five_scores.get("EmotionalStability", 3) <= 2 and "E" in top2:
        flags.append(ContradictionFlag(
            rule_id=5,
            description="Low Emotional Stability but drawn to competitive/enterprising paths.",
            follow_up_question=(
                "You're drawn to competitive/ambitious paths, but pressure situations affect you "
                "a lot. What kind of support or pace would help you thrive in a field like that?"
            ),
        ))

    # Rule 6: High Investigative interest but low Logical Reasoning self-rating
    logic_rating = skills_ratings.get("LogicalReasoning", (3, ""))[0]
    if "I" in top2 and logic_rating <= 2:
        flags.append(ContradictionFlag(
            rule_id=6,
            description="High Investigative interest but low Logical Reasoning self-rating.",
            follow_up_question=(
                "You're drawn to research/analytical scenarios, but rated your logical reasoning "
                "low. Is that about confidence, or about a specific type of problem you find hard?"
            ),
        ))

    # Rule 7: High Artistic interest but low Creativity self-rating
    creativity_rating = skills_ratings.get("Creativity", (3, ""))[0]
    if "A" in top2 and creativity_rating <= 2:
        flags.append(ContradictionFlag(
            rule_id=7,
            description="High Artistic interest but low Creativity self-rating.",
            follow_up_question=(
                "You leaned toward original/creative scenarios, but rated your own creativity low. "
                "Do you enjoy creative work but doubt your output, or is it something else?"
            ),
        ))

    # Rule 8: High Enterprising interest but low Leadership self-rating
    leadership_rating = skills_ratings.get("Leadership", (3, ""))[0]
    if "E" in top2 and leadership_rating <= 2:
        flags.append(ContradictionFlag(
            rule_id=8,
            description="High Enterprising interest but low Leadership self-rating.",
            follow_up_question=(
                "You're drawn to leadership/enterprising scenarios, but rated your leadership low. "
                "Have you had a chance to actually lead something, or is this untested so far?"
            ),
        ))

    # Rule 9: High Conventional interest but low Attention-to-Detail self-rating (inverse of Rule 4)
    if "C" in top2 and detail_rating <= 2:
        flags.append(ContradictionFlag(
            rule_id=9,
            description="High Conventional interest but low Attention-to-Detail self-rating.",
            follow_up_question=(
                "You leaned toward structured, organized scenarios, but rated your attention to "
                "detail low. Do you enjoy the structure more than the precision itself?"
            ),
        ))

    # Rule 10: High Social interest but low Verbal Communication self-rating
    verbal_rating = skills_ratings.get("VerbalCommunication", (3, ""))[0]
    if "S" in top2 and verbal_rating <= 2:
        flags.append(ContradictionFlag(
            rule_id=10,
            description="High Social interest but low Verbal Communication self-rating.",
            follow_up_question=(
                "You're drawn to people-facing/helping scenarios, but rated your verbal "
                "communication low. Is that about speaking to groups specifically, or communication "
                "in general?"
            ),
        ))

    # Rule 11: I+S profile (medical-track territory) but low Emotional Stability —
    # clinical/medical fields often involve high-pressure, high-stakes situations.
    if "I" in top2 and "S" in top2 and big_five_scores.get("EmotionalStability", 3) <= 2:
        flags.append(ContradictionFlag(
            rule_id=11,
            description="Medical/healthcare-leaning interest profile but low Emotional Stability.",
            follow_up_question=(
                "Your interests point toward medical or healthcare-related fields, which often "
                "involve high-pressure, high-stakes situations. How do you currently handle stress "
                "in demanding situations, and is that something you'd want support with?"
            ),
        ))

    return flags


# ---------------------------------------------------------------------------
# 5. FIELD SUGGESTION
# ---------------------------------------------------------------------------

# The Investigative+Social pair is unusually crowded — it covers everything from
# surgery to public health to psychology, which have very different day-to-day
# realities. We use the THIRD-highest RIASEC category to narrow this down.
MEDICAL_TRACK_SUBSPLIT = {
    "R": ["Bachelor of Medicine, Bachelor of Surgery (MBBS)", "Bachelor of Dental Surgery (BDS)", "Clinical & Medical"],           # hands-on, clinical
    "C": ["Pharmaceutical & Nutritional Sciences", "Vision Care, Diagnostic & Technical"],       # structured, precision, lab-based
    "A": ["Political & Social Sciences", "Media Sciences & Communication"],                 # expressive, human-focused
    "E": ["Business Administration & Management", "Bachelor of Medicine, Bachelor of Surgery (MBBS)"],  # leadership-facing
}


# ---------------------------------------------------------------------------
# TCF's OFFICIAL RIASEC → Discipline Mapping
# Source: TCF "Tertiary Assessment Process" (7th Nov 2025), Slide 22 —
# "Personality Assessment (SPI) – RIASEC". This is TCF's own scholarship
# assessment framework, not an external/invented model — CareerPilot's
# domain suggestions are aligned to it directly.
# ---------------------------------------------------------------------------

TCF_DISCIPLINE_GROUPS = [
    "Engineering",
    "Computer Studies",
    "Health Sciences",
    "Management Sciences",
    "Natural Sciences",
    "Social Sciences & Arts",
    "Agricultural Sciences",
]

# Ordered by TCF's own best-fit priority per RIASEC letter (slide 22 table)
TCF_RIASEC_TO_DISCIPLINES = {
    "R": ["Engineering", "Computer Studies", "Natural Sciences", "Agricultural Sciences"],
    "I": ["Health Sciences", "Natural Sciences", "Engineering", "Computer Studies"],
    "A": ["Social Sciences & Arts", "Computer Studies"],
    "S": ["Health Sciences", "Social Sciences & Arts", "Management Sciences"],
    "E": ["Management Sciences", "Social Sciences & Arts", "Computer Studies"],
    "C": ["Management Sciences", "Computer Studies", "Natural Sciences", "Social Sciences & Arts"],
}


def suggest_tcf_domains(riasec_scores: Dict[str, int], max_domains: int = 3) -> List[str]:
    """
    Suggests discipline domains using TCF's own official RIASEC-to-discipline
    table, rather than an independently invented category system. Domains
    that appear in BOTH of the student's top-2 RIASEC categories are ranked
    first (strongest fit), followed by domains appearing in only one.
    """
    top2 = top_riasec_categories(riasec_scores, 2)
    if len(top2) < 2:
        return TCF_RIASEC_TO_DISCIPLINES.get(top2[0], [])[:max_domains] if top2 else []

    cat1, cat2 = top2[0], top2[1]
    list1 = TCF_RIASEC_TO_DISCIPLINES.get(cat1, [])
    list2 = TCF_RIASEC_TO_DISCIPLINES.get(cat2, [])

    common = [d for d in list1 if d in list2]
    only1 = [d for d in list1 if d not in common]
    only2 = [d for d in list2 if d not in common]

    ordered = common + only1 + only2
    seen = set()
    deduped = []
    for d in ordered:
        if d not in seen:
            seen.add(d)
            deduped.append(d)
    return deduped[:max_domains]


def assess_confidence(riasec_scores: Dict[str, int]) -> Dict:
    """
    Determines how clearly differentiated the top RIASEC categories are.
    A student whose top 2-3 categories are close together has a genuinely
    more balanced profile — the suggestions shouldn't be presented with the
    same confidence as a student with one or two categories clearly ahead.
    """
    ranked = sorted(riasec_scores.values(), reverse=True)
    if len(ranked) < 3:
        return {"level": "strong", "note": ""}

    top_score = ranked[0]
    third_score = ranked[2]
    margin = top_score - third_score  # gap between #1 and #3

    if margin >= 8:
        return {
            "level": "strong",
            "note": "",
        }
    elif margin >= 4:
        return {
            "level": "moderate",
            "note": "Your interests lean in a fairly clear direction, though a few other areas scored close behind — worth keeping an open mind about them too.",
        }
    else:
        return {
            "level": "mixed",
            "note": "Your interests came out fairly balanced across several areas rather than pointing strongly in one direction. That's not a bad thing — it just means this is a good topic to explore further with your counsellor rather than treat as settled.",
        }


# TCF's own subject-score thresholds, validated against 600 real 2025-26
# admissions (Tertiary Assessment Process, 7th Nov 2025, Slide 19 & 27).
# Used to cite real, TCF-verified numbers in contradiction follow-ups
# instead of a generic "you rated yourself weak" statement.
TCF_VALIDATED_THRESHOLDS = {
    "Civil & Environmental Engineering": "TCF's own admissions data shows students placed in top-tier Engineering programs typically have Mathematics and Physics scores of 55-60% or higher.",
    "Mechanical Engineering": "TCF's own admissions data shows students placed in top-tier Engineering programs typically have Mathematics and Physics scores of 55-60% or higher.",
    "Electrical & Electronics Engineering": "TCF's own admissions data shows students placed in top-tier Engineering programs typically have Mathematics and Physics scores of 55-60% or higher.",
    "Chemical & Petrochemical Engineering": "TCF's own admissions data shows students placed in top-tier Engineering programs typically have Mathematics and Physics scores of 55-60% or higher.",
    "Computer Science": "TCF's own admissions data shows students placed in top-tier Computer Science programs typically have Mathematics and Physics scores of 55-60% or higher.",
    "Software Engineering": "TCF's own admissions data shows students placed in top-tier Computer Science programs typically have Mathematics and Physics scores of 55-60% or higher.",
    "Bachelor of Medicine, Bachelor of Surgery (MBBS)": "TCF's minimum threshold for MBBS/BDS is 80% overall intermediate marks, with Biology and Chemistry each at 60% or higher.",
    "Bachelor of Dental Surgery (BDS)": "TCF's minimum threshold for MBBS/BDS is 80% overall intermediate marks, with Biology and Chemistry each at 60% or higher.",
    "Pharmaceutical & Nutritional Sciences": "TCF's data shows Health Sciences students placed in top-tier programs typically have Biology and Chemistry at 55% or higher.",
    "Vision Care, Diagnostic & Technical": "TCF's data shows Health Sciences students placed in top-tier programs typically have Biology and Chemistry at 55% or higher.",
}


def check_subject_alignment(
    suggested_fields: List[str], academic_ratings: Dict[str, int]
) -> List["ContradictionFlag"]:
    """
    Cross-checks suggested fields against the student's own subject-performance
    self-ratings. Interest and personality can point toward a field, but if a
    student is genuinely weak in a subject that field actually depends on
    (e.g., Biology for Medicine, Physics/Maths for Engineering), that's a
    concrete, practical mismatch worth a counsellor's attention — independent
    of how interested the student feels.
    """
    flags = []
    rule_id = 12  # continues on from the 11 RIASEC/Big-Five-based rules

    already_flagged_fields = set()
    for field in suggested_fields:
        required = FIELD_SUBJECT_REQUIREMENTS.get(field)
        if not required or field in already_flagged_fields:
            continue

        weak_subjects = [
            s for s in required
            if academic_ratings.get(s) is not None and academic_ratings[s] <= 2
        ]
        if weak_subjects:
            subject_names = ", ".join(ACADEMIC_SUBJECTS_LABELS.get(s, s) for s in weak_subjects)
            tcf_note = TCF_VALIDATED_THRESHOLDS.get(field, "")
            follow_up = (
                f"Your interests point toward {field}, which usually depends heavily on "
                f"{subject_names}. You rated yourself as weak there — is that about how it's "
                f"taught, or a genuine difficulty with the subject? This is worth discussing "
                f"honestly before committing to this direction."
            )
            if tcf_note:
                follow_up += f" {tcf_note}"
            flags.append(ContradictionFlag(
                rule_id=rule_id,
                description=f"Suggested field '{field}' depends on {subject_names}, which the student rated as weak.",
                follow_up_question=follow_up,
            ))
            already_flagged_fields.add(field)
            rule_id += 1

    return flags


def suggest_fields(riasec_scores: Dict[str, int]) -> List[str]:
    top3 = top_riasec_categories(riasec_scores, 3)
    top2 = top3[:2]
    pair_key = frozenset(top2)

    # Special case: I+S is too broad on its own — use the 3rd category to differentiate
    # between hands-on medical fields, structured/lab fields, people-focused fields, etc.
    if pair_key == frozenset(("I", "S")) and len(top3) == 3:
        third = top3[2]
        suggestions = list(MEDICAL_TRACK_SUBSPLIT.get(third, []))
        if not suggestions:
            # No strong 3rd-category signal — fall back to the broad I+S list
            suggestions = list(FIELD_MAPPING_BY_PAIR.get(pair_key, []))
    else:
        suggestions = list(FIELD_MAPPING_BY_PAIR.get(pair_key, []))

    # Fallback: top-1 category alone, if the pair isn't in the table for some reason
    if not suggestions:
        top1 = top2[0]
        suggestions = list(FIELD_MAPPING_SINGLE.get(top1, []))

    # De-duplicate while preserving order
    seen = set()
    deduped = []
    for f in suggestions:
        if f not in seen:
            seen.add(f)
            deduped.append(f)
    return deduped[:5]  # cap at 5 suggestions


# ---------------------------------------------------------------------------
# 6. REPORT GENERATION
# ---------------------------------------------------------------------------

RIASEC_CATEGORY_DESCRIPTIONS = {
    "R": "hands-on, practical work",
    "I": "analytical, research-driven thinking",
    "A": "creative, original expression",
    "S": "people-focused, helping work",
    "E": "leadership and business-driven work",
    "C": "structured, organized work",
}

BIG_FIVE_TRAIT_DESCRIPTIONS = {
    "Openness": {
        "high": "curious and drawn to new ideas and possibilities",
        "low": "prefers familiar, proven approaches over experimenting",
    },
    "Conscientiousness": {
        "high": "organized, dependable, and detail-oriented",
        "low": "flexible and spontaneous, sometimes at the cost of structure",
    },
    "Extraversion": {
        "high": "energized by people and social settings",
        "low": "prefers quieter, more independent settings",
    },
    "Agreeableness": {
        "high": "empathetic and cooperative with others",
        "low": "direct, and comfortable with disagreement",
    },
    "EmotionalStability": {
        "high": "generally calm and steady under pressure",
        "low": "feels stress more intensely than most, especially under pressure",
    },
}


def generate_personality_overview(riasec_scores: Dict[str, int], big_five_scores: Dict[str, float]) -> str:
    """
    Produces a short, honest description of the student's interest and
    personality profile — WITHOUT naming any specific field or career.
    This is intentional: Stage 1 describes the person, not the destination.
    """
    top2 = top_riasec_categories(riasec_scores, 2)
    riasec_phrase = " and ".join(RIASEC_CATEGORY_DESCRIPTIONS[c] for c in top2)

    notable_traits = []
    for trait, score in big_five_scores.items():
        if score >= 4.0:
            notable_traits.append(BIG_FIVE_TRAIT_DESCRIPTIONS[trait]["high"])
        elif score <= 2.0:
            notable_traits.append(BIG_FIVE_TRAIT_DESCRIPTIONS[trait]["low"])

    overview = f"Your answers show a strong lean toward {riasec_phrase}. "

    if notable_traits:
        if len(notable_traits) == 1:
            overview += f"You also come across as someone who is {notable_traits[0]}."
        else:
            overview += "You also come across as someone who is " + ", ".join(notable_traits[:-1]) + f", and {notable_traits[-1]}."
    else:
        overview += "Your personality traits came out fairly balanced overall, without any single trait standing out strongly."

    return overview


def generate_student_report(name: str, riasec_scores: Dict[str, int], big_five_scores: Dict[str, float], confidence: Dict) -> str:
    overview = generate_personality_overview(riasec_scores, big_five_scores)

    report = f"Hi {name},\n\n{overview}\n"
    if confidence["note"]:
        report += f"\n{confidence['note']}\n"
    report += (
        "\nThis is a description of how you think and work — not a final decision. "
        "Use Stage 2 to explore specific fields within the domain(s) suggested for you."
    )
    return report


def generate_counsellor_report(
    student: StudentResponse,
    riasec_scores: Dict[str, int],
    big_five_scores: Dict[str, float],
    flags: List[ContradictionFlag],
    fields: List[str],
) -> str:
    lines = []
    lines.append(f"COUNSELLOR REPORT — {student.student_name}")
    if student.roll_number or student.student_class:
        lines.append(f"Roll Number: {student.roll_number or '—'}  |  Class: {student.student_class or '—'}")
    lines.append("=" * 50)
    lines.append("\nRIASEC Scores (max 30 each):")
    for cat, val in sorted(riasec_scores.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"  {cat}: {val}")

    lines.append("\nBig Five Snapshot (1-5 scale):")
    for trait, val in big_five_scores.items():
        lines.append(f"  {trait}: {val}")

    lines.append("\nSkills Self-Ratings (with student's stated reason):")
    for skill, (rating, reason) in student.skills_ratings.items():
        lines.append(f"  {skill}: {rating}/5 — \"{reason}\"")

    if student.academic_ratings:
        lines.append("\nAcademic Subject Self-Ratings:")
        for subject, rating in student.academic_ratings.items():
            label = ACADEMIC_SUBJECTS_LABELS.get(subject, subject)
            lines.append(f"  {label}: {rating}/5")

    lines.append(f"\nFlagged Contradictions ({len(flags)}):")
    if not flags:
        lines.append("  None triggered.")
    else:
        for f in flags:
            lines.append(f"  Rule {f.rule_id}: {f.description}")
            lines.append(f"    Follow-up asked: {f.follow_up_question}")
            if f.student_response:
                lines.append(f"    Student's answer: \"{f.student_response}\"")

    lines.append(f"\nSuggested Field Directions: {', '.join(fields)}")
    confidence = assess_confidence(riasec_scores)
    lines.append(f"Confidence level: {confidence['level'].upper()}")
    if confidence["note"]:
        lines.append(f"  Note: {confidence['note']}")
    lines.append("\nCounsellor prompt suggestions:")
    if flags:
        for f in flags:
            lines.append(f"  - Rule {f.rule_id} triggered — consider probing this further in the interview.")
    else:
        lines.append("  - No major contradictions flagged; proceed with standard field exploration.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 6b. QUESTION EXPORT (for frontend consumption)
# ---------------------------------------------------------------------------

def get_all_questions() -> Dict:
    """Returns the full question bank in a frontend-friendly structure."""
    return {
        "pdti": [
            {"category": cat, "question": item["en"]}
            for cat, items in PDTI_QUESTIONS.items() for item in items
        ],
        "big_five": [
            {
                "trait": trait, "question": item["text"], "question_ur": item["text_ur"],
                "reverse": item["reverse"],
            }
            for trait, items in BIG_FIVE_QUESTIONS.items() for item in items
        ],
        "skills": SKILLS,
        "skills_labels_ur": SKILLS_LABELS_UR,
        "academic_subjects": ACADEMIC_SUBJECTS,
        "academic_subjects_labels": ACADEMIC_SUBJECTS_LABELS,
    }


def parse_submission(payload: Dict) -> StudentResponse:
    """Converts raw JSON payload from the frontend into a StudentResponse object."""
    pdti_answers: Dict[str, List[int]] = {cat: [] for cat in PDTI_CATEGORIES}
    for cat, q_idx, value in payload["pdti"]:
        pdti_answers[cat].append(int(value))

    big_five_answers: Dict[str, List[int]] = {trait: [] for trait in BIG_FIVE_TRAITS}
    for trait, q_idx, value in payload["big_five"]:
        big_five_answers[trait].append(int(value))

    skills_ratings: Dict[str, Tuple[int, str]] = {}
    for skill, rating, reason in payload["skills"]:
        skills_ratings[skill] = (int(rating), reason)

    academic_ratings: Dict[str, int] = {}
    for subject, rating in payload.get("academic", []):
        academic_ratings[subject] = int(rating)

    return StudentResponse(
        student_name=payload.get("student_name", "Student"),
        roll_number=payload.get("student_roll", ""),
        student_class=payload.get("student_class", ""),
        pdti_answers=pdti_answers,
        big_five_answers=big_five_answers,
        skills_ratings=skills_ratings,
        academic_ratings=academic_ratings,
    )


# ---------------------------------------------------------------------------
# 7. MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def run_discovery_assessment(student: StudentResponse) -> Dict:
    pdti_scores = score_pdti(student.pdti_answers)
    riasec_scores = crosswalk_pdti_to_riasec(pdti_scores)
    big_five_scores = score_big_five(student.big_five_answers)

    validity = check_response_validity(student.pdti_answers)

    if not validity["valid"]:
        # Don't fabricate a confident suggestion from flat/meaningless scores.
        student_report = (
            f"Hi {student.student_name},\n\n"
            f"{validity['reason']}\n\n"
            "Rather than guess, it's better to either retake this thinking through each scenario "
            "individually, or talk this through directly with your counsellor."
        )
        counsellor_report = (
            f"COUNSELLOR REPORT — {student.student_name}\n" + "=" * 50 +
            f"\n\nVALIDITY FLAG: Straight-lined / flat response pattern detected.\n"
            f"PDTI scores: {pdti_scores}\n"
            f"Derived RIASEC scores: {riasec_scores}\n"
            "No reliable field suggestion could be generated from this response set. "
            "Recommend a retake or a direct conversation to establish genuine interests."
        )
        return {
            "pdti_scores": pdti_scores,
            "riasec_scores": riasec_scores,
            "big_five_scores": big_five_scores,
            "contradiction_flags": [],
            "suggested_fields": [],
            "valid_response": False,
            "reason": validity["reason"],
            "student_report": student_report,
            "counsellor_report": counsellor_report,
        }

    flags = detect_contradictions(riasec_scores, big_five_scores, student.skills_ratings)
    fields = suggest_fields(riasec_scores)
    flags += check_subject_alignment(fields, student.academic_ratings)
    confidence = assess_confidence(riasec_scores)
    personality_overview = generate_personality_overview(riasec_scores, big_five_scores)
    tcf_domains = suggest_tcf_domains(riasec_scores)

    student_report = generate_student_report(student.student_name, riasec_scores, big_five_scores, confidence)
    counsellor_report = generate_counsellor_report(student, riasec_scores, big_five_scores, flags, fields)

    return {
        "pdti_scores": pdti_scores,
        "riasec_scores": riasec_scores,
        "big_five_scores": big_five_scores,
        "contradiction_flags": [f.__dict__ for f in flags],
        "suggested_fields": fields,
        "suggested_domains": tcf_domains,
        "valid_response": True,
        "confidence": confidence,
        "personality_overview": personality_overview,
        "student_report": student_report,
        "counsellor_report": counsellor_report,
    }


# ---------------------------------------------------------------------------
# 8. QUICK TEST (run this file directly to see a sample output)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample_student = StudentResponse(
        student_name="Ali Raza",
        pdti_answers={
            "People": [3, 2, 3, 2, 3, 2, 3, 2],
            "Data": [5, 4, 5, 4, 5, 4, 5, 4],
            "Things": [2, 1, 2, 1, 2, 2, 2, 1],
            "Ideas": [4, 5, 4, 5, 4, 5, 4, 5],
        },
        big_five_answers={
            "Openness": [4, 4, 2, 2],
            "Conscientiousness": [5, 4, 2, 2],
            "Extraversion": [2, 2, 4, 4],
            "Agreeableness": [3, 3, 3, 3],
            "EmotionalStability": [3, 4, 2, 2],
        },
        skills_ratings={
            "Mathematics": (2, "I struggle with timed algebra tests"),
            "LogicalReasoning": (5, "I enjoy puzzles and coding logic"),
            "WrittenCommunication": (3, "Average, don't write much"),
            "VerbalCommunication": (2, "I get nervous presenting"),
            "Creativity": (3, "Sometimes, mostly in problem-solving"),
            "Leadership": (2, "Prefer not to lead groups"),
            "AttentionToDetail": (5, "I double-check everything"),
            "IndependentWork": (5, "I focus best alone"),
        },
    )

    result = run_discovery_assessment(sample_student)
    print(result["student_report"])
    print("\n" + "=" * 60 + "\n")
    print(result["counsellor_report"])
