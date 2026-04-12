"""
populate_listening_migration.py
══════════════════════════════════════════════════════════════════════
Importe les ListeningAudio + ListeningQuestion en base Django.

Sources :
  - data/listening/ljspeech_subunit_assignments.json  → ListeningAudio
  - data/listening/listening_questions_complete.json  → ListeningQuestion

Mapping JSON → modèle Django :

  ljspeech_subunit_assignments.json         ListeningAudio
  ─────────────────────────────────────     ──────────────────────────
  audio_id                              →   audio_id  (PK)
  unit_number                           →   unit_number
  unit_title                            →   unit_title
  subunit_key                           →   subunit_key
  subunit_title                         →   subunit_title
  transcript                            →   transcript
  audio_path                            →   audio_path
  cefr                                  →   cefr_level
  match_score                           →   match_score
  confidence                            →   confidence
                                        →   sub_unit (FK) ← trouvé via unit_title + subunit_title

  listening_questions_complete.json         ListeningQuestion
  ─────────────────────────────────────     ──────────────────────────
  audio_id                              →   audio  (FK → ListeningAudio)
  order                                 →   question_order
  type                                  →   question_type
  question                              →   question_text
  choices                               →   choices
  answer                                →   correct_answer
  target_word                           →   target_word
  correct_order                         →   correct_order

Usage :
    cd backend/
    python scripts/listening/populate_listening_migration.py
    python scripts/listening/populate_listening_migration.py --dry-run
    python scripts/listening/populate_listening_migration.py --reset
══════════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import argparse
from pathlib import Path

# ── Setup Django ──────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Django_prj.settings")

import django
django.setup()

from django.db import transaction
from users.models import SubUnit, ListeningAudio, ListeningQuestion

# ── Chemins des fichiers JSON ─────────────────────────────────────
DATA_DIR        = BACKEND_DIR / "data" / "listening"
ASSIGNMENTS_PATH = DATA_DIR / "ljspeech_subunit_assignments.json"
QUESTIONS_PATH   = DATA_DIR / "listening_questions_corrected.json"


# ══════════════════════════════════════════════════════════════════
#  ÉTAPE 1 — Importer les ListeningAudio
# ══════════════════════════════════════════════════════════════════

def import_audios(assignments: list, dry_run: bool) -> dict:
    """
    Crée ou met à jour les ListeningAudio en base.
    Retourne un dict {audio_id → ListeningAudio} pour l'étape suivante.
    """
    print(f"\n{'─'*60}")
    print(f"  ÉTAPE 1 — Import ListeningAudio ({len(assignments)} entrées)")
    print(f"{'─'*60}")

    # Charger toutes les SubUnits A1 en une seule requête (évite N+1)
    subunits = SubUnit.objects.filter(
        unit__level="A1"
    ).select_related("unit")

    # Index : (unit_title, subunit_title) → SubUnit
    subunit_index = {
        (su.unit.title.strip(), su.title.strip()): su
        for su in subunits
    }

    print(f"  SubUnits A1 en base : {len(subunit_index)}")

    stats = {"created": 0, "updated": 0, "skipped": 0}
    audio_map = {}   # {audio_id → ListeningAudio} pour étape 2

    for entry in assignments:
        audio_id      = entry["audio_id"]
        unit_title    = entry["unit_title"].strip()
        subunit_title = entry["subunit_title"].strip()

        # Trouver la SubUnit
        sub_unit = subunit_index.get((unit_title, subunit_title))
        if not sub_unit:
            print(f"  ❌ SubUnit introuvable : '{unit_title}' / '{subunit_title}'")
            print(f"     → Vérifie que les unités sont bien en base (manage.py shell)")
            stats["skipped"] += 1
            continue

        icon = "✅" if entry["confidence"] == "high" else "⚠️ "
        print(f"  {icon} {audio_id} → {unit_title} / {subunit_title}")

        if dry_run:
            stats["created"] += 1
            continue

        # get_or_create pour idempotence (relance possible sans doublons)
        audio_obj, created = ListeningAudio.objects.update_or_create(
            audio_id=audio_id,
            defaults={
                "sub_unit":      sub_unit,
                "unit_number":   entry["unit_number"],
                "unit_title":    unit_title,
                "subunit_key":   entry["subunit_key"],
                "subunit_title": subunit_title,
                "transcript":    entry["transcript"],
                "audio_path":    entry.get("audio_path", ""),
                "cefr_level":    entry.get("cefr", "A1"),
                "match_score":   entry.get("match_score"),
                "confidence":    entry.get("confidence", "medium"),
            }
        )
        audio_map[audio_id] = audio_obj
        stats["created" if created else "updated"] += 1

    print(f"\n  Résultat :")
    print(f"    Créés   : {stats['created']}")
    print(f"    Mis à jour : {stats['updated']}")
    print(f"    Ignorés (SubUnit manquante) : {stats['skipped']}")

    return audio_map


# ══════════════════════════════════════════════════════════════════
#  ÉTAPE 2 — Importer les ListeningQuestion
# ══════════════════════════════════════════════════════════════════

def import_questions(questions: list, audio_map: dict, dry_run: bool):
    """
    Crée les ListeningQuestion en base.
    audio_map : {audio_id → ListeningAudio} construit à l'étape 1.
    """
    print(f"\n{'─'*60}")
    print(f"  ÉTAPE 2 — Import ListeningQuestion ({len(questions)} questions)")
    print(f"{'─'*60}")

    # Si audio_map est vide (dry_run ou aucun audio créé),
    # charger les audios déjà en base pour quand même valider
    if not audio_map:
        audio_map = {a.audio_id: a for a in ListeningAudio.objects.all()}
        print(f"  Audios chargés depuis la base : {len(audio_map)}")

    stats = {"created": 0, "skipped_audio": 0, "skipped_duplicate": 0}

    # Grouper par audio_id pour l'affichage
    from collections import defaultdict
    by_audio = defaultdict(list)
    for q in questions:
        by_audio[q["audio_id"]].append(q)

    for audio_id, audio_questions in by_audio.items():
        audio_obj = audio_map.get(audio_id)

        if not audio_obj and not dry_run:
            # Essayer de le trouver en base
            try:
                audio_obj = ListeningAudio.objects.get(audio_id=audio_id)
                audio_map[audio_id] = audio_obj
            except ListeningAudio.DoesNotExist:
                print(f"  ❌ Audio {audio_id} introuvable — {len(audio_questions)} questions ignorées")
                stats["skipped_audio"] += len(audio_questions)
                continue

        print(f"  🎵 {audio_id} → {len(audio_questions)} questions", end="")

        if dry_run:
            print(f"  [DRY RUN]")
            stats["created"] += len(audio_questions)
            continue

        created_count = 0
        for q in audio_questions:
            _, created = ListeningQuestion.objects.get_or_create(
                audio=audio_obj,
                question_order=q["order"],
                defaults={
                    "question_type":  q["type"],
                    "question_text":  q["question"],
                    "choices":        q.get("choices"),
                    "correct_answer": q["answer"],
                    "target_word":    q.get("target_word") or "",
                    "correct_order":  q.get("correct_order"),
                }
            )
            if created:
                created_count += 1
            else:
                stats["skipped_duplicate"] += 1

        stats["created"] += created_count
        print(f" → {created_count} créées")

    print(f"\n  Résultat :")
    print(f"    Créées    : {stats['created']}")
    print(f"    Doublons ignorés : {stats['skipped_duplicate']}")
    print(f"    Audio manquant   : {stats['skipped_audio']}")


# ══════════════════════════════════════════════════════════════════
#  RESET (optionnel)
# ══════════════════════════════════════════════════════════════════

def reset_tables():
    """Vide les tables ListeningQuestion et ListeningAudio (CASCADE)."""
    print("\n⚠️  RESET : suppression de toutes les données listening...")
    q_count = ListeningQuestion.objects.count()
    a_count = ListeningAudio.objects.count()
    ListeningQuestion.objects.all().delete()
    ListeningAudio.objects.all().delete()
    print(f"  Supprimé : {q_count} questions + {a_count} audios")


# ══════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Import ListeningAudio + ListeningQuestion en base Django"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simulation sans écriture en base"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Vider les tables avant import (ATTENTION : supprime tout)"
    )
    parser.add_argument(
        "--audio-only", action="store_true",
        help="Importer uniquement les ListeningAudio (sans questions)"
    )
    parser.add_argument(
        "--questions-only", action="store_true",
        help="Importer uniquement les ListeningQuestion (audios déjà en base)"
    )
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════════╗")
    print("║   Import Listening : Audio + Questions → Django DB   ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"\n  Assignments : {ASSIGNMENTS_PATH}")
    print(f"  Questions   : {QUESTIONS_PATH}")
    print(f"  Mode        : {'DRY RUN' if args.dry_run else 'PRODUCTION'}")

    # ── Vérifier les fichiers ─────────────────────────────────────
    for path in [ASSIGNMENTS_PATH, QUESTIONS_PATH]:
        if not path.exists():
            print(f"\n❌ Fichier introuvable : {path}")
            print(f"   Lance le script depuis backend/ ou ajuste DATA_DIR")
            sys.exit(1)
    print(f"\n✅ Fichiers JSON trouvés")

    # ── Charger les données ───────────────────────────────────────
    with open(ASSIGNMENTS_PATH, encoding="utf-8") as f:
        assignments = json.load(f)

    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        questions_data = json.load(f)
        # Supporte les deux formats : liste directe ou {metadata, questions}
        questions = (
            questions_data["questions"]
            if isinstance(questions_data, dict)
            else questions_data
        )

    print(f"  Audios      : {len(assignments)}")
    print(f"  Questions   : {len(questions)}")

    # ── Reset si demandé ──────────────────────────────────────────
    if args.reset and not args.dry_run:
        reset_tables()

    # ── Import dans une transaction atomique ──────────────────────
    try:
        with transaction.atomic():
            audio_map = {}

            if not args.questions_only:
                audio_map = import_audios(assignments, dry_run=args.dry_run)

            if not args.audio_only:
                import_questions(questions, audio_map, dry_run=args.dry_run)

            if args.dry_run:
                print("\n⚠️  DRY RUN : aucune écriture effectuée.")
                raise Exception("dry_run_rollback")

    except Exception as e:
        if "dry_run_rollback" not in str(e):
            print(f"\n❌ Erreur — transaction annulée : {e}")
            raise

    # ── Résumé final ──────────────────────────────────────────────
    if not args.dry_run:
        total_audios    = ListeningAudio.objects.count()
        total_questions = ListeningQuestion.objects.count()
        print(f"\n{'═'*60}")
        print(f"  ✅ TERMINÉ")
        print(f"  ListeningAudio    en base : {total_audios}")
        print(f"  ListeningQuestion en base : {total_questions}")
        print(f"{'═'*60}\n")


if __name__ == "__main__":
    main()