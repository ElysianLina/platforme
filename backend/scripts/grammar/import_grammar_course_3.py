"""
import_grammar_course_3.py
==========================
Importe le cours 3 — Possessive Adjectives in English — dans la base PostgreSQL.

Placer ce script dans : PLATFORM/backend/
Placer le JSON dans   : PLATFORM/backend/grammar_a1_possessive_adjectives.json

Lancer depuis PLATFORM/backend/ :
    python import_grammar_course_3.py

Pour réimporter après modification du JSON : relancer le même script,
update_or_create garantit qu'il n'y a pas de doublon.
"""

import os
import sys
import json
import django

# ── Setup chemin Django ───────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# BASE_DIR = PLATFORM/backend/
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django_prj.settings')
django.setup()

from users.models import GrammarCourse, GrammarSection

# ── Mapping course_id → order dans le menu Grammar ───────────────────────────
COURSE_ORDER = {
    'grammar_a1_sentence_construction' : 1,
    'grammar_a1_word_order'            : 2,
    'grammar_a1_possessive_adjectives' : 3,   # ← cours 3
    # 'grammar_a1_demonstratives'       : 4,
    # 'grammar_a1_nouns'                : 5,
    # 'grammar_a1_plural'               : 6,
}

# ── Mapping course_id → category ─────────────────────────────────────────────
COURSE_CATEGORY = {
    'grammar_a1_sentence_construction' : 'phrases_noms_adjectifs',
    'grammar_a1_word_order'            : 'phrases_noms_adjectifs',
    'grammar_a1_possessive_adjectives' : 'phrases_noms_adjectifs',   # ← même catégorie
    # 'grammar_a1_numbers'              : 'chiffres_nombres',
}


def import_course(json_path: str):
    """
    Importe ou met à jour un cours de grammaire depuis un fichier JSON.
    Utilise update_or_create → peut être relancé sans doublon.
    """
    print(f"\nLecture de : {json_path}")

    if not os.path.exists(json_path):
        print(f"ERREUR : fichier introuvable → {json_path}")
        sys.exit(1)

    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    course_id = data.get('course_id')
    if not course_id:
        print("ERREUR : le JSON ne contient pas de champ 'course_id'.")
        sys.exit(1)

    print(f"  course_id : {course_id}")
    print(f"  title     : {data.get('title', '')}")
    print(f"  level     : {data.get('level', 'A1')}")
    print(f"  sections  : {len(data.get('sections', []))}")

    # ── 1. Créer ou mettre à jour le cours ────────────────────────────────────
    course, created = GrammarCourse.objects.update_or_create(
        course_id=course_id,
        defaults={
            'title'    : data.get('title', ''),
            'subtitle' : data.get('subtitle', ''),
            'level'    : data.get('level', 'A1'),
            'category' : COURSE_CATEGORY.get(course_id, 'phrases_noms_adjectifs'),
            'order'    : COURSE_ORDER.get(course_id, 99),
            'is_active': True,
        }
    )

    action = 'CRÉÉ' if created else 'MIS À JOUR'
    print(f"\n  Cours [{action}] : {course.title}")
    print(f"  order={course.order} | category={course.category} | level={course.level}")

    # ── 2. Créer ou mettre à jour chaque section ──────────────────────────────
    sections = data.get('sections', [])
    if not sections:
        print("  ATTENTION : aucune section trouvée dans le JSON.")
        return

    print(f"\n  Importation des sections :")
    for sec in sections:
        section_id = str(sec.get('section_id', ''))
        if not section_id:
            print("    ATTENTION : section sans section_id — ignorée.")
            continue

        sec_obj, sec_created = GrammarSection.objects.update_or_create(
            course=course,
            section_id=section_id,
            defaults={
                'section_type': sec.get('section_type', 'lesson'),
                'title'       : sec.get('section_title', ''),
                'order'       : int(section_id),
                'content'     : sec.get('content', {}),
            }
        )

        sec_action = 'CRÉÉE' if sec_created else 'MAJ'
        print(f"    [{sec_action}] Section {section_id} [{sec_obj.section_type}] : {sec_obj.title}")

    total = course.sections.count()
    print(f"\n  Sections en base : {total}")
    print(f"  Import terminé ✓ — '{course.title}'\n")

    # ── 3. Vérification rapide ────────────────────────────────────────────────
    print("  Vérification :")
    for sec in course.sections.all():
        exercises = sec.content.get('exercises', []) if sec.section_type == 'exercise' else []
        mistakes  = sec.content.get('mistakes', [])  if sec.section_type == 'tips'     else []
        extras = ''
        if exercises: extras = f' → {len(exercises)} exercices'
        if mistakes:  extras = f' → {len(mistakes)} mistakes'
        print(f"    ✓ Section {sec.section_id} [{sec.section_type}] : {sec.title}{extras}")


# ── Point d'entrée ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    json_file = os.path.join(BASE_DIR, 'scripts', 'grammar', 'grammar_a1_possessive_adjectives.json')

    # Accepte aussi un chemin passé en argument :
    # python import_grammar_course_3.py chemin/vers/mon_cours.json
    if len(sys.argv) > 1:
        json_file = sys.argv[1]

    import_course(json_file)
