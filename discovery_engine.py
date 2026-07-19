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
    "Medicine (MBBS)": ["Biology", "Chemistry"],
    "Dentistry": ["Biology", "Chemistry"],
    "Pharmacy": ["Biology", "Chemistry"],
    "Veterinary Sciences": ["Biology", "Chemistry"],
    "Medical Laboratory Sciences": ["Biology", "Chemistry"],
    "Public Health": ["Biology"],
    "Engineering": ["Physics", "Mathematics"],
    "Mechanical/Electrical Engineering": ["Physics", "Mathematics"],
    "Chemical Engineering": ["Chemistry", "Mathematics"],
    "Textile Engineering": ["Chemistry", "Mathematics"],
    "Applied Physics": ["Physics", "Mathematics"],
    "Environmental Science": ["Biology", "Chemistry"],
    "Computer Science": ["Mathematics", "ComputerScience"],
    "Data Science": ["Mathematics", "ComputerScience"],
    "Actuarial Science": ["Mathematics"],
    "Statistics": ["Mathematics"],
    "Economics": ["Mathematics"],
    "Accounting/Finance": ["Mathematics"],
    "Chartered Accountancy (CA/ACCA)": ["Mathematics"],
    "Finance": ["Mathematics"],
    "Law": ["EnglishLanguage"],
}

# Comprehensive mapping — all 15 possible RIASEC top-2 combinations (6 choose 2).
# Based on standard Holland Code career-cluster associations.
FIELD_MAPPING_BY_PAIR = {
    frozenset(("R", "I")): ["Engineering", "Computer Science", "Chemical Engineering", "Textile Engineering", "Environmental Science", "Applied Physics"],
    frozenset(("R", "A")): ["Architecture", "Industrial/Product Design"],
    frozenset(("R", "S")): ["Sports Science/Coaching", "Paramedic/Emergency Services", "Veterinary Sciences"],
    frozenset(("R", "E")): ["Construction Management", "Technical Entrepreneurship", "Aviation"],
    frozenset(("R", "C")): ["Mechanical/Electrical Engineering", "Technical & Trades fields", "Quality Control", "Agriculture Sciences"],
    frozenset(("I", "A")): ["Architecture", "Research Science", "UX/Design Research"],
    frozenset(("I", "S")): ["Medicine (MBBS)", "Dentistry", "Pharmacy", "Psychology", "Public Health", "Veterinary Sciences"],
    frozenset(("I", "E")): ["Data Science", "Economics", "Actuarial Science", "Biotech/Health-tech Entrepreneurship"],
    frozenset(("I", "C")): ["Computer Science", "Data Science", "Accounting/Finance", "Chartered Accountancy (CA/ACCA)", "Actuarial Science", "Statistics"],
    frozenset(("A", "S")): ["Psychology", "Teaching", "Mass Communication/Journalism", "Media/Communications", "Counseling"],
    frozenset(("A", "E")): ["Marketing", "Advertising", "Mass Communication/Journalism", "Media Production"],
    frozenset(("A", "C")): ["Graphic/Structured Design", "Publishing & Editing", "Fashion Merchandising"],
    frozenset(("S", "E")): ["Business/Management", "Marketing", "Human Resources", "Education", "Hotel Management", "Law"],
    frozenset(("S", "C")): ["Human Resources", "Nursing/Healthcare Administration", "Social Work Administration"],
    frozenset(("E", "C")): ["Business Administration", "Law", "Finance", "Accounting", "Chartered Accountancy (CA/ACCA)"],
}

# Single-category fallback (used only if a clean top-2 pair isn't found)
FIELD_MAPPING_SINGLE = {
    "R": ["Engineering", "Technical/Trades fields", "Agriculture Sciences"],
    "I": ["Computer Science", "Research Science", "Data Science", "Economics"],
    "A": ["Design", "Media/Communications", "Architecture"],
    "S": ["Psychology", "Teaching", "Human Resources"],
    "E": ["Business Administration", "Marketing", "Entrepreneurship"],
    "C": ["Accounting/Finance", "Business Administration", "Chartered Accountancy (CA/ACCA)"],
}


# ---------------------------------------------------------------------------
# 2. DATA STRUCTURES
# ---------------------------------------------------------------------------

@dataclass
class StudentResponse:
    student_name: str
    riasec_answers: Dict[str, List[int]]          # e.g. {"R": [3,4,2,5,1,3], ...} 1-5 scale
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

