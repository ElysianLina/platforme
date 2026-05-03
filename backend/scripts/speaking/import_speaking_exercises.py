"""
import_speaking_exercises_fixed.py
Script corrigé avec mapping explicite des SubUnit IDs
"""

import os
import re
import sys
import json
import django
from pathlib import Path

# Bootstrap Django
script_path = Path(__file__).resolve()
current = script_path.parent

while current.name != "backend" and current.parent != current:
    current = current.parent

if current.name != "backend":
    current = script_path.parent.parent

BACKEND_DIR = current
print(f"BACKEND_DIR: {BACKEND_DIR}")

backend_str = str(BACKEND_DIR)
if backend_str not in sys.path:
    sys.path.insert(0, backend_str)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Django_prj.settings")
django.setup()
print("Django OK")

from users.models import SubUnit, SpeakingExercise

# MAPPING EXPLICITE: (unit_number, sub_unit_key) -> subunit_id
SUBUNIT_MAPPING = {
    ("01", "A1.1"): 1,
    ("01", "A1.2"): 6,
    ("01", "A1.3"): 7,
    ("02", "A1.1"): 9,
    ("02", "A1.2"): 10,
    ("02", "A1.3"): 12,
    ("03", "A1.1"): 24,
    ("03", "A1.2"): 25,
    ("03", "A1.3"): 26,
    ("03", "A1.4"): 27,
    ("03", "A1.5"): 28,
    ("04", "A1.1"): 29,
    ("04", "A1.2"): 30,
    ("04", "A1.3"): 31,
    ("04", "A1.4"): 33,
    ("05", "A1.1"): 35,
    ("05", "A1.2"): 36,
    ("05", "A1.3"): 39,
    ("05", "A1.4"): 40,
    ("05", "A1.5"): 41,
    ("05", "A1.6"): 42,
    ("06", "A1.1"): 43,
    ("06", "A1.2"): 44,
    ("06", "A1.3"): 45,
    ("06", "A1.4"): 46,
    ("06", "A1.5"): 47,
    ("06", "A1.6"): 48,
    ("07", "A1.1"): 49,
    ("07", "A1.2"): 50,
    ("07", "A1.3"): 51,
    ("07", "A1.4"): 52,
    ("08", "A1.1"): 53,
    ("08", "A1.2"): 55,
    ("08", "A1.3"): 56,
    ("08", "A1.4"): 57,
    ("08", "A1.5"): 58,
    ("08", "A1.6"): 59,
    ("08", "A1.7"): 61,
    ("09", "A1.1"): 62,
    ("09", "A1.2"): 63,
    ("09", "A1.3"): 69,
    ("10", "A1.1"): 71,
    ("10", "A1.2"): 72,
    ("10", "A1.3"): 73,
    ("10", "A1.4"): 74,
    ("10", "A1.5"): 75,
    ("10", "A1.6"): 76,
    ("10", "A1.7"): 77,
    ("10", "A1.8"): 78,
    ("11", "A1"): 79,
    ("12", "A1.1"): 84,
    ("12", "A1.2"): 85,
    ("12", "A1.3"): 86,
    ("13", "A1.1"): 87,
    ("13", "A1.2"): 88,
    ("13", "A1.3"): 89,
    ("13", "A1.4"): 90,
    ("13", "A1.5"): 118,
    ("14", "A1"): 97,
    ("15", "A1.1"): 98,
    ("15", "A1.2"): 99,
    ("15", "A1.3"): 100,
    ("15", "A1.4"): 101,
    ("15", "A1.5"): 119,
    ("15", "A1.6"): 120,
    ("16", "A1.1"): 104,
    ("16", "A1.2"): 105,
    ("16", "A1.3"): 106,
    ("16", "A1.4"): 107,
    ("17", "A1"): 108,
}

JSON_FILE = BACKEND_DIR / "data" / "speaking" / "speaking_exercises_a1.json"
AUDIO_DIR = BACKEND_DIR / "data" / "speaking" / "audio_generated"
AUDIO_BASE_PATH = "data/speaking/audio_generated"


