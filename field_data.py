"""
TCF Career Guidance — Stage 2 Field Data Module

Loads the researched field-profile dataset (field_profiles.json) and provides
lookup helpers used by the Flask routes.

IMPORTANT DATA ACCURACY NOTE:
This dataset was researched by an external AI tool with web search (not by
this Flask app or by Claude). General information (overviews, required
skills, career scope, FAQs) should be reasonably stable, but volatile facts —
merit formulas, fees, entry test details — change year to year and MUST be
verified against each university's official admission page before being
treated as final by a student or counsellor. Every field page displays this
disclaimer.

Developed by Qarib Javed
"""

import json
import os
import re

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "field_profiles.json")

with open(DATA_PATH, encoding="utf-8") as f:
    _RAW_PROFILES = json.load(f)

# Keyed by exact field_name string (must match the names used in discovery_engine.py's
# FIELD_MAPPING tables, so Stage 1 suggestions can link straight through).
FIELD_PROFILES = {item["field_name"]: item for item in _RAW_PROFILES}


def slugify(name: str) -> str:
    """Converts a field name into a URL-safe slug, e.g. 'Business/Management' -> 'business-management'."""
    slug = name.lower()
    slug = slug.replace("/", "-")           # slashes first, so words don't get merged together
    slug = re.sub(r"[^\w\s-]", "", slug)     # drop remaining punctuation like ( ) &
    slug = re.sub(r"[\s_]+", "-", slug)      # spaces/underscores -> hyphen
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


# Precompute slug -> exact field_name lookup
SLUG_TO_FIELD_NAME = {slugify(name): name for name in FIELD_PROFILES}


def get_profile_by_slug(slug: str):
    """Returns the full field profile dict for a slug, or None if not found/not yet researched."""
    field_name = SLUG_TO_FIELD_NAME.get(slug)
    if field_name is None:
        return None
    return FIELD_PROFILES.get(field_name)


def get_slug_for_field_name(field_name: str) -> str:
    """Given an exact field name (as suggested by Stage 1), returns its slug for linking."""
    return slugify(field_name)


def has_profile(field_name: str) -> bool:
    """Whether a Stage 2 detail page exists yet for this exact field name."""
    return field_name in FIELD_PROFILES


def all_available_field_names():
    """Returns every field name that currently has a researched Stage 2 profile."""
    return sorted(FIELD_PROFILES.keys())