def check_response_validity(riasec_answers: Dict[str, List[int]]) -> Dict:
    """
    Detects genuine 'straight-lining' — when a student picks the same value
    over and over regardless of what the question actually says.

    Important: this checks variation in the RAW individual answers (all 36
    of them), NOT the final category totals. Category totals can legitimately
    end up close together for a thoughtful student (people naturally cluster
    around middle values) — that is not the same thing as not having read
    the questions. Only near-zero variation in the raw answers themselves
    is a real red flag.

    Returns a dict with 'valid' (bool) and 'reason' (str, only if invalid).
    """
    all_answers = [v for values in riasec_answers.values() for v in values]

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
    "R": ["Medicine (MBBS)", "Dentistry", "Veterinary Sciences"],           # hands-on, clinical
    "C": ["Pharmacy", "Public Health", "Medical Laboratory Sciences"],       # structured, precision, lab-based
    "A": ["Psychology", "Counseling", "Medical Humanities"],                 # expressive, human-focused
    "E": ["Healthcare Management", "Public Health Administration", "Medicine (MBBS)"],  # leadership-facing
}


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
            flags.append(ContradictionFlag(
                rule_id=rule_id,
                description=f"Suggested field '{field}' depends on {subject_names}, which the student rated as weak.",
                follow_up_question=(
                    f"Your interests point toward {field}, which usually depends heavily on "
                    f"{subject_names}. You rated yourself as weak there — is that about how it's "
                    f"taught, or a genuine difficulty with the subject? This is worth discussing "
                    f"honestly before committing to this direction."
                ),
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

def generate_student_report(name: str, fields: List[str], riasec_scores: Dict[str, int]) -> str:
    top2 = top_riasec_categories(riasec_scores, 2)
    category_names = {
        "R": "hands-on/practical work", "I": "analytical/research-driven work",
        "A": "creative/original work", "S": "people-focused/helping work",
        "E": "leadership/business-driven work", "C": "structured/organized work",
    }
    reasons = ", ".join(category_names[c] for c in top2)
    confidence = assess_confidence(riasec_scores)

    report = f"Hi {name},\n\n"
    report += "Based on your answers, here are directions that seem to genuinely fit how you think and work:\n\n"
    for f in fields:
        report += f"  • {f}\n"
    report += f"\nWhy: your answers show a strong lean toward {reasons}.\n"
    if confidence["note"]:
        report += f"\n{confidence['note']}\n"
    report += "\nThis isn't a final decision — it's a starting point for your counselling session."
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
    """Returns the full question bank in a frontend-friendly structure, with Urdu translations."""
    return {
        "riasec": [
            {"category": cat, "question": item["en"], "question_ur": item["ur"]}
            for cat, items in RIASEC_QUESTIONS.items() for item in items
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
    riasec_answers: Dict[str, List[int]] = {cat: [] for cat in RIASEC_CATEGORIES}
    for cat, q_idx, value in payload["riasec"]:
        riasec_answers[cat].append(int(value))

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
        riasec_answers=riasec_answers,
        big_five_answers=big_five_answers,
        skills_ratings=skills_ratings,
        academic_ratings=academic_ratings,
    )


# ---------------------------------------------------------------------------
# 7. MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def run_discovery_assessment(student: StudentResponse) -> Dict:
    riasec_scores = score_riasec(student.riasec_answers)
    big_five_scores = score_big_five(student.big_five_answers)

    validity = check_response_validity(student.riasec_answers)

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
            f"RIASEC scores: {riasec_scores}\n"
            "No reliable field suggestion could be generated from this response set. "
            "Recommend a retake or a direct conversation to establish genuine interests."
        )
        return {
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

    student_report = generate_student_report(student.student_name, fields, riasec_scores)
    counsellor_report = generate_counsellor_report(student, riasec_scores, big_five_scores, flags, fields)

    return {
        "riasec_scores": riasec_scores,
        "big_five_scores": big_five_scores,
        "contradiction_flags": [f.__dict__ for f in flags],
        "suggested_fields": fields,
        "valid_response": True,
        "confidence": assess_confidence(riasec_scores),
        "student_report": student_report,
        "counsellor_report": counsellor_report,
    }


# ---------------------------------------------------------------------------
# 8. QUICK TEST (run this file directly to see a sample output)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample_student = StudentResponse(
        student_name="Ali Raza",
        riasec_answers={
            "R": [2, 1, 2, 1, 2, 2],
            "I": [5, 4, 5, 4, 5, 4],
            "A": [2, 2, 3, 2, 2, 2],
            "S": [3, 2, 3, 2, 3, 2],
            "E": [2, 2, 3, 2, 2, 2],
            "C": [4, 5, 4, 5, 4, 5],
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