def build_audio_lookup(audio_dir):
    lookup = {}
    pattern = re.compile(r"^Unit(\d+)_(A\d+(?:\.\d+)?)_", re.IGNORECASE)
    for mp3 in sorted(audio_dir.glob("*.mp3")):
        m = pattern.match(mp3.name)
        if m:
            unit_num = m.group(1).zfill(2)
            sub_key = m.group(2)
            lookup[(unit_num, sub_key)] = mp3.name
    return lookup


def normalize_unit(unit_str):
    return unit_str.strip().zfill(2)


def get_subunit_by_id(subunit_id):
    try:
        return SubUnit.objects.get(id=subunit_id)
    except SubUnit.DoesNotExist:
        return None


def tokenize(sentence):
    return re.findall(r"\S+", sentence)


def run():
    print("\nImport SpeakingExercise A1 - VERSION CORRIGÉE")
    print("=" * 60)

    if not JSON_FILE.exists():
        print(f"ERROR: JSON not found: {JSON_FILE}")
        sys.exit(1)

    if not AUDIO_DIR.exists():
        print(f"ERROR: Audio dir not found: {AUDIO_DIR}")
        sys.exit(1)

    with open(JSON_FILE, encoding="utf-8") as f:
        exercises = json.load(f)

    print(f"JSON entries: {len(exercises)}")

    audio_lookup = build_audio_lookup(AUDIO_DIR)
    print(f"Audio files: {len(audio_lookup)}\n")

    created = updated = skip_audio = skip_subunit = errors = 0

    for entry in exercises:
        unit_number = normalize_unit(entry["unit"])
        sub_unit_key = entry["sub_unit"].strip()
        theme = entry["theme"].strip()
        level = entry.get("level", "A1").strip()
        sentence = entry["sentence"].strip()
        instructions = entry.get("instructions", "Read the following sentence aloud.")
        vocab_cats = entry.get("vocabulary_categories", [])

        label = f"Unit{unit_number}_{sub_unit_key}_{theme}"

        audio_key = (unit_number, sub_unit_key)
        if audio_key not in audio_lookup:
            print(f"SKIP (no audio): {label}")
            skip_audio += 1
            continue

        audio_filename = audio_lookup[audio_key]

        mapping_key = (unit_number, sub_unit_key)
        if mapping_key not in SUBUNIT_MAPPING:
            print(f"SKIP (no mapping): {label} - key {mapping_key} not found")
            skip_subunit += 1
            continue

        subunit_id = SUBUNIT_MAPPING[mapping_key]
        sub_unit = get_subunit_by_id(subunit_id)

        if sub_unit is None:
            print(f"SKIP (subunit not found): {label} - ID {subunit_id}")
            skip_subunit += 1
            continue

        if sub_unit.title != theme:
            print(f"WARNING: {label} -> SubUnit {sub_unit.title} (ID {subunit_id}) != theme {theme}")

        try:
            obj, was_created = SpeakingExercise.objects.update_or_create(
                sub_unit=sub_unit,
                defaults={
                    "theme": theme,
                    "level": level,
                    "instructions": instructions,
                    "sentence": sentence,
                    "sentence_words": tokenize(sentence),
                    "vocabulary_categories": vocab_cats,
                    "audio_filename": audio_filename,
                    "audio_path": f"{AUDIO_BASE_PATH}/{audio_filename}",
                    "unit_number": unit_number,
                },
            )

            if was_created:
                created += 1
                print(f"CREATED: {label} -> SubUnit ID {subunit_id}")
            else:
                updated += 1
                print(f"UPDATED: {label} -> SubUnit ID {subunit_id}")

        except Exception as exc:
            errors += 1
            print(f"ERROR: {label} - {exc}")

    print("\n" + "=" * 60)
    print(f"Created: {created}")
    print(f"Updated: {updated}")
    print(f"No audio: {skip_audio}")
    print(f"No subunit: {skip_subunit}")
    print(f"Errors: {errors}")


if __name__ == "__main__":
    run()