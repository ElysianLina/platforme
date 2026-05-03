"""
import_grammar_course.py
========================
Importe un fichier JSON de cours de grammaire dans la base PostgreSQL.

Placer ce script dans : PLATFORM/backend/
Lancer depuis PLATFORM/backend/ :
    python import_grammar_course.py

Pour réimporter après modification du JSON : relancer le même script,
update_or_create garantit qu'il n'y a pas de doublon.
"""

import os
import sys
import json
import django
# ── AJOUTE CECI ──────────────────────────────────────────────────────────────
# Remonte jusqu'au dossier backend/ (où se trouve Django_prj/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# BASE_DIR = C:\Users\HP\Desktop\platform\backend
sys.path.insert(0, BASE_DIR)
# ─────────────────────────────────────────────────────────────────────────────
# ── Setup Django ──────────────────────────────────────────────────────────────
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django_prj.settings')
django.setup()

from users.models import GrammarCourse, GrammarSection

# ── Mapping course_id → order (ordre dans le menu Grammar) ───────────────────
# À compléter au fur et à mesure que tu génères les autres leçons
COURSE_ORDER = {
    'grammar_a1_sentence_construction': 1,
    # 'grammar_a1_word_order'           : 2,
    # 'grammar_a1_possessive_adjectives': 3,
    # ...
}

# ── Mapping course_id → category ─────────────────────────────────────────────
COURSE_CATEGORY = {
    'grammar_a1_sentence_construction': 'phrases_noms_adjectifs',
    # 'grammar_a1_word_order'           : 'phrases_noms_adjectifs',
    # 'grammar_a1_numbers'              : 'chiffres_nombres',
    # ...
}


def import_course(json_path: str):
    """
    Importe ou met à jour un cours de grammaire depuis un fichier JSON.
    Utilise update_or_create → peut être relancé sans doublon.
    """
    print(f"\nLecture de : {json_path}")

    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    course_id = data.get('course_id')
    if not course_id:
        print("ERREUR : le JSON ne contient pas de champ 'course_id'.")
        sys.exit(1)

    # ── 1. Créer ou mettre à jour le cours ────────────────────────────────────
    course, created = GrammarCourse.objects.update_or_create(
        course_id=course_id,
        defaults={
            'title'   : data.get('title', ''),
            'subtitle': data.get('subtitle', ''),
            'level'   : data.get('level', 'A1'),
            'category': COURSE_CATEGORY.get(course_id, ''),
            'order'   : COURSE_ORDER.get(course_id, 99),
            'is_active': True,
        }
    )

    action = 'CRÉÉ' if created else 'MIS À JOUR'
    print(f"  Cours [{action}] : {course.title} (id={course.course_id})")

    # ── 2. Créer ou mettre à jour chaque section ──────────────────────────────
    sections = data.get('sections', [])
    if not sections:
        print("  ATTENTION : aucune section trouvée dans le JSON.")
        return

    for sec in sections:
        section_id = str(sec.get('section_id', ''))
        if not section_id:
            print("  ATTENTION : une section sans section_id ignorée.")
            continue

        sec_obj, sec_created = GrammarSection.objects.update_or_create(
            course=course,
            section_id=section_id,
            defaults={
                'section_type': sec.get('section_type', 'lesson'),
                'title'       : sec.get('section_title', ''),
                'order'       : int(section_id),   # section_id "1","2"… → ordre entier
                'content'     : sec.get('content', {}),
            }
        )

        sec_action = 'CRÉÉE' if sec_created else 'MAJ'
        print(f"    Section {section_id} [{sec_obj.section_type}] {sec_action} : {sec_obj.title}")

    print(f"\n  Total sections en base : {course.sections.count()}")
    print(f"  Import terminé pour : {course.title}\n")


# ── Point d'entrée ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Chemin vers le JSON — adapter si besoin
    # Par défaut : même dossier que ce script
    BASE = os.path.dirname(os.path.abspath(__file__))
    json_file = os.path.join(
        BASE,
        'grammar_a1_sentence_construction_enriched.json'
    )

    # Permet aussi de passer le chemin en argument :
    # python import_grammar_course.py chemin/vers/mon_cours.json
    if len(sys.argv) > 1:
        json_file = sys.argv[1]

    if not os.path.exists(json_file):
        print(f"ERREUR : fichier introuvable → {json_file}")
        sys.exit(1)

    import_course(json_file)
