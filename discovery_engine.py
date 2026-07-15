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
        "Fixing something broken (a bike, a gadget, furniture) using tools.",
        "Working outdoors on a physical project (construction, farming, sports).",
        "Assembling or building something from parts (a model, a machine, a circuit).",
        "Operating or repairing equipment/machinery.",
        "Working with your hands rather than at a desk all day.",
        "Learning a physical/technical trade over a purely theoretical subject.",
    ],
    "I": [
        "Solving a difficult logic or math puzzle just for fun.",
        "Researching why something happens rather than just accepting it.",
        "Running an experiment to test an idea, even if it might fail.",
        "Reading about a scientific discovery in detail out of curiosity.",
        "Debugging a problem step-by-step until you find the root cause.",
        "Choosing a subject because it makes you think harder, not because it's easy.",
    ],
    "A": [
        "Coming up with an original idea rather than following a template.",
        "Designing something (visual, written, or musical) from scratch.",
        "Expressing an opinion through writing, art, or performance.",
        "Being given an open-ended task with no fixed 'right answer.'",
        "Noticing and caring about how something looks or sounds, not just how it works.",
        "Choosing originality over following an established method.",
    ],
    "S": [
        "Explaining a difficult topic to a friend who's stuck.",
        "Being the person others come to for advice.",
        "Working in a group project where you naturally take the 'people' role.",
        "Volunteering or helping in your community.",
        "Noticing when someone is upset even if they haven't said anything.",
        "Choosing a task that involves people over one that involves working alone.",
    ],
    "E": [
        "Convincing a group to go along with your plan or idea.",
        "Taking charge when a group project has no clear leader.",
        "Starting something of your own (a small project, page, business idea).",
        "Negotiating for something you want (a better grade, a deal, a decision).",
        "Taking a risk for a bigger potential reward.",
        "Choosing a competitive environment over a stable, predictable one.",
    ],
    "C": [
        "Organizing a messy set of files, notes, or a schedule.",
        "Following a clear step-by-step process rather than improvising.",
        "Double-checking details (numbers, spelling, data) before submitting work.",
        "Keeping track of a budget, schedule, or checklist without being told to.",
        "Working within clear rules and structure rather than ambiguity.",
        "Choosing accuracy and consistency over speed.",
    ],
}

BIG_FIVE_TRAITS = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "EmotionalStability"]

BIG_FIVE_QUESTIONS = {
    "Openness": [
        "I enjoy exploring new subjects even outside what I'm required to study.",
        "I get bored doing the same type of task repeatedly.",
        "I prefer questions with multiple possible answers over ones with a single fixed answer.",
    ],
    "Conscientiousness": [
        "I plan my work ahead of time rather than doing it last minute.",
        "I finish tasks I start, even when they get boring.",
        "I notice and fix small mistakes in my own work before submitting it.",
    ],
    "Extraversion": [
        "I feel energized after spending time with a group of people.",
        "I'd rather present in front of a class than write a report alone.",
        "I speak up quickly in group discussions rather than waiting to be asked.",
    ],
    "Agreeableness": [
        "I try to keep group harmony even if it means compromising my own view.",
        "I find it easy to see things from someone else's perspective.",
        "I prioritize others' needs over winning an argument.",
    ],
    "EmotionalStability": [
        "I stay calm under exam or deadline pressure.",
        "Setbacks don't affect my mood or motivation for long.",
        "I can make decisions without over-worrying about the outcome.",
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
    """Average each Big Five trait's 3 answers. Range 1-5."""
    scores = {}
    for trait in BIG_FIVE_TRAITS:
        vals = answers.get(trait, [])
        scores[trait] = round(sum(vals) / len(vals), 2) if vals else 0.0
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

def check_response_validity(riasec_scores: Dict[str, int]) -> Dict:
    """
    Detects 'straight-lining' — when a student answers every question the same way,
    which makes the RIASEC scores flat and any top-2 selection meaningless (just
    dictionary/tie order, not a genuine signal).

    Returns a dict with 'valid' (bool) and 'reason' (str, only if invalid).
    """
    values = list(riasec_scores.values())
    spread = max(values) - min(values)

    # If every category scored within a very narrow band, there's no real signal.
    # Max possible spread is 30-6=24. A spread below 6 means answers barely varied at all.
    if spread < 6:
        return {
            "valid": False,
            "reason": (
                "Your answers were very similar across all the questions, so the categories "
                "scored almost the same. This usually means either every scenario genuinely felt "
                "the same to you right now, or the questions were answered quickly without much "
                "thought. Either way, a confident field suggestion wouldn't be honest here."
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

    return flags


# ---------------------------------------------------------------------------
# 5. FIELD SUGGESTION
# ---------------------------------------------------------------------------

def suggest_fields(riasec_scores: Dict[str, int]) -> List[str]:
    top2 = top_riasec_categories(riasec_scores, 2)
    pair_key = frozenset(top2)

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

    report = f"Hi {name},\n\n"
    report += "Based on your answers, here are directions that seem to genuinely fit how you think and work:\n\n"
    for f in fields:
        report += f"  • {f}\n"
    report += f"\nWhy: your answers show a strong lean toward {reasons}.\n"
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
        "riasec": [
            {"category": cat, "question": q}
            for cat, qs in RIASEC_QUESTIONS.items() for q in qs
        ],
        "big_five": [
            {"trait": trait, "question": q}
            for trait, qs in BIG_FIVE_QUESTIONS.items() for q in qs
        ],
        "skills": SKILLS,
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

    return StudentResponse(
        student_name=payload.get("student_name", "Student"),
        riasec_answers=riasec_answers,
        big_five_answers=big_five_answers,
        skills_ratings=skills_ratings,
    )


# ---------------------------------------------------------------------------
# 7. MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def run_discovery_assessment(student: StudentResponse) -> Dict:
    riasec_scores = score_riasec(student.riasec_answers)
    big_five_scores = score_big_five(student.big_five_answers)

    validity = check_response_validity(riasec_scores)

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
            "student_report": student_report,
            "counsellor_report": counsellor_report,
        }

    flags = detect_contradictions(riasec_scores, big_five_scores, student.skills_ratings)
    fields = suggest_fields(riasec_scores)

    student_report = generate_student_report(student.student_name, fields, riasec_scores)
    counsellor_report = generate_counsellor_report(student, riasec_scores, big_five_scores, flags, fields)

    return {
        "riasec_scores": riasec_scores,
        "big_five_scores": big_five_scores,
        "contradiction_flags": [f.__dict__ for f in flags],
        "suggested_fields": fields,
        "valid_response": True,
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
            "Openness": [4, 4, 5],
            "Conscientiousness": [5, 4, 5],
            "Extraversion": [2, 2, 1],
            "Agreeableness": [3, 3, 3],
            "EmotionalStability": [3, 4, 3],
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
